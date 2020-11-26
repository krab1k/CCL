"""Evaluate the fitness of an individual"""

import concurrent.futures
import functools
import math
import multiprocessing
import shutil
import subprocess
import sys
import tempfile
from typing import Tuple, List

import chargefw2_python
import sympy
from deap import gp, base

import ccl.errors
from ccl.regression.generators import generate_optimized_ccl_code, generate_sympy_expr


data = None


def init(dataset: str, ref_charges: str, parameters: str) -> None:
    """Initialize the data shared across the evaluations"""
    global data
    data = chargefw2_python.Data(dataset, ref_charges, parameters)


def get_objective_value(fitness: Tuple[float, float, float, float], options: dict) -> float:
    """Return the value of the objective function"""

    if any(not math.isfinite(x) for x in fitness):
        return math.inf

    def map_to_01(x: float, half: float) -> float:
        """Map value from [0; oo) to [0; 1) using half as 0.5"""
        return 2 / math.pi * math.atan(x / half)

    if options['metric'] == 'COMBINED':
        # Combine R2 and RMSD into metric ranging from 0 to 1
        return 0.5 * (1 - fitness[1] + map_to_01(fitness[0], 0.1))
    elif options['metric'] == 'RMSD':
        return fitness[0]
    else:
        return 1 - fitness[1]


def evaluate(individual: 'creator.Individual', method_skeleton: 'CCLMethod', cache: dict, ccl_objects: dict, options: dict,
             message_queue: multiprocessing.Queue) -> Tuple[float, float, float, float, float]:
    """Evaluate individual by calculating RMSD or R2 between new and reference charges"""
    invalid_result = math.inf, -math.inf, math.inf, math.inf, math.inf

    assert hasattr(individual, 'sympy_code')
    assert individual.sympy_code != ''

    if individual.sympy_code == '<expr-error>' or individual.sympy_code.startswith('<non-real>'):
        message_queue.put(('Invalid', individual.sympy_code, invalid_result))
        return invalid_result

    if str(individual.sympy_code) in cache:
        message_queue.put(('Cached', individual.sympy_code, cache[individual.sympy_code]))
        return cache[individual.sympy_code]

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
    try:
        result = chargefw2_python.evaluate(data, f'{tmpdir}/libREGRESSION.so')
    except RuntimeError:
        message_queue.put(('Invalid', individual.sympy_code, invalid_result))
        return invalid_result

    shutil.rmtree(tmpdir)

    # Check whether the charges were successfully computed
    if any(x < 0 for x in result):
        result = invalid_result
    else:
        result = get_objective_value(result, options), *result

    message_queue.put(('Evaluated', individual.sympy_code, result))
    cache[individual.sympy_code] = result
    return result


def evaluate_population(pop: List[gp.PrimitiveTree], toolbox: base.Toolbox) -> None:
    """Evaluate the fitness for each individual in the population"""
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit


def generate_sympy_code(x: gp.PrimitiveTree, ccl_objects: dict) -> str:
    """Generate sympy code for an individual"""
    try:
        sympy_expr = generate_sympy_expr(x, ccl_objects).evalf(2)
        sympy_code = str(sympy_expr)
        if sympy_expr.has(sympy.zoo, sympy.oo, sympy.nan, sympy.I):
            return f'<non-real>: {sympy_code}'
    except:
        return '<expr-error>'
    return str(sympy_expr)


def generate_sympy_codes(pop: List[gp.PrimitiveTree], ccl_objects: dict) -> None:
    """Generate sympy codes for all individuals in the population"""
    executor = concurrent.futures.ProcessPoolExecutor()
    sympy_codes = executor.map(functools.partial(generate_sympy_code, ccl_objects=ccl_objects), pop)
    for ind, sympy_code in zip(pop, sympy_codes):
        ind.sympy_code = sympy_code
