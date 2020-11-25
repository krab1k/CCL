"""Constraints that can be imposed on and individual"""

import sympy
from deap import gp


def check_symmetry(sympy_expr: sympy.Expr, ccl_objects: dict) -> bool:
    """Check whether the expression is symmetric in atom or bond variables"""
    substitutions = {}
    for ab_type in ['atom_objects', 'bond_objects']:
        if ccl_objects[ab_type]:
            x = ccl_objects[ab_type][0]
            y = ccl_objects[ab_type][1]
            substitutions[x] = y
            substitutions[y] = x

    sympy_expr_swapped = sympy.simplify(sympy_expr.subs(substitutions, simultaneous=True))
    return sympy_expr == sympy_expr_swapped


def check_symbols(individual: gp.PrimitiveTree, options: dict) -> bool:
    """Check whether an individual contains required or disabled symbols"""
    required = options['required_symbols'].copy() if options['required_symbols'] is not None else set()
    disabled = options['disabled_symbols'] if options['disabled_symbols'] is not None else set()
    for primitive in individual:
        if primitive.name in disabled:
            return False
        elif primitive.name in required:
            required.remove(primitive.name)

    return len(required) == 0


def check_max_constant(sympy_code: sympy.Expr, options: dict) -> bool:
    """Check whether the expression contains constant that is higher than allowed"""
    for atom in sympy_code.atoms():
        if atom.is_real and abs(atom) > options['max_constant_allowed']:
            return False
    return True
