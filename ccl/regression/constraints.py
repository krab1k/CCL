"""Constraints that can be imposed on and individual"""

import sympy
from deap import gp


def check_symmetry(sympy_expr: sympy.Expr, ccl_objects: dict) -> bool:
    """Check whether the expression is symmetric in atom variables"""

    objects = ccl_objects['atom_objects']
    assert len(objects) in {0, 2}

    if not objects:
        return True

    substitutions = {objects[0]: objects[1],
                     objects[1]: objects[0]}

    sympy_expr_swapped = sympy_expr.subs(substitutions, simultaneous=True)
    return (sympy_expr - sympy_expr_swapped) == 0


def check_required_symbols(individual: gp.PrimitiveTree, options: dict) -> bool:
    """Check whether an individual contains required or disabled symbols"""
    required = set(options['required_symbols'])
    for primitive in individual:
        if primitive.name in required:
            required.remove(primitive.name)

    return len(required) == 0


def check_max_constant(sympy_expr: sympy.Expr, options: dict) -> bool:
    """Check whether the expression contains constant that is higher than allowed"""
    for atom in sympy_expr.atoms():
        if atom.is_real and abs(atom) > options['max_constant_allowed']:
            return False
    return True
