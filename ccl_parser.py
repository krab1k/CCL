import antlr4
from antlr4.error.ErrorListener import ErrorListener
from antlr4.Token import CommonToken
from antlr.CCLVisitor import CCLVisitor
from antlr.CCLParser import CCLParser

from ccl_ast import *
from ccl_errors import CCLSyntaxError


# noinspection PyPep8Naming
class CCLErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        node = ASTNode((line, column))
        raise CCLSyntaxError(node, msg)


class Parser(CCLVisitor):
    def __init__(self):
        super().__init__()
        self._name_handling = VarContext.STORE

    @staticmethod
    def get_pos(ctx):
        if isinstance(ctx, antlr4.ParserRuleContext):
            return ctx.start.line, ctx.start.column
        elif isinstance(ctx, CommonToken):
            return ctx.line, ctx.column
        else:
            raise RuntimeError(f'Unknown context {ctx}')

    def visitMethod(self, ctx: CCLParser.MethodContext):
        annotations = []
        for annotation in ctx.annotations:
            annotations.append(self.visit(annotation))

        statements = []
        for statement in ctx.body:
            statements.append(self.visitStatement(statement))

        return Method(self.get_pos(ctx), statements, annotations)

    def visitParameterAnnotation(self, ctx: CCLParser.ParameterAnnotationContext):
        name = Name(self.get_pos(ctx.name), ctx.name.text, VarContext.ANNOTATION)
        ptype = ctx.ptype.text.capitalize()
        return ParameterAnnotation(self.get_pos(ctx), name, ptype)

    def visitABAnnotation(self, ctx: CCLParser.ABAnnotationContext):
        name = Name(self.get_pos(ctx.name), ctx.name.text, VarContext.ANNOTATION)
        object_type = ctx.abtype.text.capitalize()
        if ctx.constraint():
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None
        return ObjectAnnotation(self.get_pos(ctx), name, object_type, constraint)

    def visitAndOrConstraint(self, ctx: CCLParser.AndOrConstraintContext):
        lhs = self.visit(ctx.left)
        rhs = self.visit(ctx.right)
        op = BinaryLogicalOp.Ops(ctx.op.text.capitalize())
        return BinaryLogicalOp(self.get_pos(ctx), lhs, op, rhs)

    def visitNotConstraint(self, ctx: CCLParser.NotConstraintContext):
        constraint = self.visit(ctx.constraint())
        return UnaryLogicalOp(self.get_pos(ctx), UnaryLogicalOp.Ops.NOT, constraint)

    def visitParenConstraint(self, ctx: CCLParser.ParenConstraintContext):
        return self.visit(ctx.constraint())

    def visitCompareConstraint(self, ctx: CCLParser.CompareConstraintContext):
        lhs = self.visit(ctx.left)
        rhs = self.visit(ctx.right)
        op = RelOp.Ops(ctx.op.text)
        return RelOp(self.get_pos(ctx), lhs, op, rhs)

    def visitPredicateConstraint(self, ctx: CCLParser.PredicateConstraintContext):
        name = ctx.pred.text
        args = [self.visit(arg) for arg in ctx.args]
        return Predicate(self.get_pos(ctx), name, args)

    def visitString(self, ctx: CCLParser.StringContext):
        return String(self.get_pos(ctx), ctx.getText().strip('"'))

    def visitExprAnnotation(self, ctx: CCLParser.ExprAnnotationContext):
        lhs = self.visit(ctx.var())
        rhs = self.visit(ctx.expr())
        if ctx.constraint() is not None:
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None
        return ExprAnnotation(self.get_pos(ctx), lhs, rhs, constraint)

    def visitAssign(self, ctx: CCLParser.AssignContext):
        var = self.visit(ctx.lhs)
        self._name_handling = VarContext.LOAD
        expr = self.visit(ctx.rhs)
        self._name_handling = VarContext.STORE
        return Assign(self.get_pos(ctx), var, expr)

    def visitBinOp(self, ctx: CCLParser.BinOpContext):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        op = BinaryOp.Ops(ctx.op.text)
        return BinaryOp(self.get_pos(ctx.op), left, op, right)

    def visitParenOp(self, ctx: CCLParser.ParenOpContext):
        return self.visit(ctx.expr())

    def visitNumber(self, ctx: CCLParser.NumberContext):
        try:
            n = int(ctx.getText())
        except ValueError:
            n = float(ctx.getText())
        return Number(self.get_pos(ctx), n)

    def visitBasename(self, ctx: CCLParser.BasenameContext):
        return Name(self.get_pos(ctx), ctx.name.text, self._name_handling)

    def visitSubscript(self, ctx: CCLParser.SubscriptContext):
        name = Name(self.get_pos(ctx.name), ctx.name.text, self._name_handling)
        indices = []
        for idx in ctx.indices:
            indices.append(Name(self.get_pos(idx), idx.text, VarContext.LOAD))
        return Subscript(self.get_pos(ctx), name, indices, self._name_handling)

    def visitSumOp(self, ctx: CCLParser.SumOpContext):
        name = Name(self.get_pos(ctx.identifier), ctx.identifier.text, VarContext.LOAD)
        expr = self.visit(ctx.expr())
        return Sum(self.get_pos(ctx), name, expr)

    def visitUnaryOp(self, ctx: CCLParser.UnaryOpContext):
        expr = self.visit(ctx.expr())
        if ctx.op.text == '+':
            return expr
        else:
            return UnaryOp(self.get_pos(ctx), UnaryOp.Ops.NEG, expr)

    def visitFor_loop(self, ctx: CCLParser.For_loopContext):
        name = Name(self.get_pos(ctx.identifier), ctx.identifier.text, VarContext.STORE)
        value_from = self.visit(ctx.value_from)
        value_to = self.visit(ctx.value_to)
        body = []
        for statement in ctx.body:
            body.append(self.visit(statement))
        return For(self.get_pos(ctx), name, value_from, value_to, body)

    def visitFor_each(self, ctx: CCLParser.For_eachContext):
        name = Name(self.get_pos(ctx.identifier), ctx.identifier.text, VarContext.STORE)
        object_type = ctx.abtype.text.capitalize()
        if ctx.constraint() is not None:
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None
        body = []
        for statement in ctx.body:
            body.append(self.visit(statement))

        return ForEach(self.get_pos(ctx), name, object_type, constraint, body)




