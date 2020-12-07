"""Functions for generating the initial population"""

from typing import List, Set

import sympy
import tqdm
from deap import base, gp, creator

from ccl.regression.constraints import check_max_constant, check_symbol_counts
from ccl.regression.generators import generate_sympy_expr


def generate_population(toolbox: base.Toolbox, ccl_objects: dict, options: dict) -> List[gp.PrimitiveTree]:
    """Generate initial population"""

    pop = []
    codes: Set[str] = set()
    pbar = tqdm.tqdm(total=options['population_size'])
    while len(pop) < options['population_size']:
        ind = toolbox.individual()
        if not check_symbol_counts(ind, options):
            continue
        try:
            sympy_expr = generate_sympy_expr(ind, ccl_objects)
            if sympy_expr.has(sympy.zoo, sympy.oo, sympy.nan, sympy.I):
                continue
            sympy_code = str(sympy_expr)
        except RuntimeError:
            continue

        if options['max_constant_allowed'] is not None and not check_max_constant(sympy_expr, options):
            continue

        if options['unique_population']:
            if sympy_code in codes:
                continue

        codes.add(sympy_code)
        ind.sympy_code = sympy_code
        pop.append(ind)
        pbar.update()

    pbar.close()
    return pop


def add_seeded_individuals(toolbox: base.Toolbox, options: dict, ccl_objects: dict,
                           primitive_set: gp.PrimitiveSetTyped) -> List[gp.PrimitiveTree]:
    """Add individuals specified by user and their mutations"""
    pop = []
    codes = set()
    raw_codes = []
    with open(options['seeded_individuals']) as f:
        for line in f:
            raw_codes.append(line.strip())

    for no, ind in enumerate(raw_codes):
        try:
            x = creator.Individual(gp.PrimitiveTree.from_string(ind, primitive_set))
        except TypeError:
            raise RuntimeError(f'Incorrect seeded individual (probably incorrect symbol): {ind}')
        try:
            sympy_code = str(generate_sympy_expr(x, ccl_objects))
        except RuntimeError:
            raise RuntimeError(f'Initial individual causes problem: {ind}')
        print(f'[Seed {no:2d} No mutation]: {sympy_code}')
        x.sympy_code = sympy_code
        pop.append(x)
        i = 0
        codes.add(sympy_code)
        while i < options['initial_seed_mutations']:
            y = toolbox.clone(x)
            try:
                y, = toolbox.mutate(y)
            except IndexError:
                raise RuntimeError(f'Incorrect seeded individual (probably wrong arity): {ind}')
            if not check_symbol_counts(y, options):
                continue
            try:
                mut_sympy_expr = generate_sympy_expr(y, ccl_objects)
                mut_sympy_code = str(mut_sympy_expr)
            except RuntimeError:
                continue

            if mut_sympy_code in codes:
                continue

            if mut_sympy_expr.has(sympy.zoo, sympy.oo, sympy.nan, sympy.I):
                continue

            if options['max_constant_allowed'] is not None and not check_max_constant(mut_sympy_expr, options):
                continue

            codes.add(mut_sympy_code)
            i += 1
            print(f'[Seed {no:2d} Mutation {i:2d}]: {mut_sympy_code}')
            y.sympy_code = mut_sympy_code
            pop.append(y)
    return pop
