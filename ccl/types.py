from typing import Union, Tuple

from ccl.common import NoValEnum


class Type:
    pass


class StringType(Type):
    def __repr__(self):
        return 'String'


class BoolType(Type):
    def __repr__(self):
        return 'Bool'


class ObjectType(Type, NoValEnum):
    ATOM = 'Atom'
    BOND = 'Bond'


class NumericType(Type, NoValEnum):
    INT = 'Int'
    FLOAT = 'Float'


class ParameterType(Type, NoValEnum):
    ATOM = 'Atom Parameter'
    BOND = 'Bond Parameter'
    COMMON = 'Common Parameter'


class ArrayType(Type):
    def __init__(self, *indices: ObjectType) -> None:
        self.indices: Tuple[ObjectType, ...] = indices

    def __repr__(self) -> str:
        return f'ArrayType{self.indices}'

    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.indices)
        return f'Float[{args_str}]'

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.indices == other.indices

    def dim(self) -> int:
        return len(self.indices)


class FunctionType(Type):
    def __init__(self, return_type: Union[BoolType, NumericType, ArrayType],
                 *args: Union[ObjectType, NumericType, ArrayType, StringType]) -> None:
        self.args: Tuple[Union[ObjectType, NumericType, ArrayType, StringType], ...] = args
        self.return_type: Union[BoolType, NumericType, ArrayType] = return_type

    def __repr__(self) -> str:
        return f'FunctionType{self.args} -> {self.return_type}'

    def __str__(self) -> str:
        args_str = ' x '.join(f'{arg}' for arg in self.args)
        return f'{args_str} -> {self.return_type}'

    def __eq__(self, other) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return self.args == other.args and self.return_type == other.return_type


class PredicateType(FunctionType):
    def __init__(self, *args: Union[ObjectType, NumericType, StringType]):
        super().__init__(BoolType(), *args)

    def __repr__(self):
        return f'PredicateType{self.args} -> Bool'
