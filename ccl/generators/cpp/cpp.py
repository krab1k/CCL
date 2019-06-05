import os
import subprocess
from typing import Set, Dict

from ccl import ast, symboltable

__all__ = ['Cpp']

with open('ccl/generators/cpp/templates/method.h') as f:
    header_template = f.read()

with open('ccl/generators/cpp/templates/method.cpp') as f:
    method_template = f.read()

with open('ccl/generators/cpp/templates/CMakeLists.txt') as f:
    cmake_template = f.read()

sys_include_template = '#include <{file}>'

for_template = '''\
for (int {i} = {init}; {i} <= {to}; {i}++) {{
{code}
}}
'''

for_each_template = '''\
for (const auto &{name}: {objects}) {{
{atom_specs}
{code}
}}
'''


functions = {
    'electronegativity': 'electronegativity',
    'covalent radius': 'covalent_radius',
    'van der waals radius': 'vdw_radius',
    'hardness': 'hardness',
    'ionization potential': 'ionization_potential',
    'electron affinity': 'electron_affinity',
    'atomic number': 'Z',
    'valence electron count': 'valence_electron_count',
    'formal charge': 'formal_charge',
    'order': 'order'
}


class Cpp(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable, **kwargs):
        self.symbol_table: symboltable.SymbolTable = symbol_table
        if 'output_dir' in kwargs:
            self.output_dir: str = kwargs['output_dir']
        else:
            raise Exception('No output dir provided')

        self.format_code: bool = kwargs['format_code'] if 'format_code' in kwargs else False

        self.sys_includes: Set[str] = set()
        self.var_definitions: Dict[str, str] = {}
        self.var_free: Set[str] = set()

    def visit_Method(self, node: ast.Method) -> None:

        code = []
        for statement in node.statements:
            code.append(self.visit(statement))

        sys_includes = []
        for file in self.sys_includes:
            sys_includes.append(sys_include_template.format(file=file))
        sys_include_str = '\n'.join(sys_includes)

        code_str = '\n'.join(code)

        defs_str = ''

        var_defs_str = '\n'.join(var_def for var_def in self.var_definitions.values())

        var_free_str = '\n'.join(f'mkl_free(_{var});' for var in self.var_free)

        method = method_template.format(method_name=node.name.capitalize(),
                                        sys_includes=sys_include_str,
                                        defs=defs_str,
                                        var_definitions=var_defs_str,
                                        code=code_str,
                                        free=var_free_str)

        atom_parameters = []
        bond_parameters = []
        common_parameters = []

        for name, symbol in self.symbol_table.symbols.items():
            if isinstance(symbol, symboltable.ParameterSymbol):
                if symbol.type == ast.ParameterType.ATOM:
                    atom_parameters.append(name)
                elif symbol.type == ast.ParameterType.BOND:
                    bond_parameters.append(name)
                else:
                    common_parameters.append(name)

        atom_parameters_enum_str = ''
        atom_parameters_str = ''
        bond_parameters_enum_str = ''
        bond_parameters_str = ''
        common_parameters_enum_str = ''
        common_parameters_str = ''
        if atom_parameters:
            atom_parameters_enum_str = 'enum atom{{{ap_spec}}};'.format(ap_spec=', '.join(atom_parameters))
            atom_parameters_str = ', '.join(f'"{par}"' for par in atom_parameters)

        if bond_parameters:
            bond_parameters_enum_str = 'enum bond{{{bp_spec}}};'.format(bp_spec=', '.join(bond_parameters))
            bond_parameters_str = ', '.join(f'"{par}"' for par in bond_parameters)

        if common_parameters:
            common_parameters_enum_str = 'enum common{{{cp_spec}}};'.format(cp_spec=', '.join(common_parameters))
            common_parameters_str = ', '.join(f'"{par}"' for par in common_parameters)

        prototypes_str = ''

        header = header_template.format(method_name=node.name.capitalize(),
                                        common_parameters_enum=common_parameters_enum_str,
                                        atom_parameters_enum=atom_parameters_enum_str,
                                        bond_parameters_enum=bond_parameters_enum_str,
                                        common_parameters=common_parameters_str,
                                        atom_parameters=atom_parameters_str,
                                        bond_parameters=bond_parameters_str,
                                        prototypes=prototypes_str)

        with open(os.path.join(self.output_dir, 'ccl_method.cpp'), 'w') as f:
            f.write(method)

        with open(os.path.join(self.output_dir, 'ccl_method.h'), 'w') as f:
            f.write(header)

        with open(os.path.join(self.output_dir, 'CMakeLists.txt'), 'w') as f:
            f.write(cmake_template.format(method_name=node.name))

        for file in ['ccl_method.cpp', 'ccl_method.h']:
            args = ['clang-format', '-i', os.path.join(self.output_dir, file)]
            subprocess.run(args)

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        table = symboltable.SymbolTable.get_table_for_node(node)
        name = node.lhs.val if isinstance(node.lhs, ast.Name) else node.lhs.name.val
        symbol = table.resolve(name)
        if symbol.name not in self.var_definitions:
            if symbol.type == ast.NumericType.INT:
                definition = f'int _{symbol.name} = 0;'
            elif symbol.type == ast.NumericType.FLOAT:
                definition = f'double _{symbol.name} = 0.0;'
            else:  # ast.ArrayType
                self.sys_includes.add('mkl.h')
                sizes = ' * '.join('n' if t == ast.ObjectType.ATOM else 'm' for t in symbol.type.indices)
                definition = f'auto *_{symbol.name} = static_cast<double *>(mkl_calloc({sizes}, sizeof(double), 64));'
                self.var_free.add(symbol.name)

            self.var_definitions[symbol.name] = definition

        # TODO Assign number to array
        return f'{lhs} = {rhs};'

    def visit_For(self, node: ast.For) -> str:
        code = []
        for statement in node.body:
            code.append(self.visit(statement))

        name = self.visit(node.name)
        code_str = '\n'.join(code)
        return for_template.format(i=name, init=node.value_from.val, to=node.value_to.val, code=code_str)

    def visit_ForEach(self, node: ast.ForEach) -> str:
        code = []
        for statement in node.body:
            code.append(self.visit(statement))

        code_str = '\n'.join(code)

        type_str = node.type.value.lower()

        # TODO handle constraints
        if node.constraints is None:
            objects_str = f'molecule.{type_str}s()'
        else:
            raise NotImplementedError('Constraints are not implemented.')

        atom_specs_str = ''
        name = self.visit(node.name)
        if node.atom_indices is not None:
            atom_specs_str = f'const auto &_{node.atom_indices[0]} = {name}.first();\n' \
                             f'const auto &_{node.atom_indices[1]} = {name}.second();\n'

        return for_each_template.format(name=name,
                                        objects=objects_str,
                                        atom_specs=atom_specs_str,
                                        code=code_str)

    def visit_BinaryOp(self, node: ast.BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.left.result_type, ast.NumericType) and isinstance(node.right.result_type, ast.NumericType):
            if node.op == ast.BinaryOp.Ops.POW:
                self.sys_includes.add('cmath')
                return f'pow({left}, {right})'
            else:
                if not ast.is_atom(node.left):
                    left = f'({left})'
                if not ast.is_atom(node.right):
                    right = f'({right})'
                return f'{left} {node.op.value} {right}'

        # TODO matrix and vector operations
        return ''

    @staticmethod
    def visit_Name(node: ast.Name) -> str:
        return f'_{node.val}'

    @staticmethod
    def visit_Number(node: ast.Number) -> str:
        return f'{node.val}'

    def visit_Subscript(self, node: ast.Subscript) -> str:
        name = node.name.val
        table = symboltable.SymbolTable.get_table_for_node(node)
        symbol = table.resolve(name)
        if isinstance(symbol, symboltable.ParameterSymbol):
            if symbol.type == ast.ParameterType.ATOM:
                idx = self.visit(node.indices[0])
                return f'parameters_->atom()->parameter(atom::{name})({idx})'
            else:  # ast.ParameterType.BOND
                if len(node.indices) == 1:
                    idx = self.visit(node.indices[0])
                    return f'parameters_->bond()->parameter(bond::{name})({idx})'
                else:  # == 2
                    # TODO bond indexing by two atoms
                    return ''
        elif isinstance(symbol, symboltable.VariableSymbol):
            if len(node.indices) == 1:
                idx = self.visit(node.indices[0])
                return f'_{name}[{idx}.index()]'
            else:  # == 2
                idx1 = self.visit(node.indices[0])
                idx2 = self.visit(node.indices[1])
                s1 = table.resolve(node.indices[1].val)
                if s1.type == ast.ObjectType.ATOM:
                    col_size = 'n'
                else:  # ast.ObjectType.BOND
                    col_size = 'm'
                return f'_{name}[ {idx1}.index() * {col_size} + {idx2}.index()]'
        elif isinstance(symbol, symboltable.SubstitutionSymbol):
            # TODO substitution symbols
            return ''
        elif isinstance(symbol, symboltable.FunctionSymbol):
            fname = symbol.function.name
            if fname in symboltable.ELEMENT_PROPERTIES:
                idx = self.visit(node.indices[0])
                return f'{idx}.element().{functions[fname]}()'
            elif fname in {'formal charge', 'order'}:
                idx = self.visit(node.indices[0])
                return f'{idx}.{functions[fname]}()'

        raise Exception('Should not get here')
