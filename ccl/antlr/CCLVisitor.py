# Generated from /home/krab1k/Research/CCL/CCL.g4 by ANTLR 4.7
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .CCLParser import CCLParser
else:
    from CCLParser import CCLParser

# This class defines a complete generic visitor for a parse tree produced by CCLParser.

class CCLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by CCLParser#method.
    def visitMethod(self, ctx:CCLParser.MethodContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#statement.
    def visitStatement(self, ctx:CCLParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#assign.
    def visitAssign(self, ctx:CCLParser.AssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#for_loop.
    def visitFor_loop(self, ctx:CCLParser.For_loopContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#for_each.
    def visitFor_each(self, ctx:CCLParser.For_eachContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#UnaryOp.
    def visitUnaryOp(self, ctx:CCLParser.UnaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#SumOp.
    def visitSumOp(self, ctx:CCLParser.SumOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#ParenOp.
    def visitParenOp(self, ctx:CCLParser.ParenOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#NumberExpr.
    def visitNumberExpr(self, ctx:CCLParser.NumberExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#VarExpr.
    def visitVarExpr(self, ctx:CCLParser.VarExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#BinOp.
    def visitBinOp(self, ctx:CCLParser.BinOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#var.
    def visitVar(self, ctx:CCLParser.VarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#basename.
    def visitBasename(self, ctx:CCLParser.BasenameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#subscript.
    def visitSubscript(self, ctx:CCLParser.SubscriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#ExprAnnotation.
    def visitExprAnnotation(self, ctx:CCLParser.ExprAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#ParameterAnnotation.
    def visitParameterAnnotation(self, ctx:CCLParser.ParameterAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#ABAnnotation.
    def visitABAnnotation(self, ctx:CCLParser.ABAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#PropertyAnnotation.
    def visitPropertyAnnotation(self, ctx:CCLParser.PropertyAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#ParenConstraint.
    def visitParenConstraint(self, ctx:CCLParser.ParenConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#AndOrConstraint.
    def visitAndOrConstraint(self, ctx:CCLParser.AndOrConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#PredicateConstraint.
    def visitPredicateConstraint(self, ctx:CCLParser.PredicateConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#NotConstraint.
    def visitNotConstraint(self, ctx:CCLParser.NotConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#CompareConstraint.
    def visitCompareConstraint(self, ctx:CCLParser.CompareConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#arg.
    def visitArg(self, ctx:CCLParser.ArgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#number.
    def visitNumber(self, ctx:CCLParser.NumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CCLParser#string.
    def visitString(self, ctx:CCLParser.StringContext):
        return self.visitChildren(ctx)



del CCLParser