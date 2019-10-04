"""Derive complexity of methods in CCL"""

import sympy

from ccl import ast, symboltable


class Complexity(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable) -> None:
        super().__init__()
        self.symbol_table: symboltable.SymbolTable = symbol_table

    def visit_Method(self, node: ast.Method) -> str:
        raw_complexity = ' + '.join(str(self.visit(statement)) for statement in node.statements)
        ns = {'N': sympy.Symbol('N'), 'M': sympy.Symbol('M')}
        print(raw_complexity)
        res = sympy.sympify(f'O({raw_complexity}, (M, oo), (N, oo))', locals=ns)
        return f'O({res.expr})'

    def visit_ForEach(self, node: ast.ForEach) -> str:
        if node.type == ast.ObjectType.ATOM:
            mult = 'N'
        else:
            mult = 'M'

        body = ' + '.join(str(self.visit(statement)) for statement in node.body)
        return f'{mult} * ({body})'

    def visit_Assign(self, node: ast.Assign) -> str:
        return self.visit(node.rhs)

    def visit_Number(self, node: ast.Number) -> str:
        return '1'

    def visit_Subscript(self, node: ast.Subscript) -> str:
        return '1'

    def visit_For(self, node: ast.For) -> str:
        body = ' + '.join(self.visit(statement) for statement in node.body)
        return f'{node.value_to.val - node.value_from.val} * ({body})'

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        complexity_parts = []
        if not ast.is_atom(node.left):
            complexity_parts.append(str(self.visit(node.left)))

        if not ast.is_atom(node.right):
            complexity_parts.append(str(self.visit(node.right)))

        if isinstance(node.left.result_type, ast.NumericType) and isinstance(node.right.result_type, ast.NumericType):
            complexity_parts.append('1')

        return ' + '.join(complexity_parts)

    def visit_Sum(self, node: ast.Sum) -> str:
        s = self.symbol_table.resolve(node.name.val)
        if s.symbol_type == ast.ObjectType.ATOM:
            mult = 'N'
        else:
            mult = 'M'

        body = self.visit(node.expr)
        # TODO handle constraints

        return f'{mult} * ({body})'

    def visit_EE(self, node: ast.EE) -> str:
        complexity_parts = ['N ** 3']
        for part in (node.rhs, node.diag, node.off):
            if not ast.is_atom(part):
                complexity_parts.append(str(self.visit(part)))

        return ' + '.join(complexity_parts)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        complexity_parts = []
        if isinstance(node.expr.result_type, ast.NumericType):
            complexity_parts = ['1']
        elif isinstance(node.expr.result_type, ast.ArrayType):
            tmp = []
            for idx in node.expr.result_type.indices:
                if idx == ast.ObjectType.ATOM:
                    tmp.append('N')
                else:
                    tmp.append('M')
            complexity_parts.append(' * '.join(tmp))
        else:
            raise RuntimeError('We should not get here')
        if not ast.is_atom(node.expr):
            complexity_parts.append(str(self.visit(node.expr)))

        return ' + '.join(complexity_parts)

    def visit_Function(self, node: ast.Function) -> str:
        if node.name == 'inv':
            complexity_parts = ['N ** 3']
        else:
            complexity_parts = ['1']

        if not ast.is_atom(node.arg):
            complexity_parts.append(str(self.visit(node.arg)))

        return ' + '.join(complexity_parts)
