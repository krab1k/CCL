from typing import List, Union, Tuple, Optional, TypeVar
from enum import Enum


class VarContext(Enum):
    LOAD = 'Load'
    STORE = 'Store'
    ANNOTATION = 'Annotation'


class ObjectType(Enum):
    ATOM = 'Atom'
    BOND = 'Bond'


class ASTNode:
    _fields = ()

    def __init__(self, pos: Tuple[int, int]):
        self._line: int = pos[0]
        self._column: int = pos[1]
        self._parent: Optional['ASTNode'] = None

    def __dir__(self):
        return list(k for k in self.__dict__.keys() if not k.startswith('_'))

    def __repr__(self):
        attr_value = []
        for attr in dir(self):
            value = getattr(self, attr)
            if isinstance(value, str):
                attr_value.append(f'{attr}=\'{value}\'')
            else:
                attr_value.append(f'{attr}={value}')

        string = ', '.join(attr_value)
        return f'{self.__class__.__qualname__}({string})'

    def __iter__(self):
        for attr in self.__dir__():
            yield attr, getattr(self, attr)

    @property
    def parent(self):
        return self._parent


class ASTVisitor:
    def visit(self, node: ASTNode):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        for field, value in node:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):

                        self.visit(item)
            elif isinstance(value, ASTNode):
                value._parent = node
                self.visit(value)


class ParentSetter:
    def visit(self, node: ASTNode):
        for field, value in node:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        item._parent = node
                        self.visit(item)
            elif isinstance(value, ASTNode):
                value._parent = node
                self.visit(value)


class NameGetter:
    @classmethod
    def visit(cls, node: ASTNode):
        names = set()
        if isinstance(node, Name):
            names.add(node.name)
        for field, value in node:
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


class Expression(ASTNode):
    def __init__(self, pos: Tuple[int, int]):
        super().__init__(pos)
        self._result_type: Optional[str] = None

    @property
    def result_type(self):
        return self._result_type

    @result_type.setter
    def result_type(self, value: str):
        self._result_type = value


class Number(Expression):
    def __init__(self, pos: Tuple[int, int], n: Union[int, float]):
        super().__init__(pos)
        self.n: Union[int, float] = n


class Name(Expression):
    def __init__(self, pos: Tuple[int, int], name: str, ctx: VarContext):
        super().__init__(pos)
        self.name: str = name
        self.ctx: VarContext = ctx


class Subscript(Expression):
    def __init__(self, pos: Tuple[int, int], name: Name, indices: List[Name], ctx: VarContext):
        super().__init__(pos)
        self.name: Name = name
        self.indices: List[Name] = indices
        self.ctx: VarContext = ctx


class ParameterAnnotation(Annotation):
    def __init__(self, pos: Tuple[int, int], name: Name, kind: str):
        super().__init__(pos)
        self.name: Name = name
        self.kind: str = kind


class ExprAnnotation(Annotation):
    def __init__(self, pos: Tuple[int, int], lhs: Union[Name, Subscript], rhs: Expression,
                 constraints: Optional[Constraint]):
        super().__init__(pos)
        self.lhs: Union[Name, Subscript] = lhs
        self.rhs: Expression = rhs
        self.constraints: Optional[Constraint] = constraints


class ObjectAnnotation(Annotation):
    def __init__(self, pos: Tuple[int, int], name: Name, kind: str, constraints: Constraint):
        super().__init__(pos)
        self.name: Name = name
        self.kind: str = kind
        self.constraints: Constraint = constraints


class BinaryLogicalOp(Constraint):
    class Ops(Enum):
        AND = 'And'
        OR = 'Or'

    def __init__(self, pos: Tuple[int, int], lhs: Constraint, op: 'BinaryLogicalOp.Ops', rhs: Constraint):
        super().__init__(pos)
        self.lhs: Constraint = lhs
        self.rhs: Constraint = rhs
        self.op: BinaryLogicalOp.Ops = op


class UnaryLogicalOp(Constraint):
    class Ops(Enum):
        NOT = 'Not'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryLogicalOp.Ops', constraint: Constraint):
        super().__init__(pos)
        self.op: UnaryLogicalOp.Ops = op
        self.constraint: Constraint = constraint


class RelOp(Constraint):
    class Ops(Enum):
        LT = '<'
        LE = '<='
        GT = '>'
        GE = '>='
        EQ = '=='
        NEQ = '!='

    def __init__(self, pos: Tuple[int, int], lhs: Expression, op: 'RelOp.Ops', rhs: Expression):
        super().__init__(pos)
        self.lhs: Expression = lhs
        self.rhs: Expression = rhs
        self.op: RelOp.Ops = op


class String(ASTNode):
    def __init__(self, pos: Tuple[int, int], s: str):
        super().__init__(pos)
        self.s: str = s


Arg = TypeVar('Arg', Number, Name, String)


class Predicate(Constraint):
    def __init__(self, pos: Tuple[int, int], name: str, args: List[Arg]):
        super().__init__(pos)
        self.name: str = name
        self.args: List[Arg] = args


class Method(ASTNode):
    def __init__(self, pos, statements: List[Statement], annotations: List[Annotation]):
        super().__init__(pos)
        self.statements: List[Statement] = statements
        self.annotations: List[Annotation] = annotations
        self.symbol_table = None

    def print_ast(self):
        for s in self.statements:
            print(s)

        for a in self.annotations:
            print(a)


class Assign(Statement):
    def __init__(self, pos: Tuple[int, int], lhs: Expression, rhs: Expression):
        super().__init__(pos)
        self.lhs: Expression = lhs
        self.rhs: Expression = rhs


class BinaryOp(Expression):
    class Ops(Enum):
        ADD = '+'
        SUB = '-'
        MUL = '*'
        DIV = '/'
        POW = '^'

    def __init__(self, pos: Tuple[int, int], left: Expression, op: 'BinaryOp.Ops', right: Expression):
        super().__init__(pos)
        self.left: Expression = left
        self.right: Expression = right
        self.op: BinaryOp.Ops = op


class UnaryOp(Expression):
    class Ops(Enum):
        NEG = '-'

    def __init__(self, pos: Tuple[int, int], op: 'UnaryOp.Ops', expr: Expression):
        super().__init__(pos)
        self.op: UnaryOp.Ops = op
        self.expr: Expression = expr


class Sum(Expression):
    def __init__(self, pos: Tuple[int, int], name: Name, expr: Expression):
        super().__init__(pos)
        self.name: Name = name
        self.expr: Expression = expr


class For(Statement):
    def __init__(self, pos: Tuple[int, int], name: Name, value_from: Number, value_to: Number, body: List[Statement]):
        super().__init__(pos)
        self.name: Name = name
        self.value_from: Number = value_from
        self.value_to: Number = value_to
        self.body: List[Statement] = body
        self.symbol_table = None


class ForEach(Statement):
    def __init__(self, pos: Tuple[int, int], name: Name, kind: ObjectType, constraints: Constraint,
                 body: List[Statement]):
        super().__init__(pos)
        self.name: Name = name
        self.kind: ObjectType = kind
        self.constraints: Constraint = constraints
        self.body: List[Statement] = body
        self.symbol_table = None


def is_atom(node: ASTNode):
    if isinstance(node, Subscript):
        return True
    if isinstance(node, Name):
        return True
    if isinstance(node, Number):
        return True

    return False
