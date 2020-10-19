"""Symbolic regression of CCL code """

import sys
import random
from deap import gp, creator, base, tools
from typing import Tuple
import tempfile
import math
import subprocess
import shutil
import operator
import multiprocessing
import numpy as np
from typing import Optional
import decimal
import functools

import chargefw2_python

import ccl.ast
import ccl.symboltable
import ccl.types
import ccl.functions
import ccl.errors

default_options = {
    'use_math_functions': False,
    'population_size': 200,
    'crossover_probability': 0.8,
    'mutation_probability': 0.2,
    'generations': 15,
    'top_results': 5,
    'unique_population': True,
    'parallelization': True,
    'ncpus': None,
    'seed': None,
    'chargefw2_dir': '/opt/chargefw2',
    'eigen_include': '/usr/include/eigen3',
    'print_stats': True,
    'early_exit': False
}


class AtomObject:
    pass


class BondObject:
    pass


def prepare_primitive_set(table: ccl.symboltable.SymbolTable, expr: ccl.ast.RegressionExpr, options: dict) -> Tuple[gp.PrimitiveSetTyped, dict]:
    """Prepare set of primitives from which the individual is built"""
    input_types = []
    object_names = []

    atom_properties = []
    bond_properties = []

    atom_parameters = []
    bond_parameters = []
    common_parameters = []

    simple_variables = []
    atom_array_variables = []

    distance_name = None

    for s in table.get_symbols(recursive=True):
        if isinstance(s, ccl.symboltable.ObjectSymbol):
            if s.constraints is not None:
                continue
            if s.type == ccl.types.ObjectType.ATOM:
                input_types.append(AtomObject)
            else:
                input_types.append(BondObject)
            object_names.append(s.name)
        elif isinstance(s, ccl.symboltable.FunctionSymbol):
            if s.function.name in ccl.functions.ELEMENT_PROPERTIES:
                atom_properties.append(s.name)
            elif s.function.name == 'bond order':
                bond_properties.append(s.name)
            elif s.function.name == 'distance':
                distance_name = s.name
        elif isinstance(s, ccl.symboltable.ParameterSymbol):
            if s.type == ccl.types.ParameterType.ATOM:
                atom_parameters.append(s.name)
            elif s.type == ccl.types.ParameterType.BOND:
                bond_parameters.append(s.name)
            else:
                common_parameters.append(s.name)
        elif isinstance(s, ccl.symboltable.VariableSymbol):
            # Check whether the name was defined on the same line or later and thus cannot be used
            if s.def_node is not None and s.def_node.line >= expr.line:
                continue
            if isinstance(s.type, ccl.types.NumericType):
                simple_variables.append(s.name)
            elif isinstance(s.type, ccl.types.ArrayType):
                if s.type == ccl.types.ArrayType(ccl.types.ObjectType.ATOM, ):
                    atom_array_variables.append(s.name)

    primitive_set = gp.PrimitiveSetTyped('MAIN', input_types, float)

    primitive_set.addEphemeralConstant('rand', lambda: round(random.random() * 5, 1), float)
    primitive_set.addPrimitive('add', [float, float], float, 'add')
    primitive_set.addPrimitive('sub', [float, float], float, 'sub')
    primitive_set.addPrimitive('mul', [float, float], float, 'mul')
    primitive_set.addPrimitive('div', [float, float], float, 'div')
    primitive_set.addPrimitive('atom', [AtomObject], AtomObject, 'atom')
    primitive_set.addPrimitive('bond', [BondObject], BondObject, 'bond')

    for ap in atom_parameters:
        primitive_set.addPrimitive(ap, [AtomObject], float, ap)

    for bp in bond_parameters:
        primitive_set.addPrimitive(bp, [BondObject], float, bp)

    for cp in common_parameters:
        primitive_set.addTerminal(cp, float, cp)

    for v in simple_variables:
        primitive_set.addTerminal(v, float, v)

    for array_atom in atom_array_variables:
        primitive_set.addPrimitive(array_atom, [AtomObject], float, array_atom)

    if options['use_math_functions']:
        for math_fn in ccl.functions.MATH_FUNCTIONS:
            primitive_set.addPrimitive(math_fn, [float], float, math_fn)

    for f in atom_properties:
        primitive_set.addPrimitive(f, [AtomObject], float, f)

    for f in bond_properties:
        primitive_set.addPrimitive(f, [BondObject], float, f)

    if distance_name is not None:
        primitive_set.addPrimitive(distance_name, [AtomObject, AtomObject], float, distance_name)

    primitive_set.renameArguments(**{f'ARG{i}': name for i, name in enumerate(object_names)})

    functions = {'distance': distance_name,
                 'single_argument': atom_properties + bond_properties + atom_parameters + bond_parameters + atom_array_variables}

    return primitive_set, functions


def generate_ccl_code(expr, functions):
    """Generates unoptimized version of CCL code from an individual"""
    string = ''
    stack = []
    distance_name = functions.get('distance', None)
    for node in expr:
        stack.append((node, []))
        while len(stack[-1][1]) == stack[-1][0].arity:
            prim, args = stack.pop()
            if prim.name == 'add':
                string = f'({args[0]}) + ({args[1]})'
            elif prim.name == 'sub':
                string = f'({args[0]}) - ({args[1]})'
            elif prim.name == 'mul':
                string = f'({args[0]}) * ({args[1]})'
            elif prim.name == 'div':
                string = f'({args[0]}) / ({args[1]})'
            elif prim.name == 'atom':
                string = f'{args[0]}'
            elif prim.name == distance_name:
                string = f'{distance_name}[{args[0]}, {args[1]}]'
            elif prim.name in functions['single_argument']:
                string = f'{prim.name}[{args[0]}]'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return string


def generate_optimized_ccl_code(expr, functions) -> Optional[str]:
    """Generates somewhat optimized CCL code for an individual"""
    string = ''
    stack = []
    distance_name = functions.get('distance', None)
    for node in expr:
        stack.append((node, []))
        while len(stack[-1][1]) == stack[-1][0].arity:
            prim, args = stack.pop()
            if prim.name == 'add':
                try:
                    string = str(decimal.Decimal(args[0]) + decimal.Decimal(args[1]))
                except decimal.InvalidOperation:
                    if args[0] < args[1]:
                        string = f'{args[0]} + {args[1]}'
                    else:
                        string = f'{args[1]} + {args[0]}'
            elif prim.name == 'sub':
                if args[1] == '0.0':
                    string = args[0]
                else:
                    try:
                        string = str(decimal.Decimal(args[0]) - decimal.Decimal(args[1]))
                    except decimal.InvalidOperation:
                        string = f'{args[0]} - {args[1]}'
            elif prim.name == 'mul':
                if args[0] == '0.0' or args[1] == '0.0':
                    string = '0.0'
                elif args[0] == '1.0':
                    string = args[1]
                elif args[1] == '1.0':
                    string = args[0]
                elif args[0] < args[1]:
                    string = f'({args[0]}) * ({args[1]})'
                else:
                    string = f'({args[1]}) * ({args[0]})'
            elif prim.name == 'div':
                if args[1] == '0.0':
                    return None
                if args[0] == args[1]:
                    string = '1.0'
                elif args[1] == '1.0':
                    string = args[0]
                else:
                    string = f'({args[0]}) / ({args[1]})'
            elif prim.name == 'atom':
                string = args[0]
            elif prim.name == distance_name:
                if args[0] == args[1]:
                    string = '0.0'
                elif args[0] < args[1]:
                    string = f'{distance_name}[{args[0]}, {args[1]}]'
                else:
                    string = f'{distance_name}[{args[1]}, {args[0]}]'
            elif prim.name in functions['single_argument']:
                string = f'{prim.name}[{args[0]}]'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return string


def individual_eq(first, second, functions):
    """Test whether the two individuals would have a same CCL code representation"""
    return generate_optimized_ccl_code(first, functions) == generate_optimized_ccl_code(second, functions)


def evaluate(individual, method_skeleton: 'CCLMethod', cache: dict, functions, options: dict) -> Tuple[float]:
    """Evaluate individual by calculating RMSD between new and reference charges"""
    new_expr = generate_optimized_ccl_code(individual, functions)

    if new_expr is None:
        return math.inf,

    if new_expr in cache:
        print(f'Cached (RMSD = {cache[new_expr]:.4f}): {new_expr}')
        return cache[new_expr],

    new_source = method_skeleton.source.format(f'({new_expr})')

    tmpdir = tempfile.mkdtemp(prefix='ccl_regression_')
    try:
        new_method = method_skeleton.__class__(new_source)
        new_method.translate('cpp', output_dir=tmpdir)
    except ccl.errors.CCLCodeError as e:
        line = new_source.split('\n')[e.line - 1]
        print(f'CCL Compilation Error: {e.line}:{e.column}: {line}: {e.message}', file=sys.stderr)
        return math.inf,
    except Exception as e:
        print(f'Unknown error during compilation: {e}', file=sys.stderr)
        print(new_source)
        return math.inf,

    chargefw2_dir = options['chargefw2_dir']

    args = ['g++', '-O1', '-c', '-fPIC', f'-isystem{options["eigen_include"]}', 'ccl_method.cpp',
            f'-I{chargefw2_dir}/include']

    p = subprocess.run(args, cwd=tmpdir)
    if p.returncode:
        print('Cannot compile', file=sys.stderr)
        return math.inf,

    args = ['g++', '-fPIC', '-shared', '-Wl,-soname,libREGRESSION.so', '-o', 'libREGRESSION.so',
            'ccl_method.o', f'-L{chargefw2_dir}/lib', f'-Wl,-rpath,{chargefw2_dir}lib:', '-lchargefw2']

    p = subprocess.run(args, cwd=tmpdir)
    if p.returncode:
        print('Cannot link', file=sys.stderr)
        return math.inf,

    global data
    rmsd = chargefw2_python.evaluate(data, f'{tmpdir}/libREGRESSION.so')

    shutil.rmtree(tmpdir)

    res = rmsd if rmsd >= 0 else math.inf
    print(f'Evaluated (RMSD = {res:.4f}): {new_expr}')
    cache[new_expr] = res
    return res,


def generate_population(toolbox, functions, options):
    """Generate initial population"""
    pop = toolbox.population(n=options['population_size'])

    if options['unique_population']:
        codes = set()
        unique_pop = []

        for ind in pop:
            code = generate_ccl_code(ind, functions)
            if code not in codes:
                codes.add(code)
                unique_pop.append(ind)

        diff = options['population_size'] - len(unique_pop)
        while diff != 0:
            new_pop = toolbox.population(n=diff)
            for ind in new_pop:
                code = generate_ccl_code(ind, functions)
                if code not in codes:
                    codes.add(code)
                    unique_pop.append(ind)

            diff = options['population_size'] - len(unique_pop)

        pop[:] = unique_pop

    return pop


data = None


def init(dataset, ref_charges, parameters):
    global data
    data = chargefw2_python.Data(dataset, ref_charges, parameters)


def run_symbolic_regression(initial_method: 'CCLMethod', dataset: str, ref_charges: str, parameters: str,
                            user_options: Optional[dict] = None):
    expr = initial_method.get_regression_expr()
    if expr is None:
        raise RuntimeError('No regression expression specified')

    options = {**default_options}
    if user_options is not None:
        options.update(**user_options)

    manager = multiprocessing.Manager()
    cache = manager.dict()

    random.seed(options['seed'])

    # if method_template.has_parameters():
    #    raise RuntimeError('Cannot use parameter right now')

    table = ccl.symboltable.SymbolTable.get_table_for_node(expr)

    # Setup GP toolbox
    pset, functions = prepare_primitive_set(table, expr, options)

    creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
    creator.create('Individual', gp.PrimitiveTree, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register('expr', gp.genGrow, pset=pset, min_=1, max_=6)
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)

    toolbox.register('evaluate', evaluate, method_skeleton=initial_method, cache=cache, functions=functions,
                     options=options)
    toolbox.register('select', tools.selDoubleTournament, fitness_size=10, fitness_first=True, parsimony_size=1.4)
    toolbox.register('mate', gp.cxOnePoint)
    toolbox.register('expr_mut', gp.genFull, min_=0, max_=3)
    toolbox.register('mutate', gp.mutUniform, expr=toolbox.expr_mut, pset=pset)
    toolbox.register('mutate_shrink', gp.mutShrink)

    toolbox.decorate('mate', gp.staticLimit(operator.attrgetter('height'), 17))
    toolbox.decorate('mutate', gp.staticLimit(operator.attrgetter('height'), 17))

    stats = tools.Statistics(key=lambda x: x.fitness.values)
    stats.register('med', lambda x: np.median(np.array(x)[np.isfinite(x)]))
    stats.register('min', lambda x: np.min(np.array(x)[np.isfinite(x)]))
    stats.register('max', lambda x: np.max(np.array(x)[np.isfinite(x)]))

    logbook = tools.Logbook()

    hof = tools.HallOfFame(options['top_results'], similar=functools.partial(individual_eq, functions=functions))

    # Run GP algorithm
    print('*** Evaluating initial population ***')

    pop = generate_population(toolbox, functions, options)

    if options['parallelization']:
        pool = multiprocessing.Pool(options['ncpus'], initializer=init, initargs=(dataset, ref_charges, parameters))
        toolbox.register('map', pool.map)

    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    hof.update(pop)
    record = stats.compile(pop)
    logbook.record(gen=0, **record)

    for gen in range(options['generations']):
        print(f'*** Evaluating generation: {gen + 1} ***')
        offspring = toolbox.select(pop, len(pop))
        offspring = list(toolbox.map(toolbox.clone, offspring))
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < options['crossover_probability']:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < options['mutation_probability']:
                if random.random() < 0.3:
                    toolbox.mutate_shrink(mutant)
                else:
                    toolbox.mutate(mutant)
                del mutant.fitness.values

        print('=> Evaluating offspring and mutations')
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = offspring

        hof.update(pop)
        record = stats.compile(pop)
        logbook.record(gen=gen + 1, **record)

        if options['early_exit']:
            if record['min'] == 0.0:
                break

    best_count = min(len(hof), options['top_results'])
    print(f'*** Best individuals encountered ({best_count}) ***')
    for i in range(best_count):
        print(f'RMSD = {hof[i].fitness.values[0]: .4f}: ', generate_optimized_ccl_code(hof[i], functions))

    if options['print_stats']:
        logbook.header = 'gen', 'min', 'med', 'max'
        print('*** Statistics over generations ***')
        print(logbook)
