"""CCL's abstract syntax tree elements"""

from enum import Enum
from typing import List, Optional, Iterator, Any, Tuple, Union, TYPE_CHECKING

from ccl.types import *
from ccl.common import NoValEnum

if TYPE_CHECKING:
    from ccl.symboltable import SymbolTable


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

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        for attr in self.__dir__():
            yield attr, getattr(self, attr)


class HasSymbolTable:
    """Node with own symbol table"""
    def __init__(self) -> None:
        self.symbol_table: Optional[SymbolTable] = None


class ASTVisitor:
    """General visitor for AST"""
    def visit(self, node: ASTNode) -> Any:
        """Run appropriate visit method"""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        """Visit all children nodes"""
        for _, value in node:
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(value, ASTNode):
                self.visit(value)


def set_parent_nodes(node: ASTNode) -> None:
    """Set parent node for each node in AST"""
    for _, value in node:
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, ASTNode):
                    item.parent = node
                    set_parent_nodes(item)
        elif isinstance(value, ASTNode):
            value.parent = node
            set_parent_nodes(value)


def search_ast_element(node: ASTNode, query: ASTNode) -> Optional[ASTNode]:
    """Search for a node in AST"""
    if node == query:
        return node

    for _, value in node:
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, ASTNode):
                    if item == query:
                        return item
                    else:
                        res = search_ast_element(item, query)
                        if res is not None:
                            return res

        elif isinstance(value, ASTNode):
            if value == query:
                return value
            else:
                res = search_ast_element(value, query)
                if res is not None:
                    return res

    return None


class Statement(ASTNode):
    """Base class for every statement in CCL"""


class Annotation(ASTNode):
    """Base class for every annotation in CCL"""


class Constraint(ASTNode):
    """Base class for every constraint in CCL"""


class Method(ASTNode, HasSymbolTable):
    """CCL's main node representing method"""
    def __init__(self, pos: Tuple[int, int], name: str, statements: List[Statement],
                 annotations: List[Annotation]) -> None:
        super().__init__(pos)
        self.statements: List[Statement] = statements
        self.annotations: List[Annotation] = annotations
        self.name: str = name

    def print_ast(self) -> None:
        """Simple print of method's AST"""
        for statement in self.statements:
            print(statement)

        for annotation in self.annotations:
            print(annotation)


class Expression(ASTNode):
    """Common class for every expression in CCL"""
    def __init__(self, pos: Tuple[int, int]) -> None:
        super().__init__(pos)
        self._result_type: Optional[Union[NumericType, ArrayType, ParameterType, ObjectType, FunctionType]] = None

    @property
    def result_type(self) -> Optional[Union[NumericType, ArrayType, ParameterType, ObjectType, FunctionType]]:
        """Get the result type of an expression"""
        return self._result_type

    @result_type.setter
    def result_type(self, value: Union[NumericType, ArrayType, ParameterType, ObjectType, FunctionType]) -> None:
        """Set the result type of an expression"""
        self._result_type = value


class Number(Expression):
    """Integer or floating point number"""
    def __init__(self, pos: Tuple[int, int], val: Union[int, float], ntype: NumericType) -> None:
        super().__init__(pos)
        self.val: Union[int, float] = val
        self.result_type = ntype

    def __repr__(self) -> str:
        return f'Number({self.val})'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Number):
            return self.val == other.val and self.result_type == other.result_type
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.val) ^ hash(self.result_type)


class Name(Expression):
    """Simple name"""
    def __init__(self, pos: Tuple[int, int], name: str) -> None:
        super().__init__(pos)
        self.val: str = name

    def __repr__(self) -> str:
        return f'Name({self.val})'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Name):
            return self.val == other.val
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.val)


class BinaryOp(Expression):
    """Binary operation"""
    class Ops(NoValEnum):
        """Enum of all binary operations"""
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
    """Unary operation"""
    class Ops(Enum):
        """Enum of all unary operations"""
        NEG = '-'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryOp.Ops', expr: Expression) -> None:
        super().__init__(pos)
        self.op: UnaryOp.Ops = op
        self.expr: Expression = expr


class Sum(Expression):
    """Summation"""
    def __init__(self, pos: Tuple[int, int], name: Name, expr: Expression) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.expr: Expression = expr


class Subscript(Expression):
    """Indexed name"""
    def __init__(self, pos: Tuple[int, int], name: Name, indices: Tuple[Name, ...]) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.indices: Tuple[Name, ...] = indices

    def __repr__(self) -> str:
        indices_str = ', '.join(str(i) for i in self.indices)
        return f'Subscript({self.name}, [{indices_str}])'


class Function(Expression):
    """Math function"""
    def __init__(self, pos: Tuple[int, int], name: str, arg: Expression) -> None:
        super().__init__(pos)
        self.name: str = name
        self.arg: Expression = arg


class EE(Expression):
    """Electronegativity equalization scheme"""
    class Type(NoValEnum):
        """Enum of types of EE schemes"""
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
    """Assignment"""
    def __init__(self, pos: Tuple[int, int], lhs: Union[Name, Subscript], rhs: Expression) -> None:
        super().__init__(pos)
        self.lhs: Union[Name, Subscript] = lhs
        self.rhs: Expression = rhs


class For(Statement, HasSymbolTable):
    """For loop"""
    def __init__(self, pos: Tuple[int, int], name: Name, value_from: Number, value_to: Number, body: List[Statement]) \
            -> None:
        super().__init__(pos)
        self.name: Name = name
        self.value_from: Number = value_from
        self.value_to: Number = value_to
        self.body: List[Statement] = body


class ForEach(Statement, HasSymbolTable):
    """For each loop"""
    def __init__(self, pos: Tuple[int, int], name: Name, otype: ObjectType, atom_indices: Optional[Tuple[str, str]],
                 constraints: Constraint, body: List[Statement]) -> None:
        super().__init__(pos)
        self.name: Name = name
        self.type: ObjectType = otype
        self.atom_indices: Optional[Tuple[str, str]] = atom_indices
        self.constraints: Constraint = constraints
        self.body: List[Statement] = body


class BinaryLogicalOp(Constraint):
    """Binary logical operation"""
    class Ops(NoValEnum):
        """Enum of all binary logical operations"""
        AND = 'And'
        OR = 'Or'

    def __init__(self, pos: Tuple[int, int], lhs: Constraint, op: 'BinaryLogicalOp.Ops', rhs: Constraint) -> None:
        super().__init__(pos)
        self.lhs: Constraint = lhs
        self.rhs: Constraint = rhs
        self.op: BinaryLogicalOp.Ops = op

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BinaryLogicalOp):
            return self.lhs == other.lhs and self.rhs == self.rhs and self.op == other.op
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.lhs) ^ hash(self.rhs) ^ hash(self.op)


class UnaryLogicalOp(Constraint):
    """Unary logical operation"""
    class Ops(NoValEnum):
        """Enum of all unarly logical operations"""
        NOT = 'Not'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryLogicalOp.Ops', constraint: Constraint) -> None:
        super().__init__(pos)
        self.op: UnaryLogicalOp.Ops = op
        self.constraint: Constraint = constraint

    def __eq__(self, other: object) -> bool:
        if isinstance(other, UnaryLogicalOp):
            return self.op == other.op and self.constraint == other.constraint
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.op) ^ hash(self.constraint)


class RelOp(Constraint):
    """Compare operation"""
    class Ops(NoValEnum):
        """Enum of all comparison operators"""
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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RelOp):
            return self.lhs == other.lhs and self.rhs == self.rhs and self.op == other.op
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.lhs) ^ hash(self.rhs) ^ hash(self.op)


class Predicate(Constraint):
    """Predicate constraint"""
    def __init__(self, pos: Tuple[int, int], name: str, args: Tuple[Union[Number, Name], ...]) -> None:
        super().__init__(pos)
        self.name: str = name
        self.args: Tuple[Union[Number, Name], ...] = args

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Predicate):
            return self.name == other.name and self.args == other.args
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.name) ^ hash(self.args)


class Parameter(Annotation):
    """Parameter annotation"""
    def __init__(self, pos: Tuple[int, int], name: str, ptype: ParameterType) -> None:
        super().__init__(pos)
        self.name: str = name
        self.type: ParameterType = ptype


class Substitution(Annotation):
    """Substitution annotation"""
    def __init__(self, pos: Tuple[int, int], lhs: Union[Name, Subscript], rhs: Expression,
                 constraints: Optional[Constraint]) -> None:
        super().__init__(pos)
        self.lhs: Union[Name, Subscript] = lhs
        self.rhs: Expression = rhs
        self.constraints: Optional[Constraint] = constraints


class Object(Annotation):
    """Object annotation"""
    def __init__(self, pos: Tuple[int, int], name: str, otype: ObjectType, atom_indices: Optional[Tuple[str, str]],
                 constraints: Optional[Constraint]) -> None:
        super().__init__(pos)
        self.name: str = name
        self.type: ObjectType = otype
        self.atom_indices: Optional[Tuple[str, str]] = atom_indices
        self.constraints: Optional[Constraint] = constraints


class Property(Annotation):
    """Property annotation"""
    def __init__(self, pos: Tuple[int, int], name: str, prop: str) -> None:
        super().__init__(pos)
        self.name: str = name
        self.prop: str = prop


class Constant(Annotation):
    """Constant annotation"""
    def __init__(self, pos: Tuple[int, int], name: str, prop: str, element: str) -> None:
        super().__init__(pos)
        self.name: str = name
        self.prop: str = prop
        self.element: str = element


def is_atom(node: ASTNode) -> bool:
    """Check whether a node represents a simple atomic expression"""
    if isinstance(node, Subscript):
        return True
    if isinstance(node, Name):
        return True
    if isinstance(node, Number):
        return True

    return False
