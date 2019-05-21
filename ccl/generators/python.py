"""Translate method in CCL to Python"""

from typing import List, Union, Tuple, Optional

from ccl import ast, symboltable

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
class Python(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable, **kwargs) -> None:
        super().__init__()
        self.symbol_table: symboltable.SymbolTable = symbol_table
        self.definitions: List[str] = []
        self.depth: int = 2
        self.sum_count: int = 0
        self.resolving_node: Optional[ast.ASTNode] = None

    def p(self, string: str) -> str:
        return ' ' * self.depth * 4 + string

    def define_new_symbols(self, symbol_table: symboltable.SymbolTable) -> str:
        code = []
        for symbol in symbol_table.symbols.values():
            if isinstance(symbol, symboltable.VariableSymbol) and symbol.types:
                sizes = []
                for t in symbol.types:
                    if t == ast.ObjectType.ATOM:
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
        for symbol in self.symbol_table.symbols.values():
            if isinstance(symbol, symboltable.ParameterSymbol):
                if symbol.kind == ast.ParameterType.ATOM:
                    atom_parameters.append(symbol.name)
                elif symbol.kind == ast.ParameterType.BOND:
                    bond_parameters.append(symbol.name)
                else:
                    common_parameters.append(symbol.name)

        atom_parameters_str = ', '.join(f'\'{s}\'' for s in atom_parameters)
        bond_parameters_str = ', '.join(f'\'{s}\'' for s in bond_parameters)
        common_parameters_str = ', '.join(f'\'{s}\'' for s in common_parameters)
        return atom_parameters_str, bond_parameters_str, common_parameters_str

    def process_expressions(self) -> None:
        template = '''\
def {name}(self, {args}):
{code}
'''
        for symbol in self.symbol_table.symbols.values():
            if isinstance(symbol, symboltable.ExprSymbol):
                if len(symbol.rules) == 1:
                    names = ast.NameGetter.visit(symbol.rules[None])
                    needed_names = []
                    for name in names:
                        if self.symbol_table.is_global(name):
                            continue
                        s = self.symbol_table.resolve(name)
                        if not isinstance(s, symboltable.ParameterSymbol):
                            needed_names.append(name)
                    res = self.visit(symbol.rules[None])
                    code = f'    return {res}'
                else:
                    code = ''
                    needed_names = []
                    for constraint, value in symbol.rules.items():
                        names = ast.NameGetter.visit(value)
                        for name in names:
                            if name in symbol.indices:
                                needed_names.append(name)
                            elif self.symbol_table.is_global(name):
                                continue
                            else:
                                s = self.symbol_table.resolve(name)
                                if not isinstance(s, symboltable.ParameterSymbol):
                                    needed_names.append(name)

                        expr = self.visit(value)
                        if constraint is not None:
                            cond = self.visit(constraint)
                            code += f'    if {cond}:\n'
                            code += f'        return {expr}\n'
                        else:
                            code += f'    return {expr}'

                indices = ', '.join(needed_names)
                self.definitions.append(template.format(name=symbol.name, args=indices, code=code))

    def visit_Method(self, node: ast.Method) -> str:
        code_lines = []
        self.process_expressions()
        for statement in node.statements:
            code_lines.append(str(self.visit(statement)))
        code = '\n'.join(code_lines)
        defs = '\n'.join(f'    {line}' for d in self.definitions for line in d.split('\n'))
        atom_parameters, bond_parameters, common_parameters = self.get_parameters()
        return python_template.format(defs=defs, code=code, atom_parameters=atom_parameters,
                                      bond_parameters=bond_parameters, common_parameters=common_parameters)

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return self.p(f'{lhs} = {rhs}')

    def visit_Number(self, node: ast.Number) -> Union[int, float]:
        return node.n

    def visit_Name(self, node: ast.Name) -> str:
        symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(node.name)
        if isinstance(symbol, symboltable.ExprSymbol):
            names = ast.NameGetter.visit(symbol.rules[None])
            needed_names = []
            for name in names:
                if not self.symbol_table.is_global(name):
                    needed_names.append(name)

            args = ', '.join(needed_names)
            return f'self.{node.name}({args})'

        return node.name

    def visit_Subscript(self, node: ast.Subscript) -> str:
        if self.resolving_node is not None:
            symbol = symboltable.SymbolTable.get_table_for_node(self.resolving_node).resolve(node.name.name)
        else:
            symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(node.name.name)
        if isinstance(symbol, symboltable.VariableSymbol):
            name = 'charges' if symbol.name == 'q' else symbol.name
            indices = ', '.join(f'{self.visit(idx)}.index' for idx in node.indices)
            return f'{name}[{indices}]'
        if isinstance(symbol, symboltable.ParameterSymbol) and symbol.kind == ast.ParameterType.ATOM:
            return f'self.parameters.atom[\'{symbol.name}\']({node.indices[0].name})'
        if isinstance(symbol, symboltable.ParameterSymbol) and symbol.kind == ast.ParameterType.BOND:
            if len(node.indices) == 1:
                return f'self.parameters.bond[\'{symbol.name}\']({node.indices[0].name})'

            return f'self.parameters.bond[\'{symbol.name}\']({node.indices[0].name}, {node.indices[1].name})'
        if isinstance(symbol, symboltable.ExprSymbol):
            indices = ', '.join(f'{self.visit(idx)}' for idx in node.indices)
            return f'self.{symbol.name}({indices})'
        if isinstance(symbol, symboltable.FunctionSymbol):
            if symbol.function.name == 'distance':
                indices = ', '.join(f'{self.visit(idx)}' for idx in node.indices)
                return f'geometry.distance({indices})'
            if symbol.function.name == 'vdw_radius':
                name = self.visit(node.indices[0])
                return f'{name}.element.vdw_radius'

            raise NotImplementedError(f'Can\' translate function {symbol.function.name}')

        raise NotImplementedError(f'Unknown symbol type {symbol}')

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        return f'{node.op.value}' + str(self.visit(node.expr))

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if not ast.is_atom(node.left):
            left = f'({left})'
        if not ast.is_atom(node.right):
            right = f'({right})'
        if node.op == ast.BinaryOp.Ops.POW:
            op = '**'
        else:
            op = node.op.value

        return f'{left} {op} {right}'

    def visit_For(self, node: ast.For) -> str:
        value_from = self.visit_Number(node.value_from)
        value_to = self.visit_Number(node.value_to)
        name = self.visit(node.name)
        self.depth += 1
        statements = []
        for statement in node.body:
            statements.append(str(self.visit(statement)))

        code = '\n'.join(statements)
        defines = self.define_new_symbols(node.symbol_table)
        self.depth -= 1
        return self.p(f'for {name} in range({value_from}, {value_to + 1}):\n{defines}{code}')

    def visit_ForEach(self, node: ast.ForEach) -> str:
        self.depth += 1
        statements = []
        name = self.visit(node.name)
        for statement in node.body:
            statements.append(str(self.visit(statement)))

        code = '\n'.join(statements)
        defines = self.define_new_symbols(node.symbol_table)
        self.depth -= 1
        kind = ast.ObjectType(node.kind).value.lower()
        return self.p(f'for {name} in molecule.{kind}s:\n{defines}{code}')

    def visit_BinaryLogicalOp(self, node: ast.BinaryLogicalOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value.lower()
        return f'{lhs} {op} {rhs}'

    def visit_UnaryLogicalOp(self, node: ast.UnaryLogicalOp) -> str:
        expr = self.visit(node.constraint)
        return f'{node.op.value.lower()} {expr}'

    def visit_RelOp(self, node: ast.RelOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value
        return f'{lhs} {op} {rhs}'

    def visit_String(self, node: ast.String) -> str:
        return f'\'{node.s}\''

    def visit_Predicate(self, node: ast.Predicate) -> str:
        arg_list = [str(self.visit(arg)) for arg in node.args]
        args = ', '.join(arg_list)
        if node.name == 'bonded':
            return f'molecule.graph.bonded({args})'
        if node.name == 'element':
            return f'{arg_list[0]}.element.name.lower() == \'{arg_list[1]}\'.lower()'

        return f'{node.name}({args})'

    def visit_Sum(self, node: ast.Sum) -> str:
        template = '''\
def {name}(self, {args}):
    total = 0
    objects = {objects}
    for {obj} in objects:
        total += {expr}

    return total    
'''
        fname = f'sum_{self.sum_count}'
        obj = self.visit_Name(node.name)
        self.sum_count += 1
        expr = self.visit(node.expr)
        names = ast.NameGetter.visit(node.expr) - {obj}
        needed_names = []
        for name in names:
            if self.symbol_table.resolve(name) is None:
                needed_names.append(name)

        args = ', '.join(['molecule'] + needed_names)
        symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(obj)
        old = self.resolving_node
        self.resolving_node = node
        if symbol.constraints is not None:
            cond = ' if ' + str(self.visit(symbol.constraints))
        else:
            cond = ''
        self.resolving_node = old
        objects = f'[{obj} for {obj} in molecule.{symbol.kind.value.lower()}s{cond}]'
        self.definitions.append(template.format(name=fname, obj=obj, args=args, objects=objects, expr=expr))
        return f'self.{fname}({args})'
