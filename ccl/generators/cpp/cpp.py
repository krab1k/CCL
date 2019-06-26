import os
import subprocess
from typing import Set, Dict, List, Optional

from ccl import ast, symboltable
from ccl.types import *
from ccl.functions import ELEMENT_PROPERTIES

__all__ = ['Cpp']

with open('ccl/generators/cpp/templates/method.h') as template_f:
    header_template = template_f.read()

with open('ccl/generators/cpp/templates/method.cpp') as template_f:
    method_template = template_f.read()

with open('ccl/generators/cpp/templates/CMakeLists.txt') as template_f:
    cmake_template = template_f.read()

sys_include_template = '#include <{file}>'

user_include_template = '#include "{file}"'

for_template = '''\
for (int {i} = {init}; {i} <= {to}; {i}++) {{
    {code}
}}
'''

constraint_template = '''\
if ({constraint}) {{
    {code}
}}
'''

for_each_template = '''\
for (const auto &{name}: {objects}) {{
    {atom_specs}
    {code}
}}
'''

sum_template = '''\
double {method_name}::sum_{number}({args}) const {{
    double s = 0;
    for (const auto &_{name}: {objects}) {{
        {code}
    }}
    return s;
}}
'''

sum_prototype = 'double sum_{number}({args}) const;'

substitution_template = '''\
double {method_name}::{name}({args}) const {{
    {code}
}}
'''

substitution_prototype = 'double {name}({args}) const;'

ee_prototype = 'Eigen::VectorXd ee_{number}({args}) const;'

ee_template = '''\
Eigen::VectorXd {method_name}::ee_{number}({args}) const {{
    auto n = static_cast<int>(molecule.atoms().size());
    Eigen::VectorXd b = Eigen::VectorXd::Zero(n + 1);
    Eigen::MatrixXd A = Eigen::MatrixXd::Zero(n + 1, n + 1);
    
    for (const auto &_{idx_row}: molecule.atoms()) {{
        size_t {idx_row} = _{idx_row}.index();
        b({idx_row}) = {rhs};
        for (const auto &_{idx_col}: molecule.atoms()) {{
            size_t {idx_col} = _{idx_col}.index();
            if ({idx_row} == {idx_col}) {{
                A({idx_row}, {idx_row}) = {diag};
            }} else {{
                A({idx_row}, {idx_col}) = {off};
            }}
        }}
    }}
    
    b(n) = molecule.total_charge();
    A.row(n) = Eigen::VectorXd::Constant(n + 1, 1.0);
    A.col(n) = Eigen::VectorXd::Constant(n + 1, 1.0);
    A(n, n) = 0.0;
    
    return A.partialPivLu().solve(b).head(n);
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
    'bond order': 'order',
    'distance': 'distance'
}


class Cpp(ast.ASTVisitor):
    def __init__(self, symbol_table: symboltable.SymbolTable, **kwargs):
        self.symbol_table: symboltable.SymbolTable = symbol_table

        self.output_dir: Optional[str] = kwargs.get('output_dir', None)
        self.format_code: bool = kwargs.get('format_code', True)

        self.sys_includes: Set[str] = set()
        self.user_includes: Set[str] = set()
        self.var_definitions: Dict[str, str] = {}
        self.method_name: str = ''

        self.defs: List[str] = []
        self.prototypes: List[str] = []
        self.sum_count: int = 0
        self.ee_count: int = 0

        self.required_features: Set[str] = set()

        self.substitutions_needing_q: Set[str] = set()

    def define_substitutions(self):
        table = self.symbol_table.parent
        for name, symbol in table.symbols.items():
            if isinstance(symbol, symboltable.SubstitutionSymbol):
                if not symbol.indices:
                    args = ''
                    expr = self.visit(symbol.rules[None])
                    code = f'return {expr};'
                else:
                    # TODO handle bonds
                    args = ','.join(('const Molecule &molecule',
                                     *(f'const Atom &_{name.val}' for name in symbol.indices)))

                    # Check whether we have to add q as an argument
                    required_names: Set[str] = set()
                    for cond, expr in symbol.rules.items():
                        if cond is not None:
                            required_names |= symboltable.NameGetter.visit(cond, self.symbol_table)
                        required_names |= symboltable.NameGetter.visit(expr, self.symbol_table)

                    if 'q' in required_names:
                        self.substitutions_needing_q.add(name)
                        args += ', const Eigen::VectorXd _q'

                    if len(symbol.rules) == 1:
                        expr = self.visit(symbol.rules[None])
                        code = f'return {expr};'
                    else:
                        code = ''
                        for cond, expr in symbol.rules.items():
                            if cond is None:
                                # Handle default case as the last one
                                continue

                            cond_str = self.visit(cond)
                            expr_str = self.visit(expr)

                            code += f'if ({cond_str}) {{ return {expr_str}; }} else '

                        expr_str = self.visit(symbol.rules[None])

                        code += f'{{ return {expr_str}; }}'

                self.prototypes.append(substitution_prototype.format(name=name,
                                                                     args=args))

                self.defs.append(substitution_template.format(method_name=self.method_name,
                                                              name=name,
                                                              args=args,
                                                              code=code))

    def visit_Method(self, node: ast.Method) -> str:

        self.method_name = node.name.capitalize()

        self.define_substitutions()

        code = []
        for statement in node.statements:
            code.append(self.visit(statement))

        sys_includes = [sys_include_template.format(file=file) for file in self.sys_includes]
        sys_include_str = '\n'.join(sys_includes)

        user_includes = [user_include_template.format(file=file) for file in self.user_includes]
        user_include_str = '\n'.join(user_includes)

        code_str = '\n'.join(code)

        defs_str = '\n'.join(self.defs)

        prototypes_str = '\n'.join(self.prototypes)

        var_defs_str = '\n'.join(var_def for var_def in self.var_definitions.values())

        method = method_template.format(method_name=self.method_name,
                                        sys_includes=sys_include_str,
                                        user_includes=user_include_str,
                                        defs=defs_str,
                                        var_definitions=var_defs_str,
                                        code=code_str)

        atom_parameters = []
        bond_parameters = []
        common_parameters = []

        assert self.symbol_table.parent is not None

        for name, symbol in self.symbol_table.parent.symbols.items():
            if isinstance(symbol, symboltable.ParameterSymbol):
                if symbol.type == ParameterType.ATOM:
                    atom_parameters.append(name)
                elif symbol.type == ParameterType.BOND:
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

        required_features_str = ', '.join(self.required_features)

        header = header_template.format(method_name=node.name.capitalize(),
                                        common_parameters_enum=common_parameters_enum_str,
                                        atom_parameters_enum=atom_parameters_enum_str,
                                        bond_parameters_enum=bond_parameters_enum_str,
                                        common_parameters=common_parameters_str,
                                        atom_parameters=atom_parameters_str,
                                        bond_parameters=bond_parameters_str,
                                        prototypes=prototypes_str,
                                        required_features=required_features_str)

        if self.format_code:
            args = ['clang-format', '-style={ColumnLimit: 120}']
            p = subprocess.run(args, input=header.encode('ascii'), stdout=subprocess.PIPE)
            header = p.stdout.decode('ascii')
            p = subprocess.run(args, input=method.encode('ascii'), stdout=subprocess.PIPE)
            method = p.stdout.decode('ascii')

        if self.output_dir is not None:
            with open(os.path.join(self.output_dir, 'ccl_method.cpp'), 'w') as f:
                f.write(method)

            with open(os.path.join(self.output_dir, 'ccl_method.h'), 'w') as f:
                f.write(header)

            with open(os.path.join(self.output_dir, 'CMakeLists.txt'), 'w') as f:
                f.write(cmake_template.format(method_name=node.name))

        return f'// ccl_method.h\n\n{header}\n// ccl_method.cpp\n\n{method}'

    def visit_Assign(self, node: ast.Assign) -> str:
        lhs = self.visit(node.lhs)
        rhs = self.visit(node.rhs)

        table = symboltable.SymbolTable.get_table_for_node(node)
        name = node.lhs.val if isinstance(node.lhs, ast.Name) else node.lhs.name.val
        symbol = table.resolve(name)
        if symbol.name not in self.var_definitions:
            if symbol.type == NumericType.INT:
                definition = f'int _{symbol.name} = 0;'
            elif symbol.type == NumericType.FLOAT:
                definition = f'double _{symbol.name} = 0.0;'
            else:  # ArrayType
                sizes = ', '.join('n' if t == ObjectType.ATOM else 'm' for t in symbol.type.indices)
                if len(symbol.type.indices) == 1:
                    var_type = 'VectorXd'
                else:
                    var_type = 'MatrixXd'
                definition = f'Eigen::{var_type} _{symbol.name} = Eigen::{var_type}::Zero({sizes});'

            self.var_definitions[symbol.name] = definition

        if isinstance(node.lhs, ast.Name) and isinstance(symbol.type, ArrayType) and \
                isinstance(node.rhs.result_type, NumericType):
            return f'{lhs}.fill({rhs});'
        else:
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

        objects_str = f'molecule.{node.type.value.lower()}s()'
        name = self.visit(node.name)

        if node.constraints is not None:
            code_str = constraint_template.format(constraint=self.visit(node.constraints),
                                                  code=code_str)
        atom_specs_str = ''

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

        if isinstance(node.left.result_type, NumericType) and isinstance(node.right.result_type, NumericType):
            if node.op == ast.BinaryOp.Ops.POW:
                self.sys_includes.add('cmath')
                return f'pow({left}, {right})'

        if not ast.is_atom(node.left):
            left = f'({left})'

        if not ast.is_atom(node.right):
            right = f'({right})'

        if isinstance(node.right.result_type, ArrayType) and isinstance(node.left.result_type, ArrayType) and \
                node.left.result_type.dim() == 1 and node.op == ast.BinaryOp.Ops.MUL:
            left = f'{left}.transpose()'

        return f'{left} {node.op.value} {right}'

    def visit_Name(self, node: ast.Name) -> str:
        symbol = self.symbol_table.resolve(node.val)
        if symbol is not None:
            if isinstance(symbol, symboltable.ConstantSymbol):
                self.user_includes.add('periodic_table.h')
                fname = functions[symbol.property.name]
                return f'PeriodicTable::pte().get_element_by_name("{symbol.element.capitalize()}")->{fname}()'
            elif isinstance(symbol, symboltable.ParameterSymbol):
                return f'parameters_->common()->parameter(common::{node.val})'

        return f'_{node.val}'

    @staticmethod
    def visit_Number(node: ast.Number) -> str:
        return f'{node.val}'

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        return f'{node.op.value} ({self.visit(node.expr)})'

    def visit_Subscript(self, node: ast.Subscript) -> str:
        name = node.name.val
        table = symboltable.SymbolTable.get_table_for_node(node)
        symbol = table.resolve(name)
        if isinstance(symbol, symboltable.ParameterSymbol):
            self.user_includes.add('parameters.h')
            if symbol.type == ParameterType.ATOM:
                idx = self.visit(node.indices[0])
                return f'parameters_->atom()->parameter(atom::{name})({idx})'
            else:  # ParameterType.BOND
                if len(node.indices) == 1:
                    idx = self.visit(node.indices[0])
                    return f'parameters_->bond()->parameter(bond::{name})({idx})'
                else:  # == 2
                    idx1 = self.visit(node.indices[0])
                    idx2 = self.visit(node.indices[1])
                    return f'parameters_->bond()->parameter(bond::{name})(*molecule.get_bond({idx1}, {idx2}))'

        elif isinstance(symbol, symboltable.VariableSymbol):
            if len(node.indices) == 1:
                idx = self.visit(node.indices[0])
                return f'_{name}({idx}.index())'
            else:  # == 2
                idx1 = self.visit(node.indices[0])
                idx2 = self.visit(node.indices[1])
                return f'_{name}({idx1}.index(), {idx2}.index())'
        elif isinstance(symbol, symboltable.SubstitutionSymbol):
            args = ','.join(('molecule', *(f'_{name.val}' for name in node.indices)))
            if symbol.name in self.substitutions_needing_q:
                args += ', _q'
            return f'{symbol.name}({args})'
        elif isinstance(symbol, symboltable.FunctionSymbol):
            fname = symbol.function.name
            if fname in ELEMENT_PROPERTIES:
                idx = self.visit(node.indices[0])
                return f'{idx}.element().{functions[fname]}()'
            elif fname in {'formal charge', 'bond order'}:
                idx = self.visit(node.indices[0])
                return f'{idx}.{functions[fname]}()'
            elif fname == 'distance':
                self.user_includes.add('geometry.h')
                idx1 = self.visit(node.indices[0])
                idx2 = self.visit(node.indices[1])
                return f'{functions[fname]}({idx1}, {idx2})'
            else:
                raise NotImplementedError(f'Unknown function: {fname}')

        raise Exception('Should not get here')

    def visit_Sum(self, node: ast.Sum) -> str:
        number = self.sum_count
        self.sum_count += 1

        object_name = node.name.val

        used_names: Set[str] = set()
        used_names |= symboltable.NameGetter().visit(node.expr, self.symbol_table)

        assert self.symbol_table.parent is not None
        symbol = self.symbol_table.parent.resolve(object_name)

        assert symbol is not None
        assert isinstance(symbol, symboltable.ObjectSymbol)

        expr_str = self.visit(node.expr)

        if symbol.constraints is not None:
            used_names |= symboltable.NameGetter().visit(symbol.constraints, self.symbol_table)
            code = constraint_template.format(constraint=self.visit(symbol.constraints),
                                              code=f's += {expr_str};')
        else:
            code = f's += {expr_str};'

        types = {
            NumericType.INT: 'int',
            NumericType.FLOAT: 'double',
            ObjectType.ATOM: 'const Atom &',
            ObjectType.BOND: 'const Bond &',
        }

        formal_args = ['const Molecule &molecule']
        args = ['molecule']

        for name in used_names:
            s = self.symbol_table.parent.resolve(name)
            if s is None:
                local_symbol = symboltable.SymbolTable.get_table_for_node(node).resolve(name)
                if isinstance(local_symbol.type, ArrayType):
                    type_str = 'const Eigen::MatrixXd &'
                else:
                    type_str = types[local_symbol.type]

                formal_args.append(f'{type_str} _{name}')
                args.append(f'_{name}')

        if 'q' in used_names:
            formal_args.append('const Eigen::VectorXd _q')
            args.append('_q')

        formal_args_str = ', '.join(formal_args)
        args_str = ', '.join(args)

        if symbol.type == ObjectType.ATOM:
            objects = 'molecule.atoms()'
        else:  # ObjectType.BOND:
            objects = 'molecule.bonds()'

        self.prototypes.append(sum_prototype.format(number=number,
                                                    args=formal_args_str))

        self.defs.append(sum_template.format(number=number,
                                             args=formal_args_str,
                                             method_name=self.method_name,
                                             objects=objects,
                                             name=object_name,
                                             code=code
                                             ))

        return f'sum_{number}({args_str})'

    def visit_Predicate(self, node: ast.Predicate) -> str:
        if node.name == 'element':
            return f'_{node.args[0].val}.element().name() == "{node.args[1].val.capitalize()}"'
        elif node.name == 'near':
            return f'distance(_{node.args[0].val}, _{node.args[1].val}) < {node.args[2].val}'
        elif node.name == 'bonded':
            self.required_features.add('RequiredFeatures::BOND_INFO')
            return f'molecule.bonded(_{node.args[0].val}, _{node.args[1].val})'
        elif node.name == 'bond_distance':
            self.required_features.add('RequiredFeatures::BOND_DISTANCES')
            return f'molecule.bond_distance(_{node.args[0].val}, _{node.args[1].val}) == {node.args[2].val}'

        raise RuntimeError('We should not get here')

    def visit_BinaryLogicalOp(self, node: ast.BinaryLogicalOp) -> str:
        return f'({self.visit(node.lhs)}) {node.op.value.lower()} ({self.visit(node.rhs)})'

    def visit_RelOp(self, node: ast.RelOp) -> str:
        return f'({self.visit(node.lhs)}) {node.op.value} ({self.visit(node.rhs)})'

    def visit_UnaryLogicalOp(self, node: ast.UnaryLogicalOp) -> str:
        return f'{node.op.value.lower()} ({self.visit(node.constraint)})'

    def visit_EE(self, node: ast.EE) -> str:
        number = self.ee_count
        self.ee_count += 1

        off_expr = self.visit(node.off)
        diag_expr = self.visit(node.diag)
        rhs_expr = self.visit(node.rhs)

        args_str = 'molecule'
        formal_args_str = 'const Molecule &molecule'

        self.defs.append(ee_template.format(method_name=self.method_name,
                                            number=number,
                                            idx_row=node.idx_row,
                                            idx_col=node.idx_col,
                                            diag=diag_expr,
                                            off=off_expr,
                                            rhs=rhs_expr,
                                            args=formal_args_str))

        self.prototypes.append(ee_prototype.format(number=number,
                                                   args=formal_args_str))

        return f'ee_{number}({args_str})'

    def visit_Function(self, node: ast.Function) -> str:
        arg = self.visit(node.arg)
        if node.name == 'inv':
            return f'{arg}.inverse()'
        else:
            self.sys_includes.add('cmath')
            return f'{node.name}({arg})'
