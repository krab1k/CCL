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
import sympy
import tqdm
import datetime
from typing import List

import chargefw2_python

import ccl.ast
import ccl.symboltable
import ccl.types
import ccl.functions
import ccl.errors

import ccl.regression.deap_gp

default_options = {
    'use_math_functions': False,
    'population_size': 200,
    'crossover_probability': 0.8,
    'mutation_probability': 0.2,
    'generations': 15,
    'top_results': 5,
    'unique_population': True,
    'ncpus': None,
    'seed': None,
    'chargefw2_dir': '/opt/chargefw2',
    'eigen_include': '/usr/include/eigen3',
    'print_stats': True,
    'early_exit': False,
    'require_symmetry': False,
    'initial_seed': [],
    'initial_seed_mutations': 10,
    'metric': 'RMSD'
}


class AtomObject:
    pass


class BondObject:
    pass


def prepare_primitive_set(table: ccl.symboltable.SymbolTable, expr: ccl.ast.RegressionExpr, rng: random.Random,
                          options: dict) -> Tuple[gp.PrimitiveSetTyped, dict]:
    """Prepare set of primitives from which the individual is built"""
    input_types = []
    atom_names = []
    bond_names = []
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
                atom_names.append(s.name)
            else:
                input_types.append(BondObject)
                bond_names.append(s.name)
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

    primitive_set.addEphemeralConstant('rand', lambda: round(rng.random() * 2, 1), float)
    primitive_set.addTerminal('1.0', float, '1.0')
    primitive_set.addTerminal('2.0', float, '2.0')
    primitive_set.addPrimitive('add', [float, float], float, 'add')
    primitive_set.addPrimitive('sub', [float, float], float, 'sub')
    primitive_set.addPrimitive('mul', [float, float], float, 'mul')
    primitive_set.addPrimitive('div', [float, float], float, 'div')
    primitive_set.addPrimitive('sqrt', [float], float, 'sqrt')
    primitive_set.addPrimitive('cbrt', [float], float, 'cbrt')
    primitive_set.addPrimitive('square', [float], float, 'square')
    primitive_set.addPrimitive('cube', [float], float, 'cube')
    primitive_set.addPrimitive('exp', [float], float, 'exp')
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

    if options['require_symmetry']:
        if len(atom_names) not in (0, 2) or len(bond_names) not in (0, 2):
            raise RuntimeError('Symmetry requires two variables of the same name')

    ccl_objects = {'distance': distance_name,
                   'single_argument': atom_properties + bond_properties + atom_parameters + bond_parameters + atom_array_variables,
                   'atom_objects': atom_names, 'bond_objects': bond_names}

    return primitive_set, ccl_objects


def check_symmetry(sympy_expr: sympy.Expr, ccl_objects: dict) -> bool:
    substitutions = {}
    for ab_type in ['atom_objects', 'bond_objects']:
        if ccl_objects[ab_type]:
            x = ccl_objects[ab_type][0]
            y = ccl_objects[ab_type][1]
            substitutions[x] = y
            substitutions[y] = x

    sympy_expr_swapped = sympy.simplify(sympy_expr.subs(substitutions, simultaneous=True))
    return sympy_expr == sympy_expr_swapped


def generate_sympy_code(expr: gp.PrimitiveTree, ccl_objects: dict) -> sympy.Expr:
    """Generates unoptimized version of CCL code from an individual"""
    string = ''
    stack = []
    distance_name = ccl_objects.get('distance', None)
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
            elif prim.name in {'atom', 'bond'}:
                string = f'{args[0]}'
            elif prim.name in {'sqrt', 'cbrt', 'exp'}:
                string = f'{prim.name}({args[0]})'
            elif prim.name == 'square':
                string = f'({args[0]}) ** 2'
            elif prim.name == 'cube':
                string = f'({args[0]}) ** 3'
            elif prim.name == distance_name:
                if args[0] == args[1]:
                    string = '0'
                elif args[0] < args[1]:
                    string = f'{distance_name}({args[0]}{args[1]})'
                else:
                    string = f'{distance_name}({args[1]}{args[0]})'
            elif prim.name in ccl_objects['single_argument']:
                string = f'{prim.name}({args[0]})'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return sympy.simplify(sympy.sympify(string))


def generate_optimized_ccl_code(expr: gp.PrimitiveTree, ccl_objects: dict) -> str:
    """Generates somewhat optimized CCL code for an individual"""
    string = ''
    stack = []
    distance_name = ccl_objects.get('distance', None)
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
                if args[0] == args[1]:
                    string = '1.0'
                elif args[1] == '1.0':
                    string = args[0]
                else:
                    string = f'({args[0]}) / ({args[1]})'
            elif prim.name == 'sqrt':
                string = f'sqrt({args[0]})'
            elif prim.name == 'cbrt':
                string = f'({args[0]}) ^ (1.0 / 3.0)'
            elif prim.name == 'square':
                string = f'({args[0]}) ^ 2.0'
            elif prim.name == 'cube':
                string = f'({args[0]}) ^ 3.0'
            elif prim.name == 'exp':
                string = f'exp({args[0]})'
            elif prim.name in {'atom', 'bond'}:
                string = args[0]
            elif prim.name == distance_name:
                if args[0] == args[1]:
                    string = '0.0'
                elif args[0] < args[1]:
                    string = f'{distance_name}[{args[0]}, {args[1]}]'
                else:
                    string = f'{distance_name}[{args[1]}, {args[0]}]'
            elif prim.name in ccl_objects['single_argument']:
                string = f'{prim.name}[{args[0]}]'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return string


def individual_eq(first: gp.PrimitiveTree, second: gp.PrimitiveTree, ccl_objects: dict) -> bool:
    """Test whether the two individuals would have a same CCL code representation"""
    return generate_sympy_code(first, ccl_objects) == generate_sympy_code(second, ccl_objects)


def evaluate(individual: gp.PrimitiveTree, method_skeleton: 'CCLMethod', cache: dict, ccl_objects: dict, options: dict,
             message_queue: multiprocessing.Queue) -> Tuple[float, float]:
    """Evaluate individual by calculating RMSD or R2 between new and reference charges"""
    invalid_result = math.inf, -math.inf
    try:
        sympy_expr = generate_sympy_code(individual, ccl_objects)
    except OverflowError:
        message_queue.put(('Invalid', '<overflow>', invalid_result))
        return invalid_result

    sympy_expr_evaluated = str(sympy_expr.evalf(2))

    if sympy_expr.has(sympy.zoo):
        message_queue.put(('Invalid', sympy_expr_evaluated, invalid_result))
        return invalid_result

    if str(sympy_expr_evaluated) in cache:
        message_queue.put(('Cached', sympy_expr_evaluated, cache[sympy_expr_evaluated]))
        return cache[sympy_expr_evaluated]

    new_expr = generate_optimized_ccl_code(individual, ccl_objects)
    new_source = method_skeleton.source.format(f'({new_expr})')

    tmpdir = tempfile.mkdtemp(prefix='ccl_regression_')
    try:
        new_method = method_skeleton.__class__(new_source)
        new_method.translate('cpp', output_dir=tmpdir)
    except ccl.errors.CCLCodeError as e:
        line = new_source.split('\n')[e.line - 1]
        print(f'CCL Compilation Error: {e.line}:{e.column}: {line}: {e.message}', file=sys.stderr)
        return invalid_result
    except Exception as e:
        print(f'Unknown error during compilation: {e}', file=sys.stderr)
        print(new_source)
        return invalid_result

    chargefw2_dir = options['chargefw2_dir']

    args = ['g++', '-O1', '-s', '-fPIC', f'-isystem{options["eigen_include"]}', f'-I{chargefw2_dir}/include', '-shared',
            '-Wl,-soname,libREGRESSION.so', f'-L{chargefw2_dir}/lib', f'-Wl,-rpath,{chargefw2_dir}lib:',
            '-o', 'libREGRESSION.so', 'ccl_method.cpp', '-lchargefw2']

    p = subprocess.run(args, cwd=tmpdir, stderr=subprocess.PIPE)
    if p.stderr:
        print(f'Warning issued: {new_expr}', file=sys.stderr)
        print(p.stderr.decode('utf-8'))
        return invalid_result
    if p.returncode:
        print(f'Cannot compile: {new_expr}', file=sys.stderr)
        return invalid_result

    global data
    rmsd, r2 = chargefw2_python.evaluate(data, f'{tmpdir}/libREGRESSION.so')

    shutil.rmtree(tmpdir)

    if rmsd < 0 or r2 < 0:
        result = invalid_result
    else:
        result = rmsd, r2

    message_queue.put(('Evaluated', sympy_expr_evaluated, result))
    cache[str(sympy_expr_evaluated)] = result
    return result


def progress_bar(q: multiprocessing.Queue, options: dict) -> None:
    gen_bar = tqdm.tqdm(total=options['generations'] + 1, position=0, desc='Generations')
    p_bar = tqdm.tqdm(total=0, position=1, desc='Progress inside generation')
    best_bar = tqdm.tqdm(total=0, position=2, bar_format='{desc}')

    metric = options['metric']

    best_rmsd = math.inf
    best_r2 = -math.inf
    rmsd_selected, r2_selected = ('*', '') if metric == 'RMSD' else ('', '*')

    i = 1
    for message in iter(q.get, None):
        if message[0] == 'gen':
            gen_bar.set_description(f'Generation: {message[1]}')
            gen_bar.update()
            p_bar.reset(total=message[2])
        else:
            kind, expr, (rmsd, r2) = message
            p_bar.write(f'[{i:>6}] {kind:>9} ({r2_selected}R2 = {r2:6.4f} | {rmsd_selected}RMSD = {rmsd:8.4f}): {expr}')
            p_bar.update()
            i += 1
            if (metric == 'RMSD' and rmsd < best_rmsd) or (metric == 'R2' and r2 > best_r2):
                best_rmsd = rmsd
                best_r2 = r2
                best_individual = expr
                best_bar.set_description_str(f'Best so far: {r2_selected}R2 = {best_r2:6.4f} | '
                                             f'{rmsd_selected}RMSD = {best_rmsd:8.4f} : {best_individual}')

    gen_bar.close()
    p_bar.close()
    best_bar.close()


def generate_population(toolbox: base.Toolbox, ccl_objects: dict, options: dict) -> List[gp.PrimitiveTree]:
    """Generate initial population"""

    pop = []
    codes = set()
    pbar = tqdm.tqdm(total=options['population_size'])
    while len(pop) < options['population_size']:
        ind = toolbox.individual()
        try:
            sympy_code = generate_sympy_code(ind, ccl_objects).evalf(2)
            if sympy_code.has(sympy.zoo):
                continue
        except OverflowError:
            continue
        if options['require_symmetry']:
            if not check_symmetry(sympy_code, ccl_objects):
                continue
        if options['unique_population']:
            if sympy_code in codes:
                continue
            codes.add(sympy_code)

        pop.append(ind)
        pbar.update()

    pbar.close()
    return pop


def add_seeded_individuals(toolbox: base.Toolbox, options: dict, ccl_objects: dict, primitive_set: gp.PrimitiveSetTyped) -> List[gp.PrimitiveTree]:
    pop = []
    codes = set()
    for no, ind in enumerate(options['initial_seed']):
        x = creator.Individual(gp.PrimitiveTree.from_string(ind, primitive_set))
        try:
            sympy_code = generate_sympy_code(x, ccl_objects).evalf(2)
        except OverflowError:
            raise RuntimeError(f'Initial individual causes overflow: {ind}')
        print(f'[Seed {no:2d} No mutation]: {sympy_code}')
        pop.append(x)
        i = 0
        codes.add(sympy_code)
        while i < options['initial_seed_mutations']:
            y = toolbox.clone(x)
            toolbox.mutate(y)
            try:
                mut_sympy_code = generate_sympy_code(y, ccl_objects).evalf(2)
            except OverflowError:
                continue
            if mut_sympy_code.has(sympy.zoo):
                continue
            if mut_sympy_code in codes:
                continue

            if options['require_symmetry']:
                if not check_symmetry(mut_sympy_code, ccl_objects):
                    continue

            codes.add(mut_sympy_code)
            i += 1
            print(f'[Seed {no:2d} Mutation {i:2d}]: {mut_sympy_code}')
            pop.append(y)
    return pop


data = None


def init(dataset: str, ref_charges: str, parameters: str) -> None:
    global data
    data = chargefw2_python.Data(dataset, ref_charges, parameters)


def print_options(options: dict):
    print('*** Settings ***')
    max_size = max(len(opt) for opt in options)
    for opt, value in options.items():
        print(f'{opt:<{max_size + 1}}', value)


def evaluate_population(pop: List[gp.PrimitiveTree], toolbox: base.Toolbox, options: dict) -> None:
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = (fit[0], fit[1]) if options['metric'] == 'RMSD' else (fit[1], fit[0])


def run_symbolic_regression(initial_method: 'CCLMethod', dataset: str, ref_charges: str, parameters: str,
                            user_options: Optional[dict] = None):
    expr = initial_method.get_regression_expr()
    if expr is None:
        raise RuntimeError('No regression expression specified')

    start_time = datetime.datetime.now().replace(microsecond=0)

    options = {**default_options}
    if user_options is not None:
        options.update(**user_options)

    manager = multiprocessing.Manager()
    cache = manager.dict()
    q = manager.Queue()
    rng = random.Random(options['seed'])

    table = ccl.symboltable.SymbolTable.get_table_for_node(expr)

    # Setup GP toolbox
    pset, ccl_objects = prepare_primitive_set(table, expr, rng, options)

    if options['metric'] == 'RMSD':
        creator.create('FitnessMin', base.Fitness, weights=(-1.0, 1.0))
    else:
        creator.create('FitnessMin', base.Fitness, weights=(1.0, -1.0))

    creator.create('Individual', gp.PrimitiveTree, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register('expr', ccl.regression.deap_gp.gen_grow, pset=pset, min_=1, max_=6, rng=rng)
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)

    toolbox.register('evaluate', evaluate, method_skeleton=initial_method, cache=cache, ccl_objects=ccl_objects,
                     options=options, message_queue=q)
    toolbox.register('select', ccl.regression.deap_gp.sel_double_tournament, fitness_size=10, parsimony_size=1.4, rng=rng)
    toolbox.register('mate', ccl.regression.deap_gp.cx_one_point, rng=rng)
    toolbox.register('expr_mut', ccl.regression.deap_gp.gen_full, min_=0, max_=3, rng=rng)
    toolbox.register('mutate', ccl.regression.deap_gp.mut_uniform, expr=toolbox.expr_mut, pset=pset, rng=rng)
    toolbox.register('mutate_shrink', ccl.regression.deap_gp.mut_shrink, rng=rng)

    toolbox.decorate('mate', gp.staticLimit(operator.attrgetter('height'), 17))
    toolbox.decorate('mutate', gp.staticLimit(operator.attrgetter('height'), 17))

    if options['metric'] == 'RMSD':
        rmsd_idx, r2_idx = 0, 1
    else:
        rmsd_idx, r2_idx = 1, 0

    rmsd_stats = tools.Statistics(key=lambda x: x.fitness.values[rmsd_idx])
    r2_stats = tools.Statistics(key=lambda x: x.fitness.values[r2_idx])

    all_stats = tools.MultiStatistics(RMSD=rmsd_stats, R2=r2_stats)

    all_stats.register('min', lambda x: np.min(np.array(x)[np.isfinite(x)]))
    all_stats.register('med', lambda x: np.median(np.array(x)[np.isfinite(x)]))
    all_stats.register('max', lambda x: np.max(np.array(x)[np.isfinite(x)]))

    logbook = tools.Logbook()

    hof = tools.HallOfFame(options['top_results'], similar=functools.partial(individual_eq, ccl_objects=ccl_objects))

    # Run GP algorithm
    print('*** Generating initial population ***')

    pop = generate_population(toolbox, ccl_objects, options)

    if options['initial_seed']:
        print('*** Seeding initial population ***')
        pop.extend(add_seeded_individuals(toolbox, options, ccl_objects, pset))

    pool = multiprocessing.Pool(options['ncpus'], initializer=init, initargs=(dataset, ref_charges, parameters))
    toolbox.register('map', pool.map)

    progress_process = multiprocessing.Process(target=progress_bar, args=(q, options))

    q.put(('gen', 0, len(pop)))

    progress_process.start()
    evaluate_population(pop, toolbox, options)

    hof.update(pop)
    record = all_stats.compile(pop)
    logbook.record(gen=0, evals=len(pop), **record, best=generate_sympy_code(hof[0], ccl_objects).evalf(2))

    for gen in range(options['generations']):
        if options['early_exit']:
            if (options['metric'] == 'RMSD' and record['RMSD']['min'] < 1e-4) or \
                    options['metric'] == 'R2' and record['R2']['max'] > 1 - 1e-4:
                break

        offspring = toolbox.select(pop, len(pop))
        offspring = list(toolbox.map(toolbox.clone, offspring))
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if rng.random() < options['crossover_probability']:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if rng.random() < options['mutation_probability']:
                if rng.random() < 0.3:
                    toolbox.mutate_shrink(mutant)
                else:
                    toolbox.mutate(mutant)
                del mutant.fitness.values

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        q.put(('gen', gen + 1, len(invalid_ind)))

        evaluate_population(invalid_ind, toolbox, options)
        pop[:] = offspring

        hof.update(pop)
        record = all_stats.compile(pop)
        logbook.record(gen=gen + 1, evals=len(invalid_ind), **record, best=generate_sympy_code(hof[0], ccl_objects).evalf(2))

    q.put(None)
    progress_process.join()
    pool.close()

    end_time = datetime.datetime.now().replace(microsecond=0)

    print(f'\n{"=" * 30} RESULTS {"=" * 30}\n')
    print('\n*** Used files ***')
    print(f'Structures       : {dataset}')
    print(f'Reference charges: {ref_charges}')
    print(f'Parameters:      : {parameters}')

    print('\n*** Original skeleton ***')
    print(initial_method.source)
    print_options(options)

    best_count = min(len(hof), options['top_results'])
    print(f'\n*** Best individuals encountered ({best_count}) ***')

    rmsd_selected, r2_selected = ('*', '') if options['metric'] == 'RMSD' else ('', '*')
    for i in range(best_count):
        print(f'{r2_selected}R2 = {hof[i].fitness.values[r2_idx]: 6.4f}: | '
              f'{rmsd_selected}RMSD = {hof[i].fitness.values[rmsd_idx]: 8.4f}: ',
              generate_sympy_code(hof[i], ccl_objects).evalf(2))

    if options['print_stats']:
        logbook.header = 'gen', 'evals', 'RMSD', 'R2', 'best'
        logbook.chapters['RMSD'].header = 'min', 'med', 'max'
        logbook.chapters['R2'].header = 'min', 'med', 'max'
        print('\n*** Statistics over generations ***')
        print(logbook)

    time_format = '%d %B %Y: %H:%M:%S'
    print('\n*** Time stats ***')
    print(f'Started: {start_time.strftime(time_format)}')
    print(f'Ended:   {end_time.strftime(time_format)}')
    print(f'Elapsed: {end_time - start_time}')
