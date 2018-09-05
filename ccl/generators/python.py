from typing import List, Union

from ccl.symboltable import *
from ccl.ast import *

__all__ = ['Python']


python_template = '''\
import numpy as np

from method import ChargeCalculationMethod
from structures.molecule import Molecule
import geometry


class ChargeMethod(ChargeCalculationMethod):
    ATOM_PARAMETERS = [{atom_parameters}]
    BOND_PARAMETERS = [{bond_parameters}]
    COMMON_PARAMETERS = [{common_parameters}]

{defs}
    def calculate_charges(self, molecule: Molecule):
        n = len(molecule)
        charges = np.zeros(n, np.float_)
        
{code}
        
        return charges
'''


# noinspection PyPep8Naming
class Python(ASTVisitor):
    def __init__(self, symbol_table: SymbolTable) -> None:
        super().__init__()
        self.symbol_table: SymbolTable = symbol_table
        self.definitions: List[str] = []
        self.depth: int = 2
        self.sum_count: int = 0
        self.resolving_node: Optional[ASTNode] = None

    def p(self, string: str) -> str:
        return ' ' * self.depth * 4 + string

    def define_new_symbols(self, symbol_table: SymbolTable) -> str:
        code = []
        for symbol in symbol_table.symbols.values():
            if isinstance(symbol, VariableSymbol) and symbol.types:
                sizes = []
                for t in symbol.types:
                    if t == ObjectType.ATOM:
                        sizes.append('n')
                    else:
                        sizes.append('len(molecule.bonds)')
                sizes_str = ', '.join(sizes)
                if len(symbol.types) > 1:
                    sizes_str = f'({sizes})'
                code.append(self.p(f'{symbol.name} = np.zeros({sizes_str}, np.float_)'))
        return '\n'.join(code) + '\n' if code else ''

    def get_parameters(self)-> Tuple[str, str, str]:
        atom_parameters = []
        bond_parameters = []
        common_parameters = []
        for s in self.symbol_table.symbols.values():
            if isinstance(s, ParameterSymbol):
                if s.kind == ParameterType.ATOM:
                    atom_parameters.append(s.name)
                elif s.kind == ParameterType.BOND:
                    bond_parameters.append(s.name)
                else:
                    common_parameters.append(s.name)

        atom_parameters_str = ', '.join(f'\'{s}\'' for s in atom_parameters)
        bond_parameters_str = ', '.join(f'\'{s}\'' for s in bond_parameters)
        common_parameters_str = ', '.join(f'\'{s}\'' for s in common_parameters)
        return atom_parameters_str, bond_parameters_str, common_parameters_str

    def process_expressions(self) -> None:
        template = '''\
def {name}(self, {args}):
{code}
'''
        for s in self.symbol_table.symbols.values():
            if isinstance(s, ExprSymbol):
                if len(s.rules) == 1:
                    code = f'    return {self.visit(s.rules[None])}'
                    indices = ', '.join(s.indices) if s.indices else ''
                    self.definitions.append(template.format(name=s.name, args=indices, code=code))
                else:
                    code = ''
                    for constraint, value in s.rules.items():
                        expr = self.visit(value)
                        if constraint is not None:
                            cond = self.visit(constraint)
                            code += f'    if {cond}:\n'
                            code += f'        return {expr}\n'
                        else:
                            code += f'    return {expr}'
                    indices = ', '.join(s.indices)
                    self.definitions.append(template.format(name=s.name, args=indices, code=code))

    def visit_Method(self, node: Method) -> str:
        code_lines = []
        self.process_expressions()
        for statement in node.statements:
            code_lines.append(self.visit(statement))
        code = '\n'.join(code_lines)
        defs = '\n'.join(f'    {line}' for d in self.definitions for line in d.split('\n'))
        atom_parameters, bond_parameters, common_parameters = self.get_parameters()
        return python_template.format(defs=defs, code=code, atom_parameters=atom_parameters,
                                      bond_parameters=bond_parameters, common_parameters=common_parameters)

    def visit_Assign(self, node: Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return self.p(f'{lhs} = {rhs}')

    def visit_Number(self, node: Number) -> Union[int, float]:
        return node.n

    def visit_Name(self, node: Name) -> str:
        symbol = SymbolTable.get_table(node).resolve(node.name)
        if isinstance(symbol, ExprSymbol):
            return f'self.{node.name}()'
        else:
            return node.name

    def visit_Subscript(self, node: Subscript) -> str:
        if self.resolving_node is not None:
            symbol = SymbolTable.get_table(self.resolving_node).resolve(node.name.name)
        else:
            symbol = SymbolTable.get_table(node).resolve(node.name.name)
        if isinstance(symbol, VariableSymbol):
            name = 'charges' if symbol.name == 'q' else symbol.name
            indices = ', '.join(f'{self.visit(idx)}.index' for idx in node.indices)
            return f'{name}[{indices}]'
        elif isinstance(symbol, ParameterSymbol) and symbol.kind == ParameterType.ATOM:
                return f'self.parameters.atom[\'{symbol.name}\']({node.indices[0].name})'
        elif isinstance(symbol, ParameterSymbol) and symbol.kind == ParameterType.BOND:
                if len(node.indices) == 1:
                    return f'self.parameters.bond[\'{symbol.name}\']({node.indices[0].name})'
                else:
                    return f'self.parameters.bond[\'{symbol.name}\']({node.indices[0].name}, {node.indices[1].name})'
        elif isinstance(symbol, ExprSymbol):
            indices = ', '.join(f'{self.visit(idx)}' for idx in node.indices)
            return f'self.{symbol.name}({indices})'
        elif isinstance(symbol, FunctionSymbol):
            if symbol.function.name == 'distance':
                indices = ', '.join(f'{self.visit(idx)}' for idx in node.indices)
                return f'geometry.distance({indices})'
            elif symbol.function.name == 'vdw_radius':
                name = self.visit(node.indices[0])
                return f'{name}.element.vdw_radius'
            else:
                raise NotImplemented(f'Can\' translate function {symbol.function.name}')
        else:
            raise NotImplemented(f'Unknown symbol type {symbol}')

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        return f'{node.op.value}' + self.visit(node.expr)

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if not is_atom(node.left):
            left = f'({left})'
        if not is_atom(node.right):
            right = f'({right})'
        if node.op == BinaryOp.Ops.POW:
            op = '**'
        else:
            op = node.op.value

        return f'{left} {op} {right}'

    def visit_For(self, node: For) -> str:
        value_from = self.visit(node.value_from)
        value_to = self.visit(node.value_to)
        name = self.visit(node.name)
        self.depth += 1
        statements = []
        for statement in node.body:
            statements.append(self.visit(statement))

        code = '\n'.join(statements)
        defines = self.define_new_symbols(node.symbol_table)
        self.depth -= 1
        return self.p(f'for {name} in range({value_from}, {value_to + 1}):\n{defines}{code}')

    def visit_ForEach(self, node: ForEach) -> str:
        self.depth += 1
        statements = []
        name = self.visit(node.name)
        for statement in node.body:
            statements.append(self.visit(statement))

        code = '\n'.join(statements)
        defines = self.define_new_symbols(node.symbol_table)
        self.depth -= 1
        kind = ObjectType(node.kind).value.lower()
        return self.p(f'for {name} in molecule.{kind}s:\n{defines}{code}')

    def visit_BinaryLogicalOp(self, node: BinaryLogicalOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value.lower()
        return f'{lhs} {op} {rhs}'

    def visit_UnaryLogicalOp(self, node: UnaryLogicalOp) -> str:
        expr = self.visit(node.constraint)
        return f'{node.op.value.lower()} {expr}'

    def visit_RelOp(self, node: RelOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value
        return f'{lhs} {op} {rhs}'

    def visit_String(self, node: String) -> str:
        return f'\'{node.s}\''

    def visit_Predicate(self, node: Predicate) -> str:
        arg_list = [self.visit(arg) for arg in node.args]
        args = ', '.join(arg_list)
        if node.name == 'bonded':
            return f'molecule.graph.bonded({args})'
        elif node.name == 'element':
            return f'{arg_list[0]}.element.name.lower() == {arg_list[1]}.lower()'
        else:
            return f'{node.name}({args})'

    def visit_Sum(self, node: Sum) -> str:
        template = '''\
def {name}(self, {args}):
    total = 0
    objects = {objects}
    for {obj} in objects:
        total += {expr}

    return total    
'''
        fname = f'sum_{self.sum_count}'
        obj = self.visit(node.name)
        self.sum_count += 1
        expr = self.visit(node.expr)
        names = NameGetter.visit(node.expr) - {obj}
        needed_names = []
        for name in names:
            if self.symbol_table.resolve(name) is None:
                needed_names.append(name)

        args = ', '.join(['molecule'] + needed_names)
        symbol = self.symbol_table.resolve(obj)
        old = self.resolving_node
        self.resolving_node = node
        if symbol.constraints is not None:
            cond = ' if ' + self.visit(symbol.constraints)
        else:
            cond = ''
        self.resolving_node = old
        objects = f'[{obj} for {obj} in molecule.{symbol.kind.value.lower()}s{cond}]'
        self.definitions.append(template.format(name=fname, obj=obj, args=args, objects=objects, expr=expr))
        return f'self.{fname}({args})'
