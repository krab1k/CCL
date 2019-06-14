"""ANTLR-based parser converting source token stream to the CCL's abstract syntax tree"""

from typing import Union, Tuple
import antlr4
from antlr4.error.ErrorListener import ErrorListener
from antlr4.Token import CommonToken
from ccl.antlr.CCLVisitor import CCLVisitor
from ccl.antlr import CCL as CCL_Parser


import ccl.ast as ast
from ccl.errors import CCLSyntaxError


__all__ = ['CCLErrorListener', 'Parser']


# noinspection PyPep8Naming
class CCLErrorListener(ErrorListener):
    def syntaxError(self, recognizer: CCL_Parser.CCL, offendingSymbol: CommonToken, line: int, column: int,
                    msg: str, e: Exception) -> None:
        node = ast.ASTNode((line, column))
        raise CCLSyntaxError(node, msg)


class Parser(CCLVisitor):
    def __init__(self) -> None:
        super().__init__()
        self._name_handling: ast.VarContext = ast.VarContext.STORE

    @staticmethod
    def get_pos(ctx: Union[antlr4.ParserRuleContext, CommonToken]) -> Tuple[int, int]:
        if isinstance(ctx, antlr4.ParserRuleContext):
            return ctx.start.line, ctx.start.column
        if isinstance(ctx, CommonToken):
            return ctx.line, ctx.column

        raise RuntimeError(f'Unknown context {ctx}')

    def visitMethod(self, ctx: CCL_Parser.CCL.MethodContext) -> ast.Method:
        name = ctx.method_name.text

        annotations = []
        for annotation in ctx.annotations:
            annotations.append(self.visit(annotation))

        statements = []
        for statement in ctx.body:
            statements.append(self.visitStatement(statement))

        method = ast.Method(self.get_pos(ctx), name, statements, annotations)
        ast.ParentSetter().visit(method)
        return method

    def visitParameterAnnotation(self, ctx: CCL_Parser.CCL.ParameterAnnotationContext) -> ast.Parameter:
        ptype = ast.ParameterType(ctx.ptype.text.capitalize() + ' Parameter')
        return ast.Parameter(self.get_pos(ctx), ctx.name.text, ptype)

    def visitObjtype(self, ctx: CCL_Parser.CCL.ObjtypeContext) -> str:
        return ctx.getText()

    def visitObjectAnnotation(self, ctx: CCL_Parser.CCL.ObjectAnnotationContext) -> ast.Object:
        object_type = ast.ObjectType(self.visit(ctx.abtype).capitalize())
        if ctx.constraint():
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None

        if ctx.bond_decomp():
            if object_type != ast.ObjectType.BOND:
                raise CCLSyntaxError(ast.ASTNode(self.get_pos(ctx.abtype)), f'Only bonds can be decomposed.')
            atom_indices = tuple(i.text for i in ctx.bond_decomp().indices)
        else:
            atom_indices = None
        return ast.Object(self.get_pos(ctx), ctx.name.text, object_type, atom_indices, constraint)

    def visitAndOrConstraint(self, ctx: CCL_Parser.CCL.AndOrConstraintContext) -> ast.BinaryLogicalOp:
        lhs = self.visit(ctx.left)
        rhs = self.visit(ctx.right)
        op = ast.BinaryLogicalOp.Ops(ctx.op.text.capitalize())
        return ast.BinaryLogicalOp(self.get_pos(ctx), lhs, op, rhs)

    def visitNotConstraint(self, ctx: CCL_Parser.CCL.NotConstraintContext) -> ast.UnaryLogicalOp:
        constraint = self.visit(ctx.constraint())
        return ast.UnaryLogicalOp(self.get_pos(ctx), ast.UnaryLogicalOp.Ops.NOT, constraint)

    def visitParenConstraint(self, ctx: CCL_Parser.CCL.ParenConstraintContext) -> ast.Constraint:
        return self.visit(ctx.constraint())

    def visitCompareConstraint(self, ctx: CCL_Parser.CCL.CompareConstraintContext) -> ast.RelOp:
        lhs = self.visit(ctx.left)
        rhs = self.visit(ctx.right)
        op = ast.RelOp.Ops(ctx.op.text)
        return ast.RelOp(self.get_pos(ctx), lhs, op, rhs)

    def visitPredicateConstraint(self, ctx: CCL_Parser.CCL.PredicateConstraintContext) -> ast.Predicate:
        name = ctx.pred.text
        args = [self.visit(arg) for arg in ctx.args]
        return ast.Predicate(self.get_pos(ctx), name, args)

    def visitExprAnnotation(self, ctx: CCL_Parser.CCL.ExprAnnotationContext) -> ast.Substitution:
        self._name_handling = ast.VarContext.LOAD
        lhs = self.visit(ctx.var())
        rhs = self.visit(ctx.expr())
        if ctx.constraint() is not None:
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None

        self._name_handling = ast.VarContext.STORE
        return ast.Substitution(self.get_pos(ctx), lhs, rhs, constraint)

    def visitAssign(self, ctx: CCL_Parser.CCL.AssignContext) -> ast.Assign:
        var = self.visit(ctx.lhs)
        self._name_handling = ast.VarContext.LOAD
        expr = self.visit(ctx.rhs)
        self._name_handling = ast.VarContext.STORE
        return ast.Assign(self.get_pos(ctx), var, expr)

    def visitBinOp(self, ctx: CCL_Parser.CCL.BinOpContext) -> ast.BinaryOp:
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)
        op = ast.BinaryOp.Ops(ctx.op.text)
        return ast.BinaryOp(self.get_pos(ctx.op), left, op, right)

    def visitParenOp(self, ctx: CCL_Parser.CCL.ParenOpContext) -> ast.Expression:
        return self.visit(ctx.expr())

    def visitNumber(self, ctx: CCL_Parser.CCL.NumberContext) -> ast.Number:
        try:
            val = int(ctx.getText())
            ntype = ast.NumericType.INT
        except ValueError:
            val = float(ctx.getText())
            ntype = ast.NumericType.FLOAT
        return ast.Number(self.get_pos(ctx), val, ntype)

    def visitBasename(self, ctx: CCL_Parser.CCL.BasenameContext) -> ast.Name:
        return ast.Name(self.get_pos(ctx), ctx.name.text, self._name_handling)

    def visitSubscript(self, ctx: CCL_Parser.CCL.SubscriptContext) -> ast.Subscript:
        name = ast.Name(self.get_pos(ctx.name), ctx.name.text, self._name_handling)
        indices = []
        for idx in ctx.indices:
            indices.append(ast.Name(self.get_pos(idx), idx.text, ast.VarContext.LOAD))
        return ast.Subscript(self.get_pos(ctx), name, indices, self._name_handling)

    def visitSumOp(self, ctx: CCL_Parser.CCL.SumOpContext) -> ast.Sum:
        name = ast.Name(self.get_pos(ctx.identifier), ctx.identifier.text, ast.VarContext.LOAD)
        expr = self.visit(ctx.expr())
        return ast.Sum(self.get_pos(ctx), name, expr)

    def visitUnaryOp(self, ctx: CCL_Parser.CCL.UnaryOpContext) -> ast.UnaryOp:
        expr = self.visit(ctx.expr())
        if ctx.op.text == '+':
            return expr

        return ast.UnaryOp(self.get_pos(ctx), ast.UnaryOp.Ops.NEG, expr)

    def visitFor_loop(self, ctx: CCL_Parser.CCL.For_loopContext) -> ast.For:
        name = ast.Name(self.get_pos(ctx.identifier), ctx.identifier.text, ast.VarContext.STORE)
        value_from = self.visit(ctx.value_from)
        value_to = self.visit(ctx.value_to)
        body = []
        for statement in ctx.body:
            body.append(self.visit(statement))
        return ast.For(self.get_pos(ctx), name, value_from, value_to, body)

    def visitFor_each(self, ctx: CCL_Parser.CCL.For_eachContext) -> ast.ForEach:
        name = ast.Name(self.get_pos(ctx.identifier), ctx.identifier.text, ast.VarContext.STORE)
        object_type = ast.ObjectType(self.visit(ctx.abtype).capitalize())
        if ctx.constraint() is not None:
            constraint = self.visit(ctx.constraint())
        else:
            constraint = None

        if ctx.bond_decomp():
            if object_type != ast.ObjectType.BOND:
                raise CCLSyntaxError(ast.ASTNode(self.get_pos(ctx.abtype)), f'Only bonds can be decomposed.')
            atom_indices = tuple(i.text for i in ctx.bond_decomp().indices)
        else:
            atom_indices = None

        body = []
        for statement in ctx.body:
            body.append(self.visit(statement))

        return ast.ForEach(self.get_pos(ctx), name, object_type, atom_indices, constraint, body)

    def visitPropertyAnnotation(self, ctx: CCL_Parser.CCL.PropertyAnnotationContext) -> ast.Property:
        names = ' '.join(name.getText() for name in ctx.ptype)
        return ast.Property(self.get_pos(ctx), ctx.name.text, names)

    def visitConstantAnnotation(self, ctx: CCL_Parser.CCL.ConstantAnnotationContext) -> ast.Constant:
        names = ' '.join(name.getText() for name in ctx.ptype)
        return ast.Constant(self.get_pos(ctx), ctx.name.text, names, ctx.element.text)

    def visitFnExpr(self, ctx: CCL_Parser.CCL.FnExprContext) -> ast.Function:
        arg = self.visit(ctx.fn_arg)
        return ast.Function(self.get_pos(ctx), ctx.fn.text, arg)

    def visitEEExpr(self, ctx: CCL_Parser.CCL.EEExprContext) -> ast.EE:
        diag = self.visit(ctx.diag)
        off = self.visit(ctx.off)
        rhs = self.visit(ctx.rhs)
        if ctx.ee_type is not None:
            ee_type = ast.EE.Type(ctx.ee_type.text.capitalize())
            radius = self.visit(ctx.radius)
        else:
            ee_type = ast.EE.Type.FULL
            radius = None

        return ast.EE(self.get_pos(ctx), ctx.idx_row.text, ctx.idx_col.text, diag, off, rhs, ee_type, radius)
