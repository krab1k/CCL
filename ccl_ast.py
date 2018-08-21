# from ast import iter_child_nodes


class ASTNode:
    _fields = ()

    def __init__(self, pos, *args):
        self.lineno = pos[0]
        self.colno = pos[1]

        for field, value in zip(self._fields, args):
            setattr(self, field, value)

    def __repr__(self):
        field_value = []
        for field in self._fields:
            value = getattr(self, field)
            if isinstance(value, str):
                field_value.append(f'{field}=\'{value}\'')
            else:
                field_value.append(f'{field}={value}')

        string = ', '.join(field_value)
        return f'{self.__class__.__qualname__}({string})'


class Statement(ASTNode):
    pass


class Assign(Statement):
    _fields = ('lhs', 'rhs')


class Expression(ASTNode):
    pass


class BinaryOp(Expression):
    OPS = {'+': 'Add', '-': 'Sub', '*': 'Mul', '/': 'Div', '^': 'Pow'}
    _fields = ('left', 'op', 'right')


class UnaryOp(Expression):
    OPS = {'-': 'Neg'}
    _fields = ('op', 'expr')


class Number(Expression):
    _fields = ('n',)


class Name(Expression):
    _fields = ('id',)


class String(ASTNode):
    _fields = ('s',)


class Subscript(Expression):
    _fields = ('id', 'indices')


class Sum(Expression):
    _fields = ('id', 'expr')


class For(Statement):
    _fields = ('id', 'value_from', 'value_to', 'body')


class ForEach(Statement):
    _fields = ('id', 'type', 'constraints', 'body')


class Annotation(ASTNode):
    pass


class ParameterAnnotation(Annotation):
    _fields = ('id', 'type')


class ExprAnnotation(Annotation):
    _fields = ('lhs', 'rhs', 'constraints')


class ObjectAnnotation(Annotation):
    _fields = ('id', 'type', 'constraints')


class Constraint(ASTNode):
    pass


class AndOrConstraint(Constraint):
    OPS = {'and': 'And', 'or': 'Or'}
    _fields = ('lhs', 'op', 'rhs')


class UnaryConstraint(Constraint):
    OPS = {'not': 'Not'}
    _fields = ('op', 'restriction')


class CompareConstraint(Constraint):
    OPS = {'<': 'Lt', '>': 'Gt', '<=': 'Le', '>=': 'Gt', '==': 'Eq', '!=': 'Neq'}
    _fields = ('lhs', 'op', 'rhs')


class PredicateConstraint(Constraint):
    _fields = ('name', 'args')
