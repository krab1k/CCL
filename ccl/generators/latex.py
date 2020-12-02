"""Generate LaTeX representation of a method written in CCL"""


from typing import List, DefaultDict
from collections import defaultdict

from ccl import ast, symboltable, types
from ccl.functions import MATH_FUNCTIONS


GREEK_LETTERS = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu',
                 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega']


__all__ = ['Latex']


latex_template = '''\
\\documentclass{{article}}
\\usepackage{{algorithmicx}}
\\usepackage{{etoolbox}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{bm}}

\\algblockdefx[ForEach]{{ForEach}}{{EndForEach}}%
    [3]{{\\textbf{{for $\\forall$ #1}} $#2$\\notblank{{#3}}{{\\textbf{{ such that}} #3}}{{}}:}}%
    {{}}
    
\\algblockdefx[For]{{For}}{{EndFor}}%
    [3]{{\\textbf{{for $#1 = #2$ to $#3$}}:}}%
    {{}}
    
\\algtext*{{EndForEach}}
\\algtext*{{EndFor}}
    
\\pagestyle{{empty}}
\\begin{{document}}
\\noindent\\textbf{{{name}}}
\\begin{{algorithmic}}[1]
{method}
\\end{{algorithmic}}
\\bigskip
where
{substitutions}
{equalizations}
{annotations}
\\end{{document}}
'''

for_template = '''\
\\For{{{name}}}{{{value_from}}}{{{value_to}}}
{code}
\\EndFor\
'''

foreach_template = '''\
\\ForEach{{{type}}}{{{name}}}{{{constraints}}}
{code}
\\EndForEach\
'''

substitutions_template = '''\
\\begin{{eqnarray*}}
{substitutions}
\\end{{eqnarray*}}\
'''

cases_template = '''\
{lhs} &=& 
\\begin{{cases}}
{cases}
\\end{{cases}}\
'''


def add_article(word: str) -> str:
    if word[0] in 'aeio':
        return f'an {word}'
    else:
        return f'a {word}'


def greek_if_needed(word: str) -> str:
    return f'\\{word}' if word.capitalize() in GREEK_LETTERS else word


def make_parameter_sentence(p_type: str, symbols: List[symboltable.ParameterSymbol]) -> str:
    if len(symbols) == 1:
        return f'${greek_if_needed(symbols[0].name)}$ is {add_article(p_type)} parameter'
    else:
        names = ', '.join(f'${greek_if_needed(s.name)}$' for s in symbols[:-1])
        return names + f' and ${greek_if_needed(symbols[-1].name)}$ are {p_type} parameters'


class Latex(ast.ASTVisitor):
    def __init__(self, table: symboltable.SymbolTable, **kwargs: bool) -> None:
        self._symbol_table: symboltable.SymbolTable = table
        self._full_output: bool = kwargs.get('full_output', False)

        self._substitutions: List[symboltable.SubstitutionSymbol] = []
        self._ee_expressions: List[ast.EE] = []

    def process_symbols(self) -> List[str]:
        sentences = []
        parameters: DefaultDict[str, List[symboltable.ParameterSymbol]] = defaultdict(list)
        constants = []
        functions = []
        objects = []

        assert self._symbol_table.parent is not None
        for s in self._symbol_table.parent.symbols.values():
            if isinstance(s, symboltable.ParameterSymbol):
                if s.symbol_type == ast.ParameterType.ATOM:
                    parameters['atom'].append(s)
                elif s.symbol_type == ast.ParameterType.BOND:
                    parameters['bond'].append(s)
                else:
                    parameters['common'].append(s)
            elif isinstance(s, symboltable.ConstantSymbol):
                constants.append(s)
            elif isinstance(s, symboltable.FunctionSymbol):
                functions.append(s)
            elif isinstance(s, symboltable.ObjectSymbol):
                objects.append(s)
            elif isinstance(s, symboltable.SubstitutionSymbol):
                self._substitutions.append(s)

        for p_type in ['atom', 'bond', 'common']:
            if parameters[p_type]:
                sentences.append(make_parameter_sentence(p_type, parameters[p_type]))

        sentences.extend(f'${greek_if_needed(s.name)}$ is the {s.property.name} of {s.element}' for s in constants)
        sentences.extend(f'${greek_if_needed(s.name)}$ is {s.function.name}' for s in functions if s.name not in MATH_FUNCTIONS)

        for s in objects:
            constraints = ' such that ' + self.visit(s.constraints) if s.constraints else ''
            sentences.append(f'${greek_if_needed(s.name)}$ is {add_article(s.type.value.lower())}{constraints}')

        return sentences

    def process_substitutions(self) -> str:
        if not self._substitutions:
            return ''

        substitutions = []
        for s in self._substitutions:
            if s.indices:
                lhs = f'{greek_if_needed(s.name)}_{{{", ".join(self.visit(idx) for idx in s.indices)}}}'
            else:
                lhs = f'{greek_if_needed(s.name)}'
            if len(s.rules) == 1:
                substitutions.append(f'{lhs} &=& {self.visit(s.rules[None])}\\\\')
            else:
                rules = []
                for constraint, expr in s.rules.items():
                    if constraint is None:
                        continue
                    rules.append(f'{self.visit(expr)} & \\text{{if {self.visit(constraint)}}},\\\\')
                rules.append(f'{self.visit(s.rules[None])} & \\text{{otherwise.}}')
                substitutions.append(cases_template.format(lhs=lhs, cases='\n'.join(rules)))

        return substitutions_template.format(substitutions='\n'.join(substitutions))

    def process_EE(self) -> str:
        if not self._ee_expressions:
            return ''

        equalizations = []
        for i, ee in enumerate(self._ee_expressions):
            res = f'$\\bm{{q^{i}}}$ is a solution to a system of N linear equations in a form\n'
            if isinstance(ee.rhs, ast.UnaryOp) and ee.rhs.op == ast.UnaryOp.Ops.NEG:
                rhs = self.visit(ee.rhs.expr)
            else:
                rhs = f'-{self.visit(ee.rhs)}'
            off = self.visit(ee.off)
            diag = self.visit(ee.diag)
            res += f'\\[\\chi_{ee.idx_row} = {rhs} + {diag}\\bm{{q}}_{ee.idx_row} +' \
                   f'\\sum_{{{ee.idx_row} \\neq {ee.idx_col}}} {off}\\]'
            res += f'subject to $\\sum \\bm{{q}}_{ee.idx_row} = Q$,'
            equalizations.append(res)

        return '\n'.join(equalizations)

    def visit_Method(self, node: ast.Method) -> str:
        method = '\n'.join(self.visit(statement) for statement in node.statements)

        annotations = ['$\\bm{q}$ is a vector of atomic charges']
        annotations.extend(self.process_symbols())

        equalizations = self.process_EE()
        if equalizations:
            annotations.insert(1, '$Q$ is a total molecular charge')

        substitutions = self.process_substitutions()
        if substitutions:
            annotations[0] = f'and {annotations[0]}'

        annotations_str = ', '.join(annotations) + '.'

        if self._full_output:
            return latex_template.format(name=node.name, method=method, equalizations=equalizations,
                                         substitutions=substitutions, annotations=annotations_str)
        else:
            return method + equalizations + substitutions + annotations_str

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return f'\\State $\\displaystyle {lhs} = {rhs}$'

    def visit_For(self, node: ast.For) -> str:
        name = self.visit(node.name)
        value_from = self.visit(node.value_from)
        value_to = self.visit(node.value_to)
        statements = [self.visit(s) for s in node.body]
        return for_template.format(name=name, value_from=value_from, value_to=value_to, code='\n'.join(statements))

    def visit_ForEach(self, node: ast.ForEach) -> str:
        name = self.visit(node.name)
        if node.type == ast.ObjectType.ATOM:
            ab_type = 'atom'
        else:
            ab_type = 'bond'

        if node.atom_indices:
            atoms = f' = ({node.atom_indices[0]}, {node.atom_indices[1]})'
        else:
            atoms = ''

        constraints = self.visit(node.constraints) if node.constraints else ''
        statements = [self.visit(s) for s in node.body]
        return foreach_template.format(name=name + atoms, type=ab_type, constraints=constraints,
                                       code='\n'.join(statements))

    def visit_Name(self, node: ast.Name) -> str:
        name = greek_if_needed(node.val)
        s = self._symbol_table.resolve(node.val)
        if isinstance(s, symboltable.VariableSymbol) and isinstance(s.symbol_type, types.ArrayType):
            return f'\\bm{{{name}}}'
        else:
            return name

    @staticmethod
    def visit_Number(node: ast.Number) -> str:
        if node.val < 0:
            return f'({str(node.val)})'
        else:
            return str(node.val)

    def visit_Subscript(self, node: ast.Subscript) -> str:
        name = self.visit(node.name)
        indices = ', '.join(self.visit(idx) for idx in node.indices)

        return f'{name}_{{{indices}}}'

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        def need_braces(node: ast.Expression) -> bool:
            if isinstance(node, ast.BinaryOp) and node.op == ast.BinaryOp.Ops.POW:
                return False
            elif isinstance(node, ast.Function):
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

        op_str = node.op.value if node.op != ast.BinaryOp.Ops.MUL else r'\cdot'

        if node.op == ast.BinaryOp.Ops.DIV:
            return f'\\frac{{{left}}}{{{right}}}'
        else:
            return f'{{{left}}} {op_str} {{{right}}}'

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        expr = self.visit(node.expr)
        op = node.op.value.lower()
        return f'{op} {expr}'

    def visit_Sum(self, node: ast.Sum) -> str:
        name = self.visit(node.name)
        expr = self.visit(node.expr)

        return f'\\sum_{{{name}}} \\left({expr}\\right)'

    def visit_Predicate(self, node: ast.Predicate) -> str:
        args = [self.visit(arg) for arg in node.args]
        if node.name == 'bonded':
            return f'${args[0]}$ is bonded to ${args[1]}$'
        elif node.name == 'bond_distance':
            return f'${args[0]}$ is ${args[2]}$ bonds apart from ${args[1]}$'
        elif node.name == 'element':
            return f'${args[0]}$ is {args[1]}'
        elif node.name == 'near':
            return f'${args[0]}$ is within ${args[2]}$ angstroms from ${args[1]}$'

        return f'{node.name}({args})'

    def visit_RelOp(self, node: ast.RelOp) -> str:
        d = {
            ast.RelOp.Ops.LE: r'\leq',
            ast.RelOp.Ops.GE: r'\geq',
            ast.RelOp.Ops.NEQ: r'\neq'
        }

        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = d.get(node.op, node.op.value)
        return f'${lhs} {op} {rhs}$'

    def visit_BinaryLogicalOp(self, node: ast.BinaryLogicalOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value.lower()
        return f'{lhs} {op} {rhs}'

    def visit_UnaryLogicalOp(self, node: ast.UnaryLogicalOp) -> str:
        constraint = self.visit(node.constraint)
        op = node.op.value.lower()
        return f'{op} {constraint}'

    def visit_Function(self, node: ast.Function) -> str:
        arg = self.visit(node.arg)
        if node.name == 'inv':
            return f'{arg} ^ {{-1}}'
        elif node.name == 'sqrt':
            return f'\\sqrt{{{arg}}}'

        return f'\\mathrm{{{node.name}}}({arg})'

    def visit_EE(self, node: ast.EE) -> str:
        self._ee_expressions.append(node)

        res = f'\\bm{{q^{len(self._ee_expressions) - 1}}}'
        return res
