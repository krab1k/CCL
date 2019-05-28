# Generated from /home/krab1k/Research/CCL/CCL.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .CCLParser import CCLParser
else:
    from CCLParser import CCLParser

# This class defines a complete listener for a parse tree produced by CCLParser.
class CCLListener(ParseTreeListener):

    # Enter a parse tree produced by CCLParser#method.
    def enterMethod(self, ctx:CCLParser.MethodContext):
        pass

    # Exit a parse tree produced by CCLParser#method.
    def exitMethod(self, ctx:CCLParser.MethodContext):
        pass


    # Enter a parse tree produced by CCLParser#statement.
    def enterStatement(self, ctx:CCLParser.StatementContext):
        pass

    # Exit a parse tree produced by CCLParser#statement.
    def exitStatement(self, ctx:CCLParser.StatementContext):
        pass


    # Enter a parse tree produced by CCLParser#assign.
    def enterAssign(self, ctx:CCLParser.AssignContext):
        pass

    # Exit a parse tree produced by CCLParser#assign.
    def exitAssign(self, ctx:CCLParser.AssignContext):
        pass


    # Enter a parse tree produced by CCLParser#for_loop.
    def enterFor_loop(self, ctx:CCLParser.For_loopContext):
        pass

    # Exit a parse tree produced by CCLParser#for_loop.
    def exitFor_loop(self, ctx:CCLParser.For_loopContext):
        pass


    # Enter a parse tree produced by CCLParser#for_each.
    def enterFor_each(self, ctx:CCLParser.For_eachContext):
        pass

    # Exit a parse tree produced by CCLParser#for_each.
    def exitFor_each(self, ctx:CCLParser.For_eachContext):
        pass


    # Enter a parse tree produced by CCLParser#UnaryOp.
    def enterUnaryOp(self, ctx:CCLParser.UnaryOpContext):
        pass

    # Exit a parse tree produced by CCLParser#UnaryOp.
    def exitUnaryOp(self, ctx:CCLParser.UnaryOpContext):
        pass


    # Enter a parse tree produced by CCLParser#SumOp.
    def enterSumOp(self, ctx:CCLParser.SumOpContext):
        pass

    # Exit a parse tree produced by CCLParser#SumOp.
    def exitSumOp(self, ctx:CCLParser.SumOpContext):
        pass


    # Enter a parse tree produced by CCLParser#ParenOp.
    def enterParenOp(self, ctx:CCLParser.ParenOpContext):
        pass

    # Exit a parse tree produced by CCLParser#ParenOp.
    def exitParenOp(self, ctx:CCLParser.ParenOpContext):
        pass


    # Enter a parse tree produced by CCLParser#NumberExpr.
    def enterNumberExpr(self, ctx:CCLParser.NumberExprContext):
        pass

    # Exit a parse tree produced by CCLParser#NumberExpr.
    def exitNumberExpr(self, ctx:CCLParser.NumberExprContext):
        pass


    # Enter a parse tree produced by CCLParser#VarExpr.
    def enterVarExpr(self, ctx:CCLParser.VarExprContext):
        pass

    # Exit a parse tree produced by CCLParser#VarExpr.
    def exitVarExpr(self, ctx:CCLParser.VarExprContext):
        pass


    # Enter a parse tree produced by CCLParser#BinOp.
    def enterBinOp(self, ctx:CCLParser.BinOpContext):
        pass

    # Exit a parse tree produced by CCLParser#BinOp.
    def exitBinOp(self, ctx:CCLParser.BinOpContext):
        pass


    # Enter a parse tree produced by CCLParser#EEExpr.
    def enterEEExpr(self, ctx:CCLParser.EEExprContext):
        pass

    # Exit a parse tree produced by CCLParser#EEExpr.
    def exitEEExpr(self, ctx:CCLParser.EEExprContext):
        pass


    # Enter a parse tree produced by CCLParser#FnExpr.
    def enterFnExpr(self, ctx:CCLParser.FnExprContext):
        pass

    # Exit a parse tree produced by CCLParser#FnExpr.
    def exitFnExpr(self, ctx:CCLParser.FnExprContext):
        pass


    # Enter a parse tree produced by CCLParser#var.
    def enterVar(self, ctx:CCLParser.VarContext):
        pass

    # Exit a parse tree produced by CCLParser#var.
    def exitVar(self, ctx:CCLParser.VarContext):
        pass


    # Enter a parse tree produced by CCLParser#basename.
    def enterBasename(self, ctx:CCLParser.BasenameContext):
        pass

    # Exit a parse tree produced by CCLParser#basename.
    def exitBasename(self, ctx:CCLParser.BasenameContext):
        pass


    # Enter a parse tree produced by CCLParser#subscript.
    def enterSubscript(self, ctx:CCLParser.SubscriptContext):
        pass

    # Exit a parse tree produced by CCLParser#subscript.
    def exitSubscript(self, ctx:CCLParser.SubscriptContext):
        pass


    # Enter a parse tree produced by CCLParser#ExprAnnotation.
    def enterExprAnnotation(self, ctx:CCLParser.ExprAnnotationContext):
        pass

    # Exit a parse tree produced by CCLParser#ExprAnnotation.
    def exitExprAnnotation(self, ctx:CCLParser.ExprAnnotationContext):
        pass


    # Enter a parse tree produced by CCLParser#ParameterAnnotation.
    def enterParameterAnnotation(self, ctx:CCLParser.ParameterAnnotationContext):
        pass

    # Exit a parse tree produced by CCLParser#ParameterAnnotation.
    def exitParameterAnnotation(self, ctx:CCLParser.ParameterAnnotationContext):
        pass


    # Enter a parse tree produced by CCLParser#ObjectAnnotation.
    def enterObjectAnnotation(self, ctx:CCLParser.ObjectAnnotationContext):
        pass

    # Exit a parse tree produced by CCLParser#ObjectAnnotation.
    def exitObjectAnnotation(self, ctx:CCLParser.ObjectAnnotationContext):
        pass


    # Enter a parse tree produced by CCLParser#ConstantAnnotation.
    def enterConstantAnnotation(self, ctx:CCLParser.ConstantAnnotationContext):
        pass

    # Exit a parse tree produced by CCLParser#ConstantAnnotation.
    def exitConstantAnnotation(self, ctx:CCLParser.ConstantAnnotationContext):
        pass


    # Enter a parse tree produced by CCLParser#PropertyAnnotation.
    def enterPropertyAnnotation(self, ctx:CCLParser.PropertyAnnotationContext):
        pass

    # Exit a parse tree produced by CCLParser#PropertyAnnotation.
    def exitPropertyAnnotation(self, ctx:CCLParser.PropertyAnnotationContext):
        pass


    # Enter a parse tree produced by CCLParser#ParenConstraint.
    def enterParenConstraint(self, ctx:CCLParser.ParenConstraintContext):
        pass

    # Exit a parse tree produced by CCLParser#ParenConstraint.
    def exitParenConstraint(self, ctx:CCLParser.ParenConstraintContext):
        pass


    # Enter a parse tree produced by CCLParser#AndOrConstraint.
    def enterAndOrConstraint(self, ctx:CCLParser.AndOrConstraintContext):
        pass

    # Exit a parse tree produced by CCLParser#AndOrConstraint.
    def exitAndOrConstraint(self, ctx:CCLParser.AndOrConstraintContext):
        pass


    # Enter a parse tree produced by CCLParser#PredicateConstraint.
    def enterPredicateConstraint(self, ctx:CCLParser.PredicateConstraintContext):
        pass

    # Exit a parse tree produced by CCLParser#PredicateConstraint.
    def exitPredicateConstraint(self, ctx:CCLParser.PredicateConstraintContext):
        pass


    # Enter a parse tree produced by CCLParser#NotConstraint.
    def enterNotConstraint(self, ctx:CCLParser.NotConstraintContext):
        pass

    # Exit a parse tree produced by CCLParser#NotConstraint.
    def exitNotConstraint(self, ctx:CCLParser.NotConstraintContext):
        pass


    # Enter a parse tree produced by CCLParser#CompareConstraint.
    def enterCompareConstraint(self, ctx:CCLParser.CompareConstraintContext):
        pass

    # Exit a parse tree produced by CCLParser#CompareConstraint.
    def exitCompareConstraint(self, ctx:CCLParser.CompareConstraintContext):
        pass


    # Enter a parse tree produced by CCLParser#arg.
    def enterArg(self, ctx:CCLParser.ArgContext):
        pass

    # Exit a parse tree produced by CCLParser#arg.
    def exitArg(self, ctx:CCLParser.ArgContext):
        pass


    # Enter a parse tree produced by CCLParser#number.
    def enterNumber(self, ctx:CCLParser.NumberContext):
        pass

    # Exit a parse tree produced by CCLParser#number.
    def exitNumber(self, ctx:CCLParser.NumberContext):
        pass


