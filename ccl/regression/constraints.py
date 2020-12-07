"""Constraints that can be imposed on and individual"""

import sympy
from collections import Counter
from deap import gp


def _get_primitive_name(primitive: gp.Primitive) -> str:
    """Get the original name from a possibly mangled primitive"""
    if primitive.name.startswith('_sym'):
        return primitive.name.split('_')[-1]
    elif primitive.name.startswith('_term'):
        return primitive.name.split('_')[2]
    else:
        return primitive.name


def check_symbol_counts(individual: gp.PrimitiveTree, options: dict) -> bool:
    """Checks that an individual contains specified symbols in required counts"""
    counts = Counter(_get_primitive_name(primitive) for primitive in individual)

    for symbol, (low, high) in options['symbol_counts'].items():
        if low is not None and counts[symbol] < low:
            return False
        if high is not None and counts[symbol] > high:
            return False

    return True


def check_max_constant(sympy_expr: sympy.Expr, options: dict) -> bool:
    """Check whether the expression contains constant that is higher than allowed"""
    for atom in sympy_expr.atoms():
        if atom.is_real and abs(atom) > options['max_constant_allowed']:
            return False
    return True
