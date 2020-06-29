"""Derive complexity of methods in CCL"""

import sympy

from ccl import ast, symboltable


OBJECT_COMPLEXITY = {ast.ObjectType.ATOM: 'N', ast.ObjectType.BOND: 'M'}


class Complexity(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable, **kwargs: bool) -> None:
        super().__init__()
        self.symbol_table: symboltable.SymbolTable = symbol_table
        self._asymptotic = kwargs['asymptotic'] if 'asymptotic' in kwargs else False

    def visit_Method(self, node: ast.Method) -> str:
        init_complexity = []
        for s in self.symbol_table.symbols.values():
            if isinstance(s.symbol_type, ast.ArrayType):
                init_complexity.append(' * '.join(OBJECT_COMPLEXITY[idx] for idx in s.symbol_type.indices))

        statements_complexity = [self.visit(statement) for statement in node.statements]

        raw_complexity = ' + '.join(init_complexity + statements_complexity)
        ns = {'N': sympy.Symbol('N'), 'M': sympy.Symbol('M')}
        if self._asymptotic:
            res = sympy.sympify(f'O({raw_complexity}, (M, oo), (N, oo))', locals=ns)
            return f'O({res.expr})'
        else:
            return f'{sympy.sympify(raw_complexity, locals=ns).simplify()}'

    def visit_ForEach(self, node: ast.ForEach) -> str:
        mult = OBJECT_COMPLEXITY[node.type]
        body = ' + '.join(str(self.visit(statement)) for statement in node.body)

        s = node.symbol_table.resolve(node.name.val)
        assert isinstance(s, symboltable.ObjectSymbol)
        constraints = self.visit(s.constraints) if s.constraints else 0

        return f'{mult} * ({body} + {constraints})'

    def visit_Assign(self, node: ast.Assign) -> str:
        assign = '1'
        if isinstance(node.lhs, ast.Name):
            s = self.symbol_table.resolve(node.lhs.val)
            if isinstance(s.symbol_type, ast.ArrayType):
                assign = ' * '.join(OBJECT_COMPLEXITY[idx] for idx in s.symbol_type.indices)

        return f'{assign} + {self.visit(node.rhs)}'

    def visit_Number(self, node: ast.Number) -> str:
        return '0'

    def process_substitution(self, s: symboltable.SubstitutionSymbol) -> str:
        complexity_parts = []
        for cond, expr in s.rules.items():
            if cond is not None:
                complexity_parts.append(self.visit(cond))
            complexity_parts.append(self.visit(expr))

        return ' + '.join(complexity_parts)

    def visit_Subscript(self, node: ast.Subscript) -> str:
        s = self.symbol_table.resolve(node.name.val)
        if isinstance(s, symboltable.SubstitutionSymbol):
            return self.process_substitution(s)
        else:
            return '0'

    def visit_For(self, node: ast.For) -> str:
        body = ' + '.join(self.visit(statement) for statement in node.body)
        return f'{node.value_to.val - node.value_from.val} * ({body})'

    def visit_Name(self, node: ast.Name) -> str:
        s = self.symbol_table.resolve(node.val)
        if isinstance(s, symboltable.SubstitutionSymbol):
            return self.process_substitution(s)
        else:
            return '0'

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        complexity_parts = [str(self.visit(node.left)), str(self.visit(node.right))]

        ltype = node.left.result_type
        rtype = node.right.result_type
        if isinstance(ltype, ast.NumericType) and isinstance(rtype, ast.NumericType):
            complexity_parts.append('1')
        elif isinstance(ltype, ast.ArrayType) and isinstance(rtype, ast.ArrayType):
            if node.op in {node.Ops.ADD, node.Ops.SUB}:
                complexity_parts.append(' * '.join(OBJECT_COMPLEXITY[idx] for idx in ltype.indices))
            elif node.op == node.Ops.MUL:
                # Dot product
                if ltype.dim() == rtype.dim() == 1:
                    complexity_parts.append(OBJECT_COMPLEXITY[ltype.indices[0]])
                # Matrix vector multiplication
                elif {ltype.dim(), rtype.dim()} == {1, 2}:
                    tmp = [OBJECT_COMPLEXITY[ltype.indices[0]]]
                    if ltype.dim() == 1:
                        tmp.append(OBJECT_COMPLEXITY[rtype.indices[1]])
                    else:
                        tmp.append(OBJECT_COMPLEXITY[rtype.indices[0]])
                    complexity_parts.append(' * '.join(tmp))
                # Matrix matrix multiplication
                else:
                    tmp = ltype.indices + (rtype.indices[1], )
                    complexity_parts.append(' * '.join(OBJECT_COMPLEXITY[idx] for idx in tmp))
        # Scalar and matrix/vector
        else:
            if isinstance(ltype, ast.NumericType):
                complexity_parts.append(' * '.join(OBJECT_COMPLEXITY[idx] for idx in rtype.indices))
            else:
                complexity_parts.append(' * '.join(OBJECT_COMPLEXITY[idx] for idx in ltype.indices))

        return ' + '.join(complexity_parts)

    def visit_Sum(self, node: ast.Sum) -> str:
        s = self.symbol_table.resolve(node.name.val)
        mult = OBJECT_COMPLEXITY[s.symbol_type]
        body = self.visit(node.expr)

        assert isinstance(s, symboltable.ObjectSymbol)
        constraints = self.visit(s.constraints) if s.constraints else 0

        return f'{mult} * ({body} + {constraints})'

    def visit_BinaryLogicalOp(self, node: ast.BinaryLogicalOp) -> str:
        return f'1 + {self.visit(node.lhs)} + {self.visit(node.rhs)}'

    def visit_UnaryLogicalOp(self, node: ast.UnaryLogicalOp) -> str:
        return f'1 + {self.visit(node.constraint)}'

    def visit_RelOp(self, node: ast.RelOp) -> str:
        return f'1 + {self.visit(node.lhs)} + {self.visit(node.rhs)}'

    def visit_Predicate(self, node: ast.Predicate) -> str:
        return '1'

    def visit_EE(self, node: ast.EE) -> str:
        complexity_parts = ['N ** 3']
        for part in (node.rhs, node.diag, node.off):
            complexity_parts.append(self.visit(part))

        return ' + '.join(complexity_parts)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        complexity_parts = []
        if isinstance(node.expr.result_type, ast.NumericType):
            complexity_parts = ['1']
        elif isinstance(node.expr.result_type, ast.ArrayType):
            complexity_parts.append(' * '.join([OBJECT_COMPLEXITY[idx] for idx in node.expr.result_type.indices]))
        else:
            raise RuntimeError('We should not get here')

        complexity_parts.append(self.visit(node.expr))

        return ' + '.join(complexity_parts)

    def visit_Function(self, node: ast.Function) -> str:
        if node.name == 'inv':
            complexity_parts = ['N ** 3']
        else:
            complexity_parts = ['1']

        complexity_parts.append(self.visit(node.arg))

        return ' + '.join(complexity_parts)
