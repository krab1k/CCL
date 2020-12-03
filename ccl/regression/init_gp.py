"""Initialization of the GP primitive set"""

import random
from typing import Tuple, List, Iterable

from deap import gp

import ccl.ast
import ccl.functions
import ccl.symboltable
import ccl.types


class AtomObject:
    pass


def prepare_primitive_set(table: ccl.symboltable.SymbolTable, expr: ccl.ast.RegressionExpr, rng: random.Random,
                          options: dict) -> Tuple[gp.PrimitiveSetTyped, dict]:
    """Prepare set of primitives from which the individual is built"""

    def filter_disabled_terms(terms: Iterable[str]) -> List[str]:
        """Return only terms which are not disabled"""
        return [x for x in terms if x not in options['disabled_symbols']]

    if options['required_symbols'] & options['disabled_symbols']:
        raise RuntimeError('Cannot define symbol as required and disabled at the same time')

    input_types = []
    atom_names = []

    atom_properties = []
    atom_parameters = []
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
        elif isinstance(s, ccl.symboltable.FunctionSymbol):
            if s.function.name in ccl.functions.ELEMENT_PROPERTIES:
                atom_properties.append(s.name)
            elif s.function.name == 'distance':
                distance_name = s.name
        elif isinstance(s, ccl.symboltable.ParameterSymbol):
            if s.type == ccl.types.ParameterType.ATOM:
                atom_parameters.append(s.name)
            elif s.type == ccl.types.ParameterType.COMMON:
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

    atom_names.sort()

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

    if options['require_symmetry']:
        for x in filter_disabled_terms(atom_parameters + atom_array_variables + atom_properties):
            primitive_set.addTerminal(f'_sym_add_{x}', float, f'_sym_add_{x}')
            primitive_set.addTerminal(f'_sym_inv_add_{x}', float, f'_sym_inv_add_{x}')
            primitive_set.addTerminal(f'_sym_mul_{x}', float, f'_sym_mul_{x}')
    else:
        for x in filter_disabled_terms(atom_parameters + atom_array_variables + atom_properties):
            primitive_set.addPrimitive(x, [AtomObject], float, x)

    for x in filter_disabled_terms(common_parameters + simple_variables):
        primitive_set.addTerminal(x, float, x)

    if options['use_math_functions']:
        for math_fn in filter_disabled_terms(ccl.functions.MATH_FUNCTIONS):
            primitive_set.addPrimitive(math_fn, [float], float, math_fn)

    if distance_name is not None and distance_name not in options['disabled_symbols']:
        if len(atom_names) != 2:
            raise RuntimeError(f'Distance symbol {distance_name} defined, but 2 atoms variables are required')
        primitive_set.addTerminal(distance_name, float, distance_name)

    primitive_set.renameArguments(**{f'ARG{i}': name for i, name in enumerate(atom_names)})

    if options['require_symmetry']:
        if len(atom_names) not in (0, 2):
            raise RuntimeError('Symmetry requires two atom variables or none')

    ccl_objects = {'distance': distance_name,
                   'single_argument': atom_properties + atom_parameters + atom_array_variables,
                   'atom_objects': atom_names}

    return primitive_set, ccl_objects
