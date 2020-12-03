"""Symbolic regression of CCL code """

import sys
import random
from deap import gp, creator, base, tools, algorithms
import math
import operator
import concurrent.futures
import multiprocessing
import numpy as np
from typing import Optional
import tqdm
import datetime
import logging

import ccl.ast
import ccl.symboltable
import ccl.types
import ccl.functions
import ccl.errors

import ccl.regression.deap_gp
from ccl.regression.evaluate import evaluate, init, evaluate_population, generate_sympy_codes
from ccl.regression.init_gp import prepare_primitive_set
from ccl.regression.options import default_options, print_options
from ccl.regression.population import generate_population, add_seeded_individuals
from ccl.regression.constraints import check_unique_symbols


def progress_bar(q: multiprocessing.Queue, options: dict) -> None:
    """Process the messages sent from worker processes and display the progress bar"""
    gen_bar = tqdm.tqdm(total=options['generations'] + 1, position=0, desc='Generations')
    p_bar = tqdm.tqdm(total=0, position=1, desc='Progress inside generation')
    best_bar = tqdm.tqdm(total=0, position=2, bar_format='{desc}')

    best_obj = math.inf

    i = 1
    for message in iter(q.get, None):
        if message[0] == 'gen':
            gen_bar.set_description(f'Generation: {message[1]}')
            gen_bar.update()
            p_bar.reset(total=message[2])
        else:
            kind, expr, (obj, rmsd, r2, dmax, davg) = message
            p_bar.write(f'[{i:>6}] {kind:>9} (Obj = {obj:8.4f} | R2 = {r2:6.4f} | RMSD = {rmsd:8.4f} | '
                        f'Dmax = {dmax:8.2e} | Davg = {davg:8.4f}): {expr}')
            p_bar.update()
            i += 1
            if obj < best_obj:
                best_obj = obj
                best_rmsd = rmsd
                best_r2 = r2
                best_dmax = dmax
                best_davg = davg
                best_individual = expr
                best_bar.set_description_str(f'Obj = {best_obj:8.4f} | R2 = {best_r2:6.4f} | RMSD = {best_rmsd:8.4f} | '
                                             f'Dmax = {best_dmax:8.2e} | Davg = {best_davg:8.4f}): {best_individual}')

    gen_bar.close()
    p_bar.close()
    best_bar.close()


def run_symbolic_regression(initial_method: 'CCLMethod', dataset: str, ref_charges: str, parameters: str,
                            user_options: Optional[dict] = None):
    """Run the whole regression process """
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

    # Main metric, RMSD, R2, Dmax, Davg
    creator.create('FitnessMin', base.Fitness, weights=(-1.0, -1.0, 1.0, -1.0, -1.0))
    creator.create('Individual', gp.PrimitiveTree, fitness=creator.FitnessMin, sympy_code='')

    toolbox = base.Toolbox()
    toolbox.register('expr', ccl.regression.deap_gp.gen_half_and_half, pset=pset, min_=1, max_=6, rng=rng)
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)

    toolbox.register('evaluate', evaluate, method_skeleton=initial_method, cache=cache, ccl_objects=ccl_objects,
                     options=options, message_queue=q)
    toolbox.register('select', ccl.regression.deap_gp.sel_double_tournament, fitness_size=10, parsimony_size=1.4,
                     rng=rng)
    toolbox.register('mate', ccl.regression.deap_gp.cx_one_point, rng=rng)
    toolbox.register('expr_mut', ccl.regression.deap_gp.gen_full, min_=0, max_=3, rng=rng)
    toolbox.register('mutate', ccl.regression.deap_gp.mutate, expr=toolbox.expr_mut, pset=pset, rng=rng)

    toolbox.decorate('mate', gp.staticLimit(operator.attrgetter('height'), 10))
    toolbox.decorate('mutate', gp.staticLimit(operator.attrgetter('height'), 10))

    if options['unique_symbols']:
        toolbox.decorate('mate', gp.staticLimit(lambda x: int(not check_unique_symbols(x, options)), 0))
        toolbox.decorate('mutate', gp.staticLimit(lambda x: int(not check_unique_symbols(x, options)), 0))

    rmsd_stats = tools.Statistics(key=lambda x: x.fitness.values[1])
    r2_stats = tools.Statistics(key=lambda x: x.fitness.values[2])
    dmax_stats = tools.Statistics(key=lambda x: x.fitness.values[3])
    davg_stats = tools.Statistics(key=lambda x: x.fitness.values[4])

    all_stats = tools.MultiStatistics(RMSD=rmsd_stats, R2=r2_stats, Dmax=dmax_stats, Davg=davg_stats)

    all_stats.register('min', lambda x: np.min(np.array(x)[np.isfinite(x)]))
    all_stats.register('med', lambda x: np.median(np.array(x)[np.isfinite(x)]))
    all_stats.register('max', lambda x: np.max(np.array(x)[np.isfinite(x)]))

    logbook = tools.Logbook()

    hof = tools.HallOfFame(options['top_results'], similar=lambda x, y: x.sympy_code == y.sympy_code)

    print_options(options)

    # Run GP algorithm

    pop = []
    if options['seeded_individuals'] is not None:
        print('*** Seeding initial population ***')
        try:
            pop.extend(add_seeded_individuals(toolbox, options, ccl_objects, pset))
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            raise e

    print('*** Generating initial population ***')
    pop.extend(generate_population(toolbox, ccl_objects, options))

    executor = concurrent.futures.ProcessPoolExecutor(options['ncpus'],
                                                      initializer=init,
                                                      initargs=(dataset, ref_charges, parameters))
    toolbox.register('map', executor.map)

    progress_process = multiprocessing.Process(target=progress_bar, args=(q, options))

    q.put(('gen', 0, len(pop)))

    progress_process.start()
    evaluate_population(pop, toolbox)

    hof.update(pop)
    record = all_stats.compile(pop)
    logbook.record(gen=0, evals=len(pop), **record, best=hof[0].sympy_code)

    for gen in range(options['generations']):
        if options['early_exit']:
            if (options['metric'] == 'RMSD' and record['RMSD']['min'] < 1e-4) or \
                    options['metric'] == 'R2' and record['R2']['max'] > 1 - 1e-4:
                break

        offspring = toolbox.select(pop, len(pop))
        offspring = algorithms.varAnd(offspring, toolbox, options['crossover_probability'],
                                      options['mutation_probability'])

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        q.put(('gen', gen + 1, len(invalid_ind)))

        generate_sympy_codes(invalid_ind, ccl_objects)
        evaluate_population(invalid_ind, toolbox)
        pop[:] = offspring

        hof.update(pop)
        record = all_stats.compile(pop)
        logbook.record(gen=gen + 1, evals=len(invalid_ind), **record, best=hof[0].sympy_code)

    executor.shutdown(wait=True)
    q.put(None)
    progress_process.join()

    end_time = datetime.datetime.now().replace(microsecond=0)

    if options['save_best'] is not None:
        with open(options['save_best'], 'w') as f:
            for ind in hof:
                f.write(f'{ind}\n')

    logger = logging.getLogger('CCL Regression Logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    if options['results'] is not None:
        logger.addHandler(logging.FileHandler(options['results']))

    logger.info(f'\n{"=" * 30} RESULTS {"=" * 30}\n')
    logger.info('\n*** Used files ***')
    logger.info(f'Structures       : {dataset}')
    logger.info(f'Reference charges: {ref_charges}')
    logger.info(f'Parameters:      : {parameters}')

    logger.info('\n*** Original skeleton ***')
    logger.info(initial_method.source)
    logger.info('*** Settings ***')
    max_size = max(len(opt) for opt in options)
    for opt, value in options.items():
        logger.info(f'{opt:<{max_size + 1}} {value}')

    best_count = min(len(hof), options['top_results'])
    logger.info(f'\n*** Best individuals encountered ({best_count}) ***')

    for i in range(best_count):
        logger.info(f'Obj = {hof[i].fitness.values[0]: 6.4f} | '
                    f'RMSD = {hof[i].fitness.values[1]: 6.4f} | '
                    f'R2 = {hof[i].fitness.values[2]: 8.4f} | '
                    f'Dmax = {hof[i].fitness.values[3]: 8.4f} | '
                    f'Davg = {hof[i].fitness.values[4]: 8.4f}: '
                    f'{hof[i].sympy_code}')

    logbook.header = 'gen', 'evals', 'RMSD', 'R2', 'Dmax', 'Davg', 'best'
    logbook.chapters['RMSD'].header = 'min', 'med', 'max'
    logbook.chapters['R2'].header = 'min', 'med', 'max'
    logbook.chapters['Dmax'].header = 'min', 'med', 'max'
    logbook.chapters['Davg'].header = 'min', 'med', 'max'
    logger.info('\n*** Statistics over generations ***')
    logger.info(logbook)

    time_format = '%d %B %Y: %H:%M:%S'
    logger.info('\n*** Time stats ***')
    logger.info(f'Started: {start_time.strftime(time_format)}')
    logger.info(f'Ended:   {end_time.strftime(time_format)}')
    logger.info(f'Elapsed: {end_time - start_time}')
