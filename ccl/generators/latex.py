from typing import Union

from ccl.symboltable import *
from ccl.ast import *

greek_letters = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu',
                 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega']


__all__ = ['Latex']


def get_name(name: str) -> str:
    if name in greek_letters or name.capitalize() in greek_letters:
        return f'\{name}'
    else:
        return name


# noinspection PyPep8Naming
class Latex(ASTVisitor):
    def __init__(self, symbol_table: SymbolTable) -> None:
        super().__init__()
        self.depth = 0
        self.symbol_table: SymbolTable = symbol_table
        self.inside_math = True

    def visit_Name(self, node: Name) -> str:
        plain_name = get_name(node.name)
        if self.inside_math:
            return plain_name
        else:
            return f'${plain_name}$'

    def visit_Number(self, node: Number) -> Union[int, float]:
        return node.n

    def visit_For(self, node: For) -> str:
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
        return f'\\text{{for }} {value_from} \leq {name_str} \leq {value_to}:\n{body}'

    def visit_ForEach(self, node: ForEach) -> str:
        name_str = self.visit(node.name)
        kind = node.kind.value.lower()
        self.depth += 1
        body_str = [self.visit(s) for s in node.body]
        if len(node.body) == 1:
            body = f'{body_str[0]}'
        else:
            body = '\\\\' + '\\\\\n'.join(f'\\hspace*{{{4 * self.depth}mm}} {s}' for s in body_str)
        self.depth -= 1
        return f'\\forall \\text{{ {kind} }} {name_str}: {body}'

    def visit_Assign(self, node: Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return f'{lhs} = {rhs}'

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if node.op == BinaryOp.Ops.MUL:
            if not is_atom(node.left) and not (isinstance(node.left, BinaryOp) and node.left.op == BinaryOp.Ops.POW):
                left = f'\\left({left}\\right)'
            if not is_atom(node.right) and not (isinstance(node.right, BinaryOp) and node.right.op == BinaryOp.Ops.POW):
                right = f'\\left({right}\\right)'
            op = ''
        elif node.op == BinaryOp.Ops.DIV:
            return f'\\frac{{{left}}}{{{right}}}'
        elif node.op == BinaryOp.Ops.POW:
            if is_atom(node.left):
                return f'{{{left}}} ^ {{{right}}}'
            else:
                return f'\\left({left}\\right)^{right}'
        else:
            op = node.op.value

        return f'{left} {op} {right}'

    def visit_Sum(self, node: Sum) -> str:
        name = self.visit(node.name)
        expr = self.visit(node.expr)

        return f'\sum_{{{name}}}\\left({expr}\\right)'

    def visit_Subscript(self, node: Subscript) -> str:
        name = self.visit(node.name)
        indices = ', '.join(self.visit(idx) for idx in node.indices)
        return f'{name}_{{{indices}}}'

    def visit_Method(self, node: Method) -> str:
        statements = ''
        for s in node.statements:
            statements += f'{self.visit(s)}\n'

        self.inside_math = False
        annotations = self.visit_SymbolTable()
        return f'\\noindent ${statements}$\n\n\\vspace*{{5mm}}\\noindent where\n\n\\noindent {annotations}'

    def visit_BinaryLogicalOp(self, node: BinaryLogicalOp) -> str:
        left = self.visit(node.lhs)
        right = self.visit(node.rhs)

        return f'{left} {node.op.value.lower()} {right}'

    def visit_RelOp(self, node: RelOp) -> str:
        self.inside_math = True
        left = self.visit(node.lhs)
        right = self.visit(node.rhs)
        self.inside_math = False

        return f'${left} {node.op.value} {right}$'

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        op = UnaryOp.Ops(node.op).value
        return f'{op}' + self.visit(node.expr)

    def visit_UnaryLogicalOp(self, node: UnaryLogicalOp) -> str:
        op = UnaryLogicalOp.Ops(node.op).value
        return f'{op.lower()} ' + self.visit(node.constraint)

    def visit_String(self, node: String) -> str:
        return f'\\text{{{node.s}}}'

    def visit_Predicate(self, node: Predicate) -> str:
        if node.name == 'bonded':
            a1 = self.visit(node.args[0])
            a2 = self.visit(node.args[1])
            return f'{a1}\\text{{ is bonded to }}{a2}'
        elif node.name == 'element':
            a = self.visit(node.args[0])
            s = self.visit(node.args[1])
            return f'{a}\\text{{ is {s}}}'
        else:
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
        for s in self.symbol_table.symbols.values():
            if isinstance(s, ParameterSymbol):
                if s.kind == ParameterType.ATOM:
                    atom_parameters.append(s)
                elif s.kind == ParameterType.BOND:
                    bond_parameters.append(s)
                else:
                    common_parameters.append(s)
            elif isinstance(s, ObjectSymbol):
                if s.kind == ObjectType.ATOM:
                    atoms.append(s)
                else:
                    bonds.append(s)
            elif isinstance(s, ExprSymbol):
                expressions.append(s)
            elif isinstance(s, VariableSymbol):
                pass  # We need only vector q
            elif isinstance(s, FunctionSymbol):
                functions.append(s)
            else:
                raise RuntimeError(f'No suitable symbol type for {s}')

        expressions_string = []
        strings = []
        if expressions:
            self.inside_math = True
            for s in expressions:
                if len(s.rules) == 1:
                    if s.indices:
                        indices = '_{' + ', '.join(idx for idx in s.indices) + '}'
                    else:
                        indices = ''
                    expressions_string.append(f'${get_name(s.name)}{indices} = {self.visit(s.rules[None])}$\\\\')
                else:
                    rules = ''
                    for constraint, value in s.rules.items():
                        if constraint:
                            c = '\\text{if }' + self.visit(constraint) + '\\\\'
                        else:
                            c = '\\text{otherwise}\\\\'
                        value = self.visit(value)
                        rules += f'{value} & {c}\n'
                    indices = '_{' + ', '.join(idx for idx in s.indices) + '}'
                    expressions_string.append(f'${get_name(s.name)}{indices} = \n\\begin{{cases}}\n'
                                              f'{rules}\\end{{cases}}$')
            self.inside_math = False
        if expressions_string:
            strings.append('\n\n\\noindent and\n\n$q$ is a vector of charges')
        else:
            strings.append('$q$ is a vector of charges')
        if functions:
            for s in functions:
                if s.function.name == 'distance':
                    strings.append(f'${get_name(s.name)}_{{i, j}}$ is a distance between atoms $i$ and $j$')
                else:
                    strings.append(f'${get_name(s.name)}$ is {s.function.comment}')
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
            for s in atoms:
                tmp = f'${get_name(s.name)}$ is an atom'
                if s.constraints:
                    tmp += ' such that ' + self.visit(s.constraints)

                strings.append(tmp)

        if bonds:
            for s in bonds:
                tmp = f'${get_name(s.name)}$ is a bond'
                if s.constraints:
                    tmp += ' such that ' + self.visit(s.constraints)

                strings.append(tmp)

        return '\n'.join(expressions_string) + ', '.join(strings) + '.'
