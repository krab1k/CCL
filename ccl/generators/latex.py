"""Generate LaTeX representation of a method written in CCL"""


from ccl import ast, symboltable


GREEK_LETTERS = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu',
                 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega']


__all__ = ['Latex']


latex_template = '''\
\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\pagestyle{{empty}}
\\begin{{document}}
{code}
\\end{{document}}
'''


class Latex(ast.ASTVisitor):
    def __init__(self, table: symboltable.SymbolTable, **kwargs: bool) -> None:
        self.symbol_table: symboltable.SymbolTable = table
        self.full_output: bool = kwargs.get('full_output', False)

    def visit_Method(self, node: ast.Method) -> str:
        method = ''
        for statement in node.statements:
            method += self.visit(statement)

        annotations = 'where $q$ is a vector of atomic charges.'

        if self.full_output:
            return latex_template.format(code=method + '\\\\\n' + annotations)
        else:
            return method + annotations

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return f'$${lhs} = {rhs}$$\\\\'

    def visit_For(self, node: ast.For) -> str:
        name = self.visit(node.name)
        value_from = self.visit(node.value_from)
        value_to = self.visit(node.value_to)
        header = f'for ${value_from} \\leq {name} \\leq {value_to}$:\\\\\n'
        statements = []
        for statement in node.body:
            statements.append(self.visit(statement))

        return header + '\n'.join(statements)

    def visit_ForEach(self, node: ast.ForEach) -> str:
        name = self.visit(node.name)
        if node.type == ast.ObjectType.ATOM:
            ab_type = 'atom'
        else:
            ab_type = 'bond'
        header = f'$\\forall$ {ab_type} ${name}$:\\\\\n'
        statements = []
        for statement in node.body:
            statements.append(self.visit(statement))

        return header + '\n'.join(statements)

    @staticmethod
    def visit_Name(node: ast.Name) -> str:
        if node.val.capitalize() in GREEK_LETTERS:
            return f'\\{node.val}'
        else:
            return node.val

    @staticmethod
    def visit_Number(node: ast.Number) -> str:
        return str(node.val)

    def visit_Subscript(self, node: ast.Subscript) -> str:
        name = self.visit(node.name)
        indices = ', '.join(self.visit(idx) for idx in node.indices)

        return f'{name}_{{{indices}}}'

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        def need_braces(node: ast.Expression) -> bool:
            if isinstance(node, ast.BinaryOp) and node.op in [ast.BinaryOp.Ops.POW, ast.BinaryOp.Ops.DIV]:
                return False
            elif ast.is_atom(node):
                return False
            else:
                return True

        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op not in [ast.BinaryOp.Ops.ADD, ast.BinaryOp.Ops.SUB, ast.BinaryOp.Ops.DIV]:
            if need_braces(node.left):
                left = f'\\left({left}\\right)'
            if need_braces(node.right):
                right = f'\\left({right}\\right)'

        op_str = node.op.value if node.op != ast.BinaryOp.Ops.MUL else '\\cdot'

        if node.op == ast.BinaryOp.Ops.DIV:
            return f'\\frac{{{left}}}{{{right}}}'
        else:
            return f'{{{left}}} {op_str} {{{right}}}'

    def visit_Sum(self, node: ast.Sum) -> str:
        name = self.visit(node.name)
        expr = self.visit(node.expr)

        return f'\\sum_{{{name}}} \\left({expr}\\right)'
