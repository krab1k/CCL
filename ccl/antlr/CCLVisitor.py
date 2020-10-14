# Generated from /home/krab1k/Research/CCL/CCL.g4 by ANTLR 4.8
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .CCL import CCL
else:
    from CCL import CCL

# This class defines a complete generic visitor for a parse tree produced by CCL.

class CCLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by CCL#method.
    def visitMethod(self, ctx:CCL.MethodContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#statement.
    def visitStatement(self, ctx:CCL.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#assign.
    def visitAssign(self, ctx:CCL.AssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#for_loop.
    def visitFor_loop(self, ctx:CCL.For_loopContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#for_each.
    def visitFor_each(self, ctx:CCL.For_eachContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#objtype.
    def visitObjtype(self, ctx:CCL.ObjtypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#bond_decomp.
    def visitBond_decomp(self, ctx:CCL.Bond_decompContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#UnaryOp.
    def visitUnaryOp(self, ctx:CCL.UnaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#SumOp.
    def visitSumOp(self, ctx:CCL.SumOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#ParenOp.
    def visitParenOp(self, ctx:CCL.ParenOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#NumberExpr.
    def visitNumberExpr(self, ctx:CCL.NumberExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#RegressionExpr.
    def visitRegressionExpr(self, ctx:CCL.RegressionExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#VarExpr.
    def visitVarExpr(self, ctx:CCL.VarExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#BinOp.
    def visitBinOp(self, ctx:CCL.BinOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#EEExpr.
    def visitEEExpr(self, ctx:CCL.EEExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#FnExpr.
    def visitFnExpr(self, ctx:CCL.FnExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#var.
    def visitVar(self, ctx:CCL.VarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#basename.
    def visitBasename(self, ctx:CCL.BasenameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#subscript.
    def visitSubscript(self, ctx:CCL.SubscriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#ExprAnnotation.
    def visitExprAnnotation(self, ctx:CCL.ExprAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#ParameterAnnotation.
    def visitParameterAnnotation(self, ctx:CCL.ParameterAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#ObjectAnnotation.
    def visitObjectAnnotation(self, ctx:CCL.ObjectAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#ConstantAnnotation.
    def visitConstantAnnotation(self, ctx:CCL.ConstantAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#PropertyAnnotation.
    def visitPropertyAnnotation(self, ctx:CCL.PropertyAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#ParenConstraint.
    def visitParenConstraint(self, ctx:CCL.ParenConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#AndOrConstraint.
    def visitAndOrConstraint(self, ctx:CCL.AndOrConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#PredicateConstraint.
    def visitPredicateConstraint(self, ctx:CCL.PredicateConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#NotConstraint.
    def visitNotConstraint(self, ctx:CCL.NotConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#CompareConstraint.
    def visitCompareConstraint(self, ctx:CCL.CompareConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#arg.
    def visitArg(self, ctx:CCL.ArgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#names.
    def visitNames(self, ctx:CCL.NamesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCL#number.
    def visitNumber(self, ctx:CCL.NumberContext):
        return self.visitChildren(ctx)



del CCL