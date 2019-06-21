"""Generate LaTeX representation of a method written in CCL"""

from typing import Union

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


def get_name(name: str) -> str:
    if name in GREEK_LETTERS or name.capitalize() in GREEK_LETTERS:
        return f'\\{name}'

    return name


# noinspection PyPep8Naming
class Latex(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable, **kwargs) -> None:
        super().__init__()
        self.depth: int = 0
        self.symbol_table: symboltable.SymbolTable = symbol_table
        self.inside_math: bool = True
        self.full_output: bool = kwargs['full_output'] if 'full_output' in kwargs else False

    def visit(self, node: ast.ASTNode) -> str:  # Just to make mypy happy
        return str(super().visit(node))

    def visit_Name(self, node: ast.Name) -> str:
        plain_name = get_name(node.val)
        if self.inside_math:
            return plain_name

        return f'${plain_name}$'

    @staticmethod
    def visit_Number(node: ast.Number) -> Union[int, float]:
        return node.val

    def visit_For(self, node: ast.For) -> str:
        name_str = self.visit(node.name)
        value_from = self.visit(node.value_from)
        value_to = self.visit(node.value_to)
        self.depth += 1
        body_str = [self.visit(s) for s in node.body]
        if len(node.body) == 1:
            body = f'{body_str[0]}'
        else:
            body = '\\\\' + '\\\\\n'.join(f'\\hspace*{{{4 * self.depth}mm}} {s}' for s in body_str)
        self.depth -= 1
        return f'\\text{{for }} {value_from} \\leq {name_str} \\leq {value_to}:\n{body}'

    def visit_ForEach(self, node: ast.ForEach) -> str:
        name_str = self.visit(node.name)
        kind = node.type.value.lower()
        self.depth += 1
        body_str = [self.visit(s) for s in node.body]
        if len(node.body) == 1:
            body = f'{body_str[0]}'
        else:
            body = '\\\\' + '\\\\\n'.join(f'\\hspace*{{{4 * self.depth}mm}} {s}' for s in body_str)
        self.depth -= 1
        return f'\\forall \\text{{ {kind} }} {name_str}: {body}'

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return f'{lhs} = {rhs}'

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if node.op == ast.BinaryOp.Ops.MUL:
            if not ast.is_atom(node.left) and not (isinstance(node.left, ast.BinaryOp) and
                                                   node.left.op == ast.BinaryOp.Ops.POW):
                left = f'\\left({left}\\right)'
            if not ast.is_atom(node.right) and not (isinstance(node.right, ast.BinaryOp) and
                                                    node.right.op == ast.BinaryOp.Ops.POW):
                right = f'\\left({right}\\right)'
            op = ''
        elif node.op == ast.BinaryOp.Ops.DIV:
            return f'\\frac{{{left}}}{{{right}}}'
        elif node.op == ast.BinaryOp.Ops.POW:
            if ast.is_atom(node.left):
                return f'{{{left}}} ^ {{{right}}}'

            return f'\\left({left}\\right)^{right}'
        else:
            op = node.op.value

        return f'{left} {op} {right}'

    def visit_Sum(self, node: ast.Sum) -> str:
        name = self.visit(node.name)
        expr = self.visit(node.expr)

        return f'\\sum_{{{name}}}\\left({expr}\\right)'

    def visit_Subscript(self, node: ast.Subscript) -> str:
        name = self.visit(node.name)
        indices = ', '.join(self.visit(idx) for idx in node.indices)
        return f'{name}_{{{indices}}}'

    def visit_Method(self, node: ast.Method) -> str:
        statements = ''
        for s in node.statements:
            statements += f'{self.visit(s)}\n'

        self.inside_math = False
        annotations = self.visit_SymbolTable()
        if self.full_output:
            code = f'\\noindent ${statements}$\n\n\\vspace*{{5mm}}\\noindent where\n\n\\noindent {annotations}'
            return latex_template.format(code=code)
        else:
            return f'\\noindent ${statements}$\n\n\\vspace*{{5mm}}\\noindent where\n\n\\noindent {annotations}'

    def visit_BinaryLogicalOp(self, node: ast.BinaryLogicalOp) -> str:
        left = self.visit(node.lhs)
        right = self.visit(node.rhs)

        return f'{left} {node.op.value.lower()} {right}'

    def visit_RelOp(self, node: ast.RelOp) -> str:
        self.inside_math = True
        left = self.visit(node.lhs)
        right = self.visit(node.rhs)
        self.inside_math = False

        return f'${left} {node.op.value} {right}$'

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        op = ast.UnaryOp.Ops(node.op).value
        return f'{op}' + self.visit(node.expr)

    def visit_UnaryLogicalOp(self, node: ast.UnaryLogicalOp) -> str:
        op = ast.UnaryLogicalOp.Ops(node.op).value
        return f'{op.lower()} ' + self.visit(node.constraint)

    def visit_Predicate(self, node: ast.Predicate) -> str:
        if node.name == 'bonded':
            a1 = self.visit(node.args[0])
            a2 = self.visit(node.args[1])
            return f'{a1}\\text{{ is bonded to }}{a2}'
        if node.name == 'element':
            a = self.visit(node.args[0])
            s = self.visit(node.args[1])
            return f'{a}\\text{{ is {s}}}'

        args = ', '.join(self.visit(arg) for arg in node.args)
        return f'\\text{{{node.name}}}({args})'

    def visit_SymbolTable(self) -> str:
        atom_parameters = []
        bond_parameters = []
        common_parameters = []
        expressions = []
        atoms = []
        bonds = []
        functions = []
        for symbol in self.symbol_table.symbols.values():
            if isinstance(symbol, symboltable.ParameterSymbol):
                if symbol.type == ast.ParameterType.ATOM:
                    atom_parameters.append(symbol)
                elif symbol.type == ast.ParameterType.BOND:
                    bond_parameters.append(symbol)
                else:
                    common_parameters.append(symbol)
            elif isinstance(symbol, symboltable.ObjectSymbol):
                if symbol.type == ast.ObjectType.ATOM:
                    atoms.append(symbol)
                else:
                    bonds.append(symbol)
            elif isinstance(symbol, symboltable.SubstitutionSymbol):
                expressions.append(symbol)
            elif isinstance(symbol, symboltable.VariableSymbol):
                pass  # We need only vector q
            elif isinstance(symbol, symboltable.FunctionSymbol):
                functions.append(symbol)
            else:
                raise RuntimeError(f'No suitable symbol type for {symbol}')

        expressions_string = []
        strings = []
        if expressions:
            self.inside_math = True
            for symbol in expressions:
                if len(symbol.rules) == 1:
                    if symbol.indices:
                        indices = '_{' + ', '.join(idx.val for idx in symbol.indices) + '}'
                    else:
                        indices = ''
                    expressions_string.append(f'${get_name(symbol.name)}{indices} = '
                                              f'{self.visit(symbol.rules[None])}$\\\\')
                else:
                    rules = ''
                    for constraint, value in symbol.rules.items():
                        if constraint:
                            c = '\\text{if }' + self.visit(constraint) + '\\\\'
                        else:
                            c = '\\text{otherwise}\\\\'
                        value_str = self.visit(value)
                        rules += f'{value_str} & {c}\n'
                    indices = '_{' + ', '.join(idx.val for idx in symbol.indices) + '}'
                    expressions_string.append(f'${get_name(symbol.name)}{indices} = \n\\begin{{cases}}\n'
                                              f'{rules}\\end{{cases}}$')
            self.inside_math = False
        if expressions_string:
            strings.append('\n\n\\noindent and\n\n$q$ is a vector of charges')
        else:
            strings.append('$q$ is a vector of charges')
        if functions:
            for symbol in functions:
                if symbol.function.name == 'distance':
                    strings.append(f'${get_name(symbol.name)}_{{i, j}}$ is a distance between atoms $i$ and $j$')
                else:
                    strings.append(f'${get_name(symbol.name)}$ is {symbol.function.name}')
        if atom_parameters:
            if len(atom_parameters) == 1:
                strings.append(f'${get_name(atom_parameters[0].name)}$ is an atom parameter')
            else:
                names = ', '.join(f'${get_name(s.name)}$' for s in atom_parameters)
                strings.append(f'{names} are atom parameters')

        if bond_parameters:
            if len(bond_parameters) == 1:
                strings.append(f'${get_name(bond_parameters[0].name)}$ is a bond parameter')
            else:
                names = ', '.join(f'${get_name(s.name)}$' for s in bond_parameters)
                strings.append(f'{names} are bond parameters')

        if common_parameters:
            if len(common_parameters) == 1:
                strings.append(f'${get_name(common_parameters[0].name)}$ is a common parameter')
            else:
                names = ', '.join(f'${get_name(s.name)}$' for s in atom_parameters)
                strings.append(f'{names} are common parameters')

        if atoms:
            for symbol in atoms:
                tmp = f'${get_name(symbol.name)}$ is an atom'
                if symbol.constraints:
                    tmp += ' such that ' + self.visit(symbol.constraints)

                strings.append(tmp)

        if bonds:
            for symbol in bonds:
                tmp = f'${get_name(symbol.name)}$ is a bond'
                if symbol.constraints:
                    tmp += ' such that ' + self.visit(symbol.constraints)

                strings.append(tmp)

        return '\n'.join(expressions_string) + ', '.join(strings) + '.'
