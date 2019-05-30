"""CCL's abstract syntax tree elements"""

from typing import List, Union, Tuple, Optional, Set, Generator, Any
from enum import Enum


class NoValEnum(Enum):
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self.name}'

    def __str__(self) -> str:
        return f'{self.value}'


class Type:
    pass


class VarContext(Type, NoValEnum):
    LOAD = 'Load'
    STORE = 'Store'


class ObjectType(Type, NoValEnum):
    ATOM = 'Atom'
    BOND = 'Bond'


class NumericType(Type, NoValEnum):
    INT = 'Int'
    FLOAT = 'Float'


class ParameterType(Type, NoValEnum):
    ATOM = 'Atom'
    BOND = 'Bond'
    COMMON = 'Common'


class ArrayType(Type):
    def __init__(self, *indices: ObjectType) -> None:
        self.indices: Tuple[ObjectType, ...] = indices

    def __repr__(self) -> str:
        return f'ArrayType{self.indices}'

    def __str__(self) -> str:
        args_str = ', '.join(f'{arg}' for arg in self.indices)
        return f'Float[{args_str}]'

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.indices == other.indices


class FunctionType(Type):
    def __init__(self, return_type: NumericType, *args: Union[ObjectType, NumericType]) -> None:
        self.args: Tuple[Union[ObjectType, NumericType], ...] = args
        self.return_type: NumericType = return_type

    def __repr__(self) -> str:
        return f'FunctionType{self.args} -> {self.return_type}'

    def __str__(self) -> str:
        args_str = ' x '.join(f'{arg}' for arg in self.args)
        return f'{args_str} -> {self.return_type}'

    def __eq__(self, other) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return self.args == other.args and self.return_type == other.return_type


class ASTNode:
    _fields = ()
    _internal = ('line', 'column', 'parent')

    def __init__(self, pos: Tuple[int, int]) -> None:
        self.line: int = pos[0]
        self.column: int = pos[1]
        self.parent: Optional['ASTNode'] = None

    def __dir__(self) -> List[str]:
        return list(k for k in self.__dict__ if k not in ASTNode._internal)

    def __repr__(self) -> str:
        attr_value = []
        for attr in dir(self):
            value = getattr(self, attr)
            if isinstance(value, str):
                attr_value.append(f'{attr}=\'{value}\'')
            else:
                attr_value.append(f'{attr}={value}')

        string = ', '.join(attr_value)
        return f'{self.__class__.__qualname__}({string})'

    def __iter__(self) -> Generator[Tuple[str, str], None, None]:
        for attr in self.__dir__():
            yield attr, getattr(self, attr)


class ASTVisitor:
    def visit(self, node: ASTNode) -> Any:
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        for _, value in node:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(value, ASTNode):
                self.visit(value)


class ParentSetter:
    def visit(self, node: ASTNode) -> None:
        for _, value in node:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        item.parent = node
                        self.visit(item)
            elif isinstance(value, ASTNode):
                value.parent = node
                self.visit(value)


class NameGetter:
    @classmethod
    def visit(cls, node: ASTNode) -> Set[str]:
        names = set()
        if isinstance(node, Name):
            names.add(node.val)
        for _, value in node:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        names = names | cls.visit(item)
            elif isinstance(value, ASTNode):
                names = names | cls.visit(value)

        return names


class Statement(ASTNode):
    pass


class Annotation(ASTNode):
    pass


class Constraint(ASTNode):
    pass


class Method(ASTNode):
    def __init__(self, pos: Tuple[int, int], name: str, statements: List[Statement],
                 annotations: List[Annotation]) -> None:
        super().__init__(pos)
        self.statements: List[Statement] = statements
        self.annotations: List[Annotation] = annotations
        self.symbol_table = None
        self.name = name

    def print_ast(self) -> None:
        for s in self.statements:
            print(s)

        for a in self.annotations:
            print(a)


class Expression(ASTNode):
    def __init__(self, pos: Tuple[int, int]) -> None:
        super().__init__(pos)
        self._result_type: Optional[Union[NumericType, ParameterType, ObjectType]] = None

    @property
    def result_type(self) -> Union[NumericType, ParameterType, ObjectType]:
        return self._result_type

    @result_type.setter
    def result_type(self, value: Union[NumericType, ParameterType, ObjectType]) -> None:
        self._result_type = value


class Number(Expression):
    def __init__(self, pos: Tuple[int, int], val: Union[int, float], ntype: NumericType) -> None:
        super().__init__(pos)
        self.val: Union[int, float] = val
        self.result_type = ntype


class Name(Expression):
    def __init__(self, pos: Tuple[int, int], name: str, ctx: VarContext) -> None:
        super().__init__(pos)
        self.val: str = name
        self.ctx: VarContext = ctx


class BinaryOp(Expression):
    class Ops(NoValEnum):
        ADD = '+'
        SUB = '-'
        MUL = '*'
        DIV = '/'
        POW = '^'

    def __init__(self, pos: Tuple[int, int], left: Expression, op: 'BinaryOp.Ops', right: Expression) -> None:
        super().__init__(pos)
        self.left: Expression = left
        self.right: Expression = right
        self.op: BinaryOp.Ops = op


class UnaryOp(Expression):
    class Ops(Enum):
        NEG = '-'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryOp.Ops', expr: Expression) -> None:
        super().__init__(pos)
        self.op: UnaryOp.Ops = op
        self.expr: Expression = expr


class Sum(Expression):
    def __init__(self, pos: Tuple[int, int], name: Name, expr: Expression) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.expr: Expression = expr


class Subscript(Expression):
    def __init__(self, pos: Tuple[int, int], name: Name, indices: List[Name], ctx: VarContext) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.indices: List[Name] = indices
        self.ctx: VarContext = ctx


class Function(Expression):
    def __init__(self, pos: Tuple[int, int], name: str, arg: Expression) -> None:
        super().__init__(pos)
        self.name: str = name
        self.arg: Expression = arg


class EE(Expression):
    class Type(NoValEnum):
        FULL = 'Full'
        CUTOFF = 'Cutoff'
        COVER = 'Cover'

    def __init__(self, pos: Tuple[int, int], idx_row: str, idx_col: str, diag: Expression, off: Expression,
                 rhs: Expression, ee_type: 'EE.Type', radius: Optional[NumericType]) -> None:
        super().__init__(pos)
        self.idx_row: str = idx_row
        self.idx_col: str = idx_col
        self.diag: Expression = diag
        self.off: Expression = off
        self.rhs: Expression = rhs
        self.type: 'EE.Type' = ee_type
        self.radius: Optional[NumericType] = radius


class Assign(Statement):
    def __init__(self, pos: Tuple[int, int], lhs: Expression, rhs: Expression) -> None:
        super().__init__(pos)
        self.lhs: Expression = lhs
        self.rhs: Expression = rhs


class For(Statement):
    def __init__(self, pos: Tuple[int, int], name: Name, value_from: Number, value_to: Number, body: List[Statement]) \
            -> None:
        super().__init__(pos)
        self.name: Name = name
        self.value_from: Number = value_from
        self.value_to: Number = value_to
        self.body: List[Statement] = body
        self.symbol_table = None


class ForEach(Statement):
    def __init__(self, pos: Tuple[int, int], name: Name, otype: ObjectType, constraints: Constraint,
                 body: List[Statement]) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.type: ObjectType = otype
        self.constraints: Constraint = constraints
        self.body: List[Statement] = body
        self.symbol_table = None


class BinaryLogicalOp(Constraint):
    class Ops(NoValEnum):
        AND = 'And'
        OR = 'Or'

    def __init__(self, pos: Tuple[int, int], lhs: Constraint, op: 'BinaryLogicalOp.Ops', rhs: Constraint) -> None:
        super().__init__(pos)
        self.lhs: Constraint = lhs
        self.rhs: Constraint = rhs
        self.op: BinaryLogicalOp.Ops = op


class UnaryLogicalOp(Constraint):
    class Ops(NoValEnum):
        NOT = 'Not'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryLogicalOp.Ops', constraint: Constraint) -> None:
        super().__init__(pos)
        self.op: UnaryLogicalOp.Ops = op
        self.constraint: Constraint = constraint


class RelOp(Constraint):
    class Ops(NoValEnum):
        LT = '<'
        LE = '<='
        GT = '>'
        GE = '>='
        EQ = '=='
        NEQ = '!='

    def __init__(self, pos: Tuple[int, int], lhs: Expression, op: 'RelOp.Ops', rhs: Expression) -> None:
        super().__init__(pos)
        self.lhs: Expression = lhs
        self.rhs: Expression = rhs
        self.op: RelOp.Ops = op


class Predicate(Constraint):
    def __init__(self, pos: Tuple[int, int], name: str, args: List[Union[Number, Name]]) -> None:
        super().__init__(pos)
        self.name: str = name
        self.args: List[Union[Number, Name]] = args


class Parameter(Annotation):
    def __init__(self, pos: Tuple[int, int], name: str, ptype: ParameterType) -> None:
        super().__init__(pos)
        self.name: str = name
        self.type: ParameterType = ptype


class Substitution(Annotation):
    def __init__(self, pos: Tuple[int, int], lhs: Union[Name, Subscript], rhs: Expression,
                 constraints: Optional[Constraint]) -> None:
        super().__init__(pos)
        self.lhs: Union[Name, Subscript] = lhs
        self.rhs: Expression = rhs
        self.constraints: Optional[Constraint] = constraints


class Object(Annotation):
    def __init__(self, pos: Tuple[int, int], name: str, otype: ObjectType, constraints: Optional[Constraint]) -> None:
        super().__init__(pos)
        self.name: str = name
        self.type: ObjectType = otype
        self.constraints: Optional[Constraint] = constraints


class Property(Annotation):
    def __init__(self, pos: Tuple[int, int], name: str, prop: str) -> None:
        super().__init__(pos)
        self.name: str = name
        self.prop: str = prop


class Constant(Annotation):
    def __init__(self, pos: Tuple[int, int], name: str, prop: str, element: str) -> None:
        super().__init__(pos)
        self.name: str = name
        self.prop: str = prop
        self.element: str = element


def is_atom(node: ASTNode) -> bool:
    if isinstance(node, Subscript):
        return True
    if isinstance(node, Name):
        return True
    if isinstance(node, Number):
        return True

    return False
