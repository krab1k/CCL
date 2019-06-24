"""Common functions defined in CCL"""

from ccl.types import *


class Function:
    """General function class"""
    def __init__(self, name: str, fn_type: FunctionType) -> None:
        self.name: str = name
        self.type: FunctionType = fn_type

    def __str__(self) -> str:
        return f'{self.name}: {self.type}'


FUNCTIONS = {}
MATH_FUNCTIONS = {'exp', 'sqrt', 'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh'}

# Add common math functions
for fn in MATH_FUNCTIONS:
    FUNCTIONS[fn] = Function(fn, FunctionType(NumericType.FLOAT, NumericType.FLOAT))

FUNCTIONS['inv'] = Function('inv', FunctionType(ArrayType(ObjectType.ATOM, ObjectType.ATOM),
                                                ArrayType(ObjectType.ATOM, ObjectType.ATOM)))


# Add atom properties
_FLOAT_ELEMENT_PROPERTIES = {'electronegativity', 'covalent radius', 'van der waals radius', 'hardness',
                             'ionization potential', 'electron affinity'}
_INT_ELEMENT_PROPERTIES = {'atomic number', 'valence electron count'}

for prop in _FLOAT_ELEMENT_PROPERTIES:
    FUNCTIONS[prop] = Function(prop, FunctionType(NumericType.FLOAT, ObjectType.ATOM))

for prop in _INT_ELEMENT_PROPERTIES | {'formal charge'}:
    FUNCTIONS[prop] = Function(prop, FunctionType(NumericType.INT, ObjectType.ATOM))


ELEMENT_PROPERTIES = _FLOAT_ELEMENT_PROPERTIES | _INT_ELEMENT_PROPERTIES


# Add bond properties
FUNCTIONS['bond order'] = Function('bond order', FunctionType(NumericType.INT, ObjectType.BOND))


# Add custom functions
FUNCTIONS['distance'] = Function('distance', FunctionType(NumericType.FLOAT, ObjectType.ATOM, ObjectType.ATOM))

PREDICATES = {'element': Function('element', PredicateType(ObjectType.ATOM, StringType())),
              'bonded': Function('bonded', PredicateType(ObjectType.ATOM, ObjectType.ATOM)),
              'near': Function('near', PredicateType(ObjectType.ATOM, ObjectType.ATOM, NumericType.FLOAT)),
              'bond_distance': Function('bond_distance',
                                        PredicateType(ObjectType.ATOM, ObjectType.ATOM, NumericType.INT))}

# TODO Sum functions (inv, distance,..) may use something like ObjectType.ANY
