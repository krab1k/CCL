"""Initialization of the GP primitive set"""

import random
from typing import Tuple

from deap import gp

import ccl.ast
import ccl.functions
import ccl.symboltable
import ccl.types


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

    if options['allow_random_constants']:
        primitive_set.addEphemeralConstant('rand', lambda: round(rng.random() * 2, 1), float)

    primitive_set.addTerminal('0.5', float, '0.5')
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
