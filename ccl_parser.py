import antlr4
from antlr4.Token import CommonToken
from antlr.CCLVisitor import CCLVisitor
from antlr.CCLParser import CCLParser

from ccl_ast import *
from ccl_symboltable import SymbolTable


class Parser(CCLVisitor):
    def __init__(self):
        super().__init__()
        self.annotations = []
        self.statements = []
        self.symtable = SymbolTable()

    @staticmethod
    def get_pos(ctx):
        if isinstance(ctx, antlr4.ParserRuleContext):
            return ctx.start.line, ctx.start.column
        elif isinstance(ctx, CommonToken):
            return ctx.line, ctx.column
        else:
            raise RuntimeError(f'Unknown context {ctx}')

    def visitMethod(self, ctx: CCLParser.MethodContext):
        for annotation in ctx.annotations:
            self.annotations.append(self.visit(annotation))

        for statement in ctx.body:
            self.statements.append(self.visitStatement(statement))
        pass

    def visitParameterAnnotation(self, ctx: CCLParser.ParameterAnnotationContext):
        name = Name(self.get_pos(ctx.name), ctx.name.text)
        ptype = ctx.ptype.text.capitalize()
        return ParameterAnnotation(self.get_pos(ctx), name, ptype)

    def visitABAnnotation(self, ctx: CCLParser.ABAnnotationContext):
        name = Name(self.get_pos(ctx.name), ctx.name.text)
        abtype = ctx.abtype.text.capitalize()
        constraint = self.visit(ctx.constraint())
        return ObjectAnnotation(self.get_pos(ctx), name, abtype, constraint)

    def visitAndOrConstraint(self, ctx: CCLParser.AndOrConstraintContext):
        lhs = self.visit(ctx.left)
        rhs = self.visit(ctx.right)
        op = AndOrConstraint.OPS[ctx.op.text]
        return AndOrConstraint(self.get_pos(ctx), lhs, op, rhs)

    def visitNotConstraint(self, ctx: CCLParser.NotConstraintContext):
        constraint = self.visit(ctx.constraint())
        return UnaryConstraint(self.get_pos(ctx), UnaryConstraint.OPS['not'], constraint)

    def visitParenConstraint(self, ctx: CCLParser.ParenConstraintContext):
        return self.visit(ctx.constraint())

    def visitCompareConstraint(self, ctx: CCLParser.CompareConstraintContext):
        lhs = self.visit(ctx.left)
        rhs = self.visit(ctx.right)
        op = CompareConstraint.OPS[ctx.op.text]
        return CompareConstraint(self.get_pos(ctx), lhs, op, rhs)

    def visitPredicateConstraint(self, ctx: CCLParser.PredicateConstraintContext):
        name = ctx.pred.text
        args = [self.visit(arg) for arg in ctx.args]
        return PredicateConstraint(self.get_pos(ctx), name, args)

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
        expr = self.visit(ctx.rhs)
        return Assign(self.get_pos(ctx), var, expr)

    def visitBinOp(self, ctx: CCLParser.BinOpContext):
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        op = BinaryOp.OPS[ctx.op.text]
        return BinaryOp(self.get_pos(ctx), left, op, right)

    def visitParenOp(self, ctx: CCLParser.ParenOpContext):
        return self.visit(ctx.expr())

    def visitNumber(self, ctx: CCLParser.NumberContext):
        try:
            n = int(ctx.getText())
        except ValueError:
            n = float(ctx.getText())
        return Number(self.get_pos(ctx), n)

    def visitBasename(self, ctx: CCLParser.BasenameContext):
        return Name(self.get_pos(ctx), ctx.name.text)

    def visitSubscript(self, ctx: CCLParser.SubscriptContext):
        name = ctx.name.text
        indices = []
        for idx in ctx.indices:
            indices.append(Name(self.get_pos(idx), idx.text))
        return Subscript(self.get_pos(ctx), name, indices)

    def visitSumOp(self, ctx: CCLParser.SumOpContext):
        name = ctx.identifier.text
        expr = self.visit(ctx.expr())
        return Sum(self.get_pos(ctx), name, expr)

    def visitUnaryOp(self, ctx: CCLParser.UnaryOpContext):
        expr = self.visit(ctx.expr())
        if ctx.op.text == '+':
            return expr
        else:
            return UnaryOp(self.get_pos(ctx), UnaryOp.OPS['-'], expr)

    def visitFor_loop(self, ctx: CCLParser.For_loopContext):
        name = Name(self.get_pos(ctx.identifier), ctx.identifier.text)
        value_from = Number(self.get_pos(ctx.value_from), int(ctx.value_from.text))
        value_to = Number(self.get_pos(ctx.value_to), int(ctx.value_to.text))
        body = []
        for statement in ctx.body:
            body.append(self.visit(statement))
        return For(self.get_pos(ctx), name, value_from, value_to, body)

    def visitFor_each(self, ctx: CCLParser.For_eachContext):
        name = Name(self.get_pos(ctx.identifier), ctx.identifier.text)
        abtype = ctx.abtype.text.capitalize()
        if ctx.constraint() is not None:
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None
        body = []
        for statement in ctx.body:
            body.append(self.visit(statement))

        return ForEach(self.get_pos(ctx), name, abtype, constraint, body)




