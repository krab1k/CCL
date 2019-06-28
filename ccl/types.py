"""Types used in CCL"""

from typing import Union, Tuple, Type

from ccl.common import NoValEnum


class CCLType:
    """Baseclass type"""
    pass


class StringType(CCLType):
    """String type"""
    def __repr__(self) -> str:
        return 'String'


class BoolType(CCLType):
    """Boolean type"""
    def __repr__(self) -> str:
        return 'Bool'


class ObjectType(CCLType, NoValEnum):
    """Type for atom or bond"""
    ATOM = 'Atom'
    BOND = 'Bond'


class NumericType(CCLType, NoValEnum):
    """Integer or floating point type"""
    INT = 'Int'
    FLOAT = 'Float'


class ParameterType(CCLType, NoValEnum):
    """Type for parameters"""
    ATOM = 'Atom Parameter'
    BOND = 'Bond Parameter'
    COMMON = 'Common Parameter'


class ArrayType(CCLType):
    """Type representing an array"""
    def __init__(self, *indices: ObjectType) -> None:
        self.indices: Tuple[ObjectType, ...] = indices

    def __repr__(self) -> str:
        return f'ArrayType{self.indices}'

    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.indices)
        return f'Float[{args_str}]'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.indices == other.indices

    def dim(self) -> int:
        return len(self.indices)


class FunctionType(CCLType):
    """Function type"""
    def __init__(self, return_type: Union[Type[BoolType], NumericType, ArrayType],
                 *args: Union[ObjectType, NumericType, ArrayType, Type[StringType]]) -> None:
        self.args: Tuple[Union[ObjectType, NumericType, ArrayType, Type[StringType]], ...] = args
        self.return_type: Union[Type[BoolType], NumericType, ArrayType] = return_type

    def __repr__(self) -> str:
        return f'FunctionType{self.args} -> {self.return_type}'

    def __str__(self) -> str:
        args_str = ' x '.join(f'{arg}' for arg in self.args)
        return f'{args_str} -> {self.return_type}'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return self.args == other.args and self.return_type == other.return_type


class PredicateType(FunctionType):
    """Functions returing boolean"""
    def __init__(self, *args: Union[ObjectType, NumericType, Type[StringType]]):
        super().__init__(BoolType, *args)

    def __repr__(self) -> str:
        return f'PredicateType{self.args} -> Bool'
