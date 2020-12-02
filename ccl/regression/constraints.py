"""Constraints that can be imposed on and individual"""

import sympy
from collections import Counter
from deap import gp


def check_required_symbols(individual: gp.PrimitiveTree, options: dict) -> bool:
    """Check whether an individual contains required symbols"""
    required = set(options['required_symbols'])
    for primitive in individual:
        if primitive.name.startswith('_sym'):
            name = primitive.name.split('_')[-1]
        else:
            name = primitive.name
        if name in required:
            required.remove(name)
            if not required:
                break

    return len(required) == 0


def check_unique_symbols(individual: gp.PrimitiveTree, options: dict) -> bool:
    """Checks whether an individual contains each unique symbol at most once"""
    counts = Counter({s: 0 for s in options['unique_symbols']})
    for primitive in individual:
        if primitive.name.startswith('_sym'):
            name = primitive.name.split('_')[-1]
        else:
            name = primitive.name

        if name in counts:
            counts[name] += 1
    return all(count <= 1 for count in counts.values())


def check_max_constant(sympy_expr: sympy.Expr, options: dict) -> bool:
    """Check whether the expression contains constant that is higher than allowed"""
    for atom in sympy_expr.atoms():
        if atom.is_real and abs(atom) > options['max_constant_allowed']:
            return False
    return True
