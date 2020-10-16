"""Symbolic regression of CCL code """

import sys
import random
from deap import gp, creator, base, tools
from typing import Tuple
import tempfile
import math
import subprocess
import shutil
import multiprocessing
from typing import Optional

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
    'generations': 10,
    'top_results': 5,
    'parallelization': True,
    'ncpus': None,
    'seed': None,
    'chargefw2_dir': '/opt/chargefw2'
}


class AtomObject:
    pass


class BondObject:
    pass


manager = multiprocessing.Manager()
cache = manager.dict()


def prepare_primitive_set(table: ccl.symboltable.SymbolTable, options: dict) -> Tuple[gp.PrimitiveSetTyped, dict]:
    input_types = []
    object_names = []

    atom_properties = []
    bond_properties = []

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

    primitive_set = gp.PrimitiveSetTyped('MAIN', input_types, float)

    primitive_set.addEphemeralConstant('rand', lambda: round(random.random() * 5, 1), float)
    primitive_set.addPrimitive('add', [float, float], float, 'add')
    primitive_set.addPrimitive('sub', [float, float], float, 'sub')
    primitive_set.addPrimitive('mul', [float, float], float, 'mul')
    primitive_set.addPrimitive('div', [float, float], float, 'div')
    primitive_set.addPrimitive('atom', [AtomObject], AtomObject, 'atom')

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

    functions = {'distance': distance_name, 'atom': atom_properties, 'bond': bond_properties}

    return primitive_set, functions


def generate_ccl_code(expr, functions):
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
                string = f'({args[0]}) + ({args[1]})'
            elif prim.name == 'mul':
                string = f'({args[0]}) * ({args[1]})'
            elif prim.name == 'div':
                string = f'({args[0]}) / ({args[1]})'
            elif prim.name == 'atom':
                string = f'{args[0]}'
            elif prim.name == distance_name:
                string = f'{distance_name}[{args[0]}, {args[1]}]'
            elif prim.name in functions['atom'] or prim.name in functions['bond']:
                string = f'{prim.name}[{args[0]}]'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return string


def evaluate(individual, method_skeleton: 'CCLMethod', functions, data: dict, options: dict) -> Tuple[float]:
    new_expr = generate_ccl_code(individual, functions)

    if new_expr in cache:
        return (cache[new_expr],)

    new_source = method_skeleton.source.format(f'({new_expr})')

    new_method = method_skeleton.__class__(new_source)

    tmpdir = tempfile.mkdtemp(prefix='ccl_regression_')
    try:
        new_method.translate('cpp', output_dir=tmpdir)
    except ccl.errors.CCLCodeError as e:
        line = new_source.split('\n')[e.line - 1]
        print(f'CCL Compilation Error: {e.line}:{e.column}: {line}: {e.message}')
        return (math.inf,)
    except Exception as e:
        print(f'Unknown error during compilation: {e}')
        print(new_source)
        return (math.inf,)

    chargefw2_dir = options['chargefw2_dir']

    args = ['g++', '-O1', '-c', '-fPIC', '-isystem/usr/include/eigen3', 'ccl_method.cpp', f'-I{chargefw2_dir}/include']

    p = subprocess.run(args, cwd=tmpdir)
    if p.returncode:
        print('Cannot compile', file=sys.stderr)
        return (math.inf,)

    args = ['g++', '-fPIC', '-shared', '-Wl,-soname,libREGRESSION.so', '-o', 'libREGRESSION.so',
            'ccl_method.o', f'-L{chargefw2_dir}/lib', f'-Wl,-rpath,{chargefw2_dir}lib:', '-lchargefw2']

    p = subprocess.run(args, cwd=tmpdir)
    if p.returncode:
        print('Cannot link', file=sys.stderr)
        return (math.inf,)

    args = [f'{chargefw2_dir}/bin/chargefw2', '--mode', 'evaluation', '--method', f'{tmpdir}/libREGRESSION.so',
            '--ref-chg-file', data['ref-charges'], '--input-file', data['set'],
            '--chg-out-dir', tmpdir]

    if data['parameters'] is not None:
        args.extend(['--par-file', data['parameters']])

    p = subprocess.run(args, cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    shutil.rmtree(tmpdir)
    if p.returncode:
        print(f'Evaluated (RMSD = inf): {new_expr}')
        cache[new_expr] = math.inf
        return (math.inf,)
    else:
        rmsd = float(p.stdout.decode('utf-8'))
        cache[new_expr] = rmsd
        print(f'Evaluated (RMSD = {rmsd:.3f}): {new_expr}')
        return (rmsd,)


def generate(initial_method: 'CCLMethod', dataset: str, ref_charges: str, parameters: str,
             user_options: Optional[dict] = None):
    expr = initial_method.get_regression_expr()
    if expr is None:
        raise RuntimeError('No regression expression specified')

    options = {**default_options}
    if user_options is not None:
        options.update(**user_options)

    random.seed(options['seed'])

    # if method_template.has_parameters():
    #    raise RuntimeError('Cannot use parameter right now')

    table = ccl.symboltable.SymbolTable.get_table_for_node(expr)

    # Setup GP toolbox
    pset, functions = prepare_primitive_set(table, options)

    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("expr", gp.genGrow, pset=pset, min_=1, max_=5)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register('evaluate', evaluate, method_skeleton=initial_method, functions=functions,
                     data={'set': dataset, 'ref-charges': ref_charges, 'parameters': parameters}, options=options)
    toolbox.register("select", tools.selTournament, tournsize=5)
    toolbox.register("mate", gp.cxOnePoint)
    toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
    toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

    # Run GP algorithm
    print('*** Evaluating initial population ***')
    pop = toolbox.population(n=options['population_size'])

    if options['parallelization']:
        pool = multiprocessing.Pool(options['ncpus'])
        toolbox.register('map', pool.map)

    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

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
                toolbox.mutate(mutant)
                del mutant.fitness.values

        print('=> Evaluating offspring and mutations')
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = offspring

    results = {}
    for individual in pop:
        results[generate_ccl_code(individual, functions)] = individual

    best = sorted(results.values(), key=lambda x: x.fitness.values[0])

    best_no = min(options["top_results"], len(best))
    print(f'TOP {best_no}: ')
    for i in range(best_no):
        print(f'RMSD = {best[i].fitness.values[0]: .3f}: ', generate_ccl_code(best[i], functions))
