"""Translate method in CCL to C++"""

import os
from typing import Tuple, Union, Optional, List

from ccl import ast, symboltable

__all__ = ['Cpp']

with open('ccl/generators/cpp/templates/method.h') as f:
    header_template = f.read()

with open('ccl/generators/cpp/templates/method.cpp') as f:
    method_template = f.read()

with open('ccl/generators/cpp/templates/CMakeLists.txt') as f:
    cmake_template = f.read()


# noinspection PyPep8Naming
class Cpp(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable, output_dir: str = None) -> None:
        super().__init__()
        self.symbol_table: symboltable.SymbolTable = symbol_table
        self.depth: int = 1
        self.resolving_node: Optional[ast.ASTNode] = None
        self.sum_count: int = 0
        self.prototypes: List[str] = []
        self.definitions: List[str] = []
        self.output_dir: Optional[str] = output_dir
        self.method_name: str = ''

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
                        sizes.append('molecule.bonds().size()')
                sizes_str = ', '.join(sizes)
                if len(symbol.types) > 1:
                    raise NotImplementedError('Only 1D arrays are supported')
                code.append(self.p(f'std::vector<double> {symbol.name} ({sizes_str}, 0);'))
        return '\n'.join(code) + '\n' if code else ''

    def get_parameters(self) -> Tuple[str, str, str, str, str, str]:
        atom_parameters = []
        bond_parameters = []
        common_parameters = []
        for symbol in self.symbol_table.symbols.values():
            if isinstance(symbol, symboltable.ParameterSymbol):
                if symbol.type == ast.ParameterType.ATOM:
                    atom_parameters.append(symbol.name)
                elif symbol.type == ast.ParameterType.BOND:
                    bond_parameters.append(symbol.name)
                else:
                    common_parameters.append(symbol.name)

        atom_str = '{' + ', '.join(f'"{s}"' for s in atom_parameters) + '}'
        bond_str = '{' + ', '.join(f'"{s}"' for s in bond_parameters) + '}'
        common_str = '{' + ', '.join(f'"{s}"' for s in common_parameters) + '}'
        atom_enum = 'enum atom{' + ', '.join(f'{s}' for s in atom_parameters) + '};' if atom_parameters else ''
        bond_enum = 'enum bond{' + ', '.join(f'{s}' for s in bond_parameters) + '};' if bond_parameters else ''
        common_enum = 'enum common{' + ', '.join(f'{s}' for s in common_parameters) + '};' if common_parameters else ''
        return atom_str, bond_str, common_str, atom_enum, bond_enum, common_enum

    def process_expressions(self) -> None:
        template = '''\
double {method_name}::{name}({args}) const {{
{code}
}}
'''
        for symbol in self.symbol_table.symbols.values():
            if isinstance(symbol, symboltable.SubstitutionSymbol):
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
                    code = f'    return {res};\n'
                else:
                    code = ''
                    needed_names = []
                    for constraint, value in symbol.rules.items():
                        names = ast.NameGetter.visit(value)
                        for name in names:
                            if name in symbol.indices:
                                # TODO what about bonds?
                                needed_names.append(f'const Atom &{name}')
                            elif self.symbol_table.is_global(name):
                                continue
                            else:
                                s = self.symbol_table.resolve(name)
                                if not isinstance(s, symboltable.ParameterSymbol):
                                    needed_names.append(name)

                        expr = self.visit(value)
                        if constraint is not None:
                            cond = self.visit(constraint)
                            code += f'    if({cond})\n'
                            code += f'        return {expr};\n'
                        else:
                            code += f'    return {expr};\n'

                indices = ', '.join(needed_names)
                self.prototypes.append(f'double {symbol.name}({indices}) const;')
                self.definitions.append(
                    template.format(method_name=self.method_name, name=symbol.name, args=indices, code=code))

    def visit_Method(self, node: ast.Method) -> str:
        code_lines = []

        self.method_name = node.name

        self.process_expressions()
        for statement in node.statements:
            code_lines.append(str(self.visit(statement)))

        code = '\n'.join(code_lines)
        sys_includes = ''
        user_includes = ''

        atom_str, bond_str, common_str, atom_enum, bond_enum, common_enum = self.get_parameters()
        defs = '\n'.join(f'{line}' for d in self.definitions for line in d.split('\n'))
        prototypes = '\n    '.join(self.prototypes)

        header = header_template.format(method_name=self.method_name, common_parameters=common_str,
                                        atom_parameters=atom_str,
                                        bond_parameters=bond_str,
                                        common_parameters_enum=common_enum, atom_parameters_enum=atom_enum,
                                        bond_parameters_enum=bond_enum,
                                        prototypes=prototypes)
        method = method_template.format(method_name=self.method_name,
                                        code=code, sys_includes=sys_includes, user_includes=user_includes,
                                        defs=defs)

        if self.output_dir is not None:
            with open(os.path.join(self.output_dir, 'ccl_method.h'), 'w') as f:
                f.write(header)

            with open(os.path.join(self.output_dir, 'ccl_method.cpp'), 'w') as f:
                f.write(method)

            with open(os.path.join(self.output_dir, 'CMakeLists.txt'), 'w') as f:
                f.write(cmake_template.format(method_name=self.method_name))

        return header + method

    def visit_Number(self, node: ast.Number) -> Union[int, float]:
        return node.val

    def visit_Name(self, node: ast.Name) -> str:
        return node.val

    def visit_For(self, node: ast.For) -> str:
        value_from = self.visit_Number(node.value_from)
        value_to = self.visit_Number(node.value_to)
        name = self.visit_Name(node.name)
        self.depth += 1
        statements = []
        for statement in node.body:
            statements.append(str(self.visit(statement)))

        defines = self.define_new_symbols(node.symbol_table)
        self.depth -= 1
        code = '\n'.join(statements)
        return self.p(f'for(int {name} = {value_from}; {name} <= {value_to}; {name}++) {{\n{defines}{code}\n') + self.p(
            '}')

    def visit_ForEach(self, node: ast.ForEach) -> str:
        self.depth += 1
        statements = []
        name = self.visit(node.name)
        for statement in node.body:
            statements.append(str(self.visit(statement)))

        defines = self.define_new_symbols(node.symbol_table)
        self.depth -= 1
        code = '\n'.join(statements)
        kind = ast.ObjectType(node.type).value.lower()
        return self.p(f'for(const auto &{name}: molecule.{kind}s()) {{\n{defines}{code}\n') + self.p('}')

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        return self.p(f'{lhs} = {rhs};')

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if not ast.is_atom(node.left):
            left = f'({left})'
        if not ast.is_atom(node.right):
            right = f'({right})'
        if node.op == ast.BinaryOp.Ops.POW:
            return f'pow({left}, {right})'
        else:
            op = node.op.value
            return f'{left} {op} {right}'

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        return f'{node.op.value}' + str(self.visit(node.expr))

    def visit_Subscript(self, node: ast.Subscript) -> str:
        if self.resolving_node is not None:
            symbol = symboltable.SymbolTable.get_table_for_node(self.resolving_node).resolve(node.name.val)
        else:
            symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(node.name.val)
        if isinstance(symbol, symboltable.VariableSymbol):
            name = 'q' if symbol.name == 'q' else symbol.name
            indices = ', '.join(f'{self.visit(idx)}.index()' for idx in node.indices)
            return f'{name}[{indices}]'

        if isinstance(symbol, symboltable.ParameterSymbol) and symbol.type == ast.ParameterType.ATOM:
            return f'parameters_->atom()->parameter(atom::{symbol.name})({node.indices[0].val})'

        if isinstance(symbol, symboltable.ParameterSymbol) and symbol.type == ast.ParameterType.BOND:
            if len(node.indices) == 1:
                return f'parameters_->bond()->parameter(bond::{symbol.name})({node.indices[0].val})'
            else:
                raise NotImplementedError('Only single indexing implemented')
        if isinstance(symbol, symboltable.SubstitutionSymbol):
            indices = ', '.join(f'{self.visit(idx)}' for idx in node.indices)
            return f'{symbol.name}({indices})'
        if isinstance(symbol, symboltable.FunctionSymbol):
            if symbol.function.name == 'distance':
                indices = ', '.join(f'{self.visit(idx)}' for idx in node.indices)
                return f'geometry.distance({indices})'
            if symbol.function.name == 'vdw_radius':
                name = self.visit(node.indices[0])
                return f'{name}.element.vdw_radius'

            raise NotImplementedError(f'Can\' translate function {symbol.function.name}')

        raise NotImplementedError(f'Unknown symbol type {symbol}')

    def visit_RelOp(self, node: ast.RelOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value
        return f'{lhs} {op} {rhs}'

    def visit_BinaryLogicalOp(self, node: ast.BinaryLogicalOp) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)
        op = node.op.value.lower()
        return f'{lhs} {op} {rhs}'

    def visit_UnaryLogicalOp(self, node: ast.UnaryLogicalOp) -> str:
        expr = self.visit(node.constraint)
        return f'{node.op.value.lower()} {expr}'

    def visit_Predicate(self, node: ast.Predicate) -> str:
        arg_list = [str(self.visit(arg)) for arg in node.args]
        args = ', '.join(arg_list)
        if node.name == 'bonded':
            return f'molecule.bonded({args})'
        if node.name == 'element':
            return f'{arg_list[0]}.element().name() == "{arg_list[1]}"'

        return f'{node.name}({args})'

    def visit_Sum(self, node: ast.Sum) -> str:
        template = '''\
double {method_name}::{name}({args}) const {{
    double total = 0;
    for(const auto &{obj}: molecule.{kind}s()) {{
        if({cond}) {{
            total += {expr};
        }}
    }}
    return total;
}}'''
        fname = f'sum_{self.sum_count}'
        obj = self.visit_Name(node.name)
        self.sum_count += 1
        expr = self.visit(node.expr)
        names = ast.NameGetter.visit(node.expr) - {obj}
        needed_names = []
        needed_names_plain = []
        for name in names:
            if self.symbol_table.resolve(name) is None:
                symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(name)
                if isinstance(symbol, symboltable.VariableSymbol):
                    if len(symbol.types) > 0:
                        needed_names.append(f'std::vector<double> &{name}')
                    else:
                        needed_names.append(f'double {name}')
                elif isinstance(symbol, symboltable.ObjectSymbol):
                    if symbol.type == ast.ObjectType.ATOM:
                        needed_names.append(f'const Atom &{name}')
                    else:
                        needed_names.append(f'const Bond &{name}')

                needed_names_plain.append(name)

        args = ', '.join(['molecule'] + needed_names_plain)
        f_args = ', '.join(['const Molecule &molecule'] + needed_names)
        symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(obj)
        old = self.resolving_node
        self.resolving_node = node
        if symbol.constraints is not None:
            cond = str(self.visit(symbol.constraints))
        else:
            cond = ''
        self.resolving_node = old
        kind = symbol.kind.value.lower()
        self.prototypes.append(f'double {fname}({f_args}) const;')
        self.definitions.append(
            template.format(method_name=self.method_name, name=fname, obj=obj, args=f_args, kind=kind, cond=cond,
                            expr=expr))
        return f'{fname}({args})'
