"""CCL's abstract syntax tree elements"""

from enum import Enum
from typing import List, Optional, Generator, Any

from ccl.types import *


class ASTNode:
    """General AST node"""
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

    def __iter__(self) -> Generator[Tuple[str, Any], None, None]:
        for attr in self.__dir__():
            yield attr, getattr(self, attr)


class ASTVisitor:
    """General visitor for AST"""
    def visit(self, node: ASTNode) -> Any:
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        for _, value in node:
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(value, ASTNode):
                self.visit(value)


class ParentSetter:
    """Set parent node for each node in AST"""
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


class Statement(ASTNode):
    """Base class for every statement in CCL"""


class Annotation(ASTNode):
    """Base class for every annotation in CCL"""


class Constraint(ASTNode):
    """Base class for every constraint in CCL"""


class Method(ASTNode):
    def __init__(self, pos: Tuple[int, int], name: str, statements: List[Statement],
                 annotations: List[Annotation]) -> None:
        super().__init__(pos)
        self.statements: List[Statement] = statements
        self.annotations: List[Annotation] = annotations
        self.symbol_table = None
        self.name: str = name

    def print_ast(self) -> None:
        for statement in self.statements:
            print(statement)

        for annotation in self.annotations:
            print(annotation)


class Expression(ASTNode):
    def __init__(self, pos: Tuple[int, int]) -> None:
        super().__init__(pos)
        self._result_type: Optional[Union[NumericType, ArrayType, ParameterType, ObjectType, FunctionType]] = None

    @property
    def result_type(self) -> Optional[Union[NumericType, ArrayType, ParameterType, ObjectType, FunctionType]]:
        return self._result_type

    @result_type.setter
    def result_type(self, value: Union[NumericType, ArrayType, ParameterType, ObjectType, FunctionType]) -> None:
        self._result_type = value


class Number(Expression):
    def __init__(self, pos: Tuple[int, int], val: Union[int, float], ntype: NumericType) -> None:
        super().__init__(pos)
        self.val: Union[int, float] = val
        self.result_type = ntype

    def __repr__(self) -> str:
        return f'Number({self.val})'

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.val == other.val and self.result_type == other.result_type
        else:
            return False

    def __hash__(self):
        return hash(self.val) ^ hash(self.result_type)


class Name(Expression):
    def __init__(self, pos: Tuple[int, int], name: str) -> None:
        super().__init__(pos)
        self.val: str = name

    def __repr__(self) -> str:
        return f'Name({self.val})'

    def __eq__(self, other):
        if isinstance(other, Name):
            return self.val == other.val
        else:
            return False

    def __hash__(self):
        return hash(self.val)


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
    def __init__(self, pos: Tuple[int, int], name: Name, indices: List[Name]) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.indices: List[Name] = indices

    def __repr__(self) -> str:
        indices_str = ', '.join(str(i) for i in self.indices)
        return f'Subscript({self.name}, [{indices_str}])'


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
    def __init__(self, pos: Tuple[int, int], lhs: Union[Name, Subscript], rhs: Expression) -> None:
        super().__init__(pos)
        self.lhs: Union[Name, Subscript] = lhs
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
    def __init__(self, pos: Tuple[int, int], name: Name, otype: ObjectType, atom_indices: Optional[Tuple[str, str]],
                 constraints: Constraint, body: List[Statement]) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.type: ObjectType = otype
        self.atom_indices: Optional[Tuple[str, str]] = atom_indices
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

    def __eq__(self, other):
        if isinstance(other, RelOp):
            return self.lhs == other.lhs and self.rhs == self.rhs and self.op == other.op
        else:
            return False

    def __hash__(self):
        return hash(self.lhs) ^ hash(self.rhs) ^ hash(self.op)


class UnaryLogicalOp(Constraint):
    class Ops(NoValEnum):
        NOT = 'Not'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryLogicalOp.Ops', constraint: Constraint) -> None:
        super().__init__(pos)
        self.op: UnaryLogicalOp.Ops = op
        self.constraint: Constraint = constraint

    def __eq__(self, other):
        if isinstance(other, UnaryLogicalOp):
            return self.op == other.op and self.constraint == other.constraint
        else:
            return False

    def __hash__(self):
        return hash(self.op) ^ hash(self.constraint)


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

    def __eq__(self, other):
        if isinstance(other, RelOp):
            return self.lhs == other.lhs and self.rhs == self.rhs and self.op == other.op
        else:
            return False

    def __hash__(self):
        return hash(self.lhs) ^ hash(self.rhs) ^ hash(self.op)


class Predicate(Constraint):
    def __init__(self, pos: Tuple[int, int], name: str, args: Tuple[Union[Number, Name]]) -> None:
        super().__init__(pos)
        self.name: str = name
        self.args: Tuple[Union[Number, Name]] = args

    def __eq__(self, other):
        if isinstance(other, Predicate):
            return self.name == other.name and self.args == other.args
        else:
            return False

    def __hash__(self):
        return hash(self.name) ^ hash(self.args)


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
    def __init__(self, pos: Tuple[int, int], name: str, otype: ObjectType, atom_indices: Union[None, Tuple[str, str]],
                 constraints: Optional[Constraint]) -> None:
        super().__init__(pos)
        self.name: str = name
        self.type: ObjectType = otype
        self.atom_indices: Optional[Tuple[str, str]] = atom_indices
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
