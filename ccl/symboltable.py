"""CCC's implementation of a symbol table"""

from typing import Dict, Tuple, Optional, Union, Set
from abc import ABC, abstractmethod

from ccl import ast
from ccl.errors import CCLSymbolError, CCLTypeError


class Function:
    def __init__(self, name: str, fn_type: ast.FunctionType) -> None:
        self.name: str = name
        self.type: ast.FunctionType = fn_type

    def __str__(self) -> str:
        return f'{self.name}: {self.type}'


FUNCTIONS = {}

# Add common math functions
MATH_FUNCTIONS_NAMES = ['exp', 'sqrt', 'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh']
for fn in MATH_FUNCTIONS_NAMES:
    FUNCTIONS[fn] = Function(fn, ast.FunctionType(ast.NumericType.FLOAT, ast.NumericType.FLOAT))

FUNCTIONS['inv'] = Function('inv', ast.FunctionType(ast.ArrayType(ast.ObjectType.ATOM, ast.ObjectType.ATOM),
                                                    ast.ArrayType(ast.ObjectType.ATOM, ast.ObjectType.ATOM)))

# Add atom properties
for prop in ['electronegativity', 'covalent radius', 'van der waals radius', 'hardness', 'ionization potential',
             'electron affinity']:
    FUNCTIONS[prop] = Function(prop, ast.FunctionType(ast.NumericType.FLOAT, ast.ObjectType.ATOM))

for prop in ['atomic number', 'valence electron count']:
    FUNCTIONS[prop] = Function(prop, ast.FunctionType(ast.NumericType.INT, ast.ObjectType.ATOM))

# Add bond properties
FUNCTIONS['order'] = Function('order', ast.FunctionType(ast.NumericType.INT, ast.ObjectType.BOND))


# Add custom functions
FUNCTIONS['formal charge'] = Function('formal charge', ast.FunctionType(ast.NumericType.INT, ast.ObjectType.ATOM))
FUNCTIONS['distance'] = Function('distance',
                                 ast.FunctionType(ast.NumericType.FLOAT, ast.ObjectType.ATOM, ast.ObjectType.ATOM))

PREDICATES = {'element': Function('element', ast.PredicateType(ast.ObjectType.ATOM, ast.StringType())),
              'bonded': Function('bonded', ast.PredicateType(ast.ObjectType.ATOM, ast.ObjectType.ATOM)),
              'near': Function('near',
                               ast.PredicateType(ast.ObjectType.ATOM, ast.ObjectType.ATOM, ast.NumericType.FLOAT)),
              'bond_distance': Function('bond_distance',
                                        ast.PredicateType(ast.ObjectType.ATOM, ast.ObjectType.ATOM,
                                                          ast.NumericType.INT))}

# TODO Sum functions (inv, distance,..) may use something like ObjectType.ANY


class Symbol(ABC):
    @abstractmethod
    def __init__(self, name: str, def_node: Optional[ast.ASTNode]) -> None:
        self.name: str = name
        self.def_node: Optional[ast.ASTNode] = def_node

    @abstractmethod
    def symbol_type(self) -> Union[ast.NumericType, ast.ArrayType, ast.ObjectType, ast.ArrayType, ast.ParameterType]:
        pass


class ParameterSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, ptype: ast.ParameterType) -> None:
        super().__init__(name, def_node)
        self.type: ast.ParameterType = ptype

    def __repr__(self) -> str:
        return f'ParameterSymbol({self.name}, {self.type})'

    def symbol_type(self) -> Union[ast.ParameterType, ast.NumericType]:
        if self.type == ast.ParameterType.COMMON:
            return ast.NumericType.FLOAT

        return self.type


class ObjectSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, otype: ast.ObjectType,
                 constraints: Optional[ast.Constraint]) -> None:
        super().__init__(name, def_node)
        self.type: ast.ObjectType = otype
        self.constraints: Optional[ast.Constraint] = constraints

    def __repr__(self) -> str:
        return f'ObjectSymbol({self.name}, {self.type}, {self.constraints})'

    def symbol_type(self) -> ast.ObjectType:
        return self.type


class FunctionSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ast.ASTNode], f: Function) -> None:
        super().__init__(name, def_node)
        self.function: Function = f

    def __repr__(self) -> str:
        return f'FunctionSymbol({self.name}, {self.function})'

    def symbol_type(self) -> ast.FunctionType:
        return self.function.type


class VariableSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ast.ASTNode],
                 vtype: Union[ast.NumericType, ast.ArrayType]) -> None:
        super().__init__(name, def_node)
        self.type: Union[ast.NumericType, ast.ArrayType] = vtype

    def __repr__(self) -> str:
        return f'VariableSymbol({self.name}, {self.type})'

    def symbol_type(self) -> Union[ast.NumericType, ast.ArrayType]:
        return self.type


class SubstitutionSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, indices: Tuple[ast.Name, ...]) -> None:
        super().__init__(name, def_node)
        self.indices: Tuple[ast.Name, ...] = indices
        self.rules: Dict[Optional[ast.Constraint], ast.Expression] = {}

    def __repr__(self) -> str:
        return f'SubstitutionSymbol({self.name}, {self.indices})'

    def symbol_type(self) -> Union[ast.NumericType, ast.ArrayType, ast.ObjectType, ast.ArrayType, ast.ParameterType]:
        # All the expressions must have same type, so pick the default one
        return self.rules[None].result_type


class ConstantSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, f: Function, element: str):
        super().__init__(name, def_node)
        self.property: Function = f
        self.element: str = element

    def __repr__(self) -> str:
        return f'ConstantSymbol({self.name}, {self.property}, {self.element})'

    def symbol_type(self) -> ast.NumericType:
        return self.property.type.return_type


class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable']) -> None:
        self.parent: Optional['SymbolTable'] = parent
        self.symbols: Dict[str, Symbol] = {}

    def __repr__(self) -> str:
        return 'SymbolTable'

    def resolve(self, s: str) -> Optional[Symbol]:
        if s in self.symbols:
            return self.symbols[s]

        if self.parent is not None:
            return self.parent.resolve(s)

        return None

    def define(self, symbol: Symbol) -> None:
        if self.resolve(symbol.name):
            raise CCLSymbolError(symbol.def_node, f'Symbol {symbol.name} already defined.')

        self.symbols[symbol.name] = symbol

    def print(self) -> None:
        for symbol in self.symbols.values():
            print(symbol)

    @classmethod
    def create_from_ast(cls, node: ast.Method) -> 'SymbolTable':
        visitor = SymbolTableBuilder()
        visitor.visit(node)
        return visitor.symbol_table


# noinspection PyPep8Naming
class SymbolTableBuilder(ast.ASTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.global_table: SymbolTable = SymbolTable(None)
        self.symbol_table: SymbolTable = SymbolTable(self.global_table)
        self.current_table: SymbolTable = self.symbol_table

        self._iterating_over: Set[str] = set()
        self._indices_mapping: Dict[str, str] = {}

        # Add math function names to the global table
        for fn_name in MATH_FUNCTIONS_NAMES:
            self.global_table.define(FunctionSymbol(fn_name, None, FUNCTIONS[fn_name]))

        # q is always a vector of charges
        self.global_table.define(VariableSymbol('q', None, ast.ArrayType(ast.ObjectType.ATOM, )))

    @property
    def iterating_over(self) -> Set[str]:
        return {self._indices_mapping.get(i, i) for i in self._iterating_over}

    def visit_Method(self, node: ast.Method) -> None:
        node.symbol_table = self.current_table
        for annotation in node.annotations:
            self.visit(annotation)

        for statement in node.statements:
            self.visit(statement)

    def visit_Parameter(self, node: ast.Parameter) -> None:
        self.current_table.define(ParameterSymbol(node.name, node, node.type))

    def visit_Object(self, node: ast.Object) -> None:
        if node.atom_indices is not None:
            i1, i2 = node.atom_indices
            s1 = self.current_table.resolve(i1)
            s2 = self.current_table.resolve(i2)
            if s1 is not None or s2 is not None:
                raise CCLSymbolError(node, f'Decomposition of bond symbol {node.name} used already defined names.')

            self.current_table.define(ObjectSymbol(i1, node, ast.ObjectType.ATOM, None))
            self.current_table.define(ObjectSymbol(i2, node, ast.ObjectType.ATOM, None))
        self.current_table.define(ObjectSymbol(node.name, node, node.type, node.constraints))

    def visit_Constant(self, node: ast.Constant) -> None:
        try:
            f = FUNCTIONS[node.prop]
        except KeyError:
            raise CCLSymbolError(node, f'Property {node.prop} is not known.')

        if len(f.type.args) != 1 or f.type.args[0] != ast.ObjectType.ATOM:
            raise CCLTypeError(node, f'Function {node.prop} is not a property')

        self.current_table.define(ConstantSymbol(node.name, node, f, node.element))

    def visit_Property(self, node: ast.Property) -> None:
        try:
            f = FUNCTIONS[node.prop]
        except KeyError:
            raise CCLSymbolError(node, f'Function {node.prop} is not known.')

        self.current_table.define(FunctionSymbol(node.name, node, f))

    def visit_Name(self, node: ast.Name) -> None:
        name = self._indices_mapping.get(node.val, node.val)
        s = self.current_table.resolve(name)
        if s is not None:
            if isinstance(s, SubstitutionSymbol):
                self.visit(s.rules[None])
            node.result_type = s.symbol_type()
        else:
            raise CCLSymbolError(node, f'Symbol {name} not defined.')

    def visit_Subscript(self, node: ast.Subscript) -> None:
        s = self.current_table.resolve(node.name.val)
        if not isinstance(s, SubstitutionSymbol):
            self.visit(node.name)

        symbol_type = node.name.result_type

        index_types = []
        for idx in node.indices:
            self.visit(idx)
            index_types.append(idx.result_type)
            mapped_val = self._indices_mapping.get(idx.val, idx.val)
            if isinstance(idx.result_type, ast.ObjectType) and \
                    mapped_val not in self.iterating_over:
                raise CCLSymbolError(idx, f'Object {mapped_val} not bound to any For/ForEach/Sum.')
        index_types = tuple(index_types)
        index_types_str = ', '.join(str(i) for i in index_types)

        if isinstance(s, ParameterSymbol):
            if symbol_type == ast.ParameterType.ATOM and index_types != (ast.ObjectType.ATOM,) or \
               (symbol_type == ast.ParameterType.BOND and
                    index_types not in [(ast.ObjectType.BOND,), (ast.ObjectType.ATOM, ast.ObjectType.ATOM)]):
                raise CCLTypeError(node, f'Cannot index parameter symbol of type {symbol_type} with {index_types_str}.')
        elif isinstance(s, VariableSymbol) and isinstance(symbol_type, ast.ArrayType):
            if symbol_type.indices != index_types:
                raise CCLTypeError(node, f'Cannot index Array of type {symbol_type} '
                                         f'using index/indices of type(s) {index_types_str}.')
        elif isinstance(s, FunctionSymbol):
            if symbol_type.args != index_types:
                raise CCLTypeError(node, f'Cannot use function {s.function.name}: {s.function.type} '
                                         f'with arguments of type(s) {index_types_str}')

            node.result_type = s.function.type.return_type
            return
        elif isinstance(s, SubstitutionSymbol):
            if len(s.indices) != len(index_types):
                raise CCLTypeError(node, f'Bad number of indices for {s.name}, got {len(index_types)}, '
                                         f'expected {len(s.indices)}.')
            if not all(isinstance(t, ast.ObjectType) for t in index_types):
                raise CCLTypeError(node, f'Substitution indices for symbol {s.name} must have type Atom or Bond.')

            self._indices_mapping.update({si.val: ni.val for si, ni in zip(s.indices, node.indices)})
            types = set()
            for constraint, expr in s.rules.items():
                if constraint is not None:
                    self.visit(constraint)
                self.visit(expr)
                types.add(expr.result_type)

            if len(types) > 1:
                raise CCLTypeError(node, f'All expressions within a substitution symbol {s.name} must have same type.')

            for si in s.indices:
                self._indices_mapping.pop(si.val)
        else:
            raise CCLTypeError(node, f'Cannot index type {symbol_type} with indices of type(s) {index_types_str}')

        # Return Float if not assigned already
        node.result_type = ast.NumericType.FLOAT

    def visit_Assign(self, node: ast.Assign) -> None:
        def check_types(lhs: ast.Type, rhs: ast.Type):
            if isinstance(lhs, ast.ArrayType) and isinstance(rhs, ast.ArrayType):
                return lhs == rhs
            # Can assign number to all elements of the vector/matrix
            if isinstance(lhs, ast.ArrayType) and isinstance(rhs, ast.NumericType):
                return True
            if isinstance(lhs, ast.NumericType) and isinstance(rhs, ast.NumericType):
                # Cannot assign Float to Int, OK otherwise
                if lhs == ast.NumericType.INT and rhs == ast.NumericType.FLOAT:
                    return False
                else:
                    return True

            return False

        self.visit(node.rhs)
        rtype = node.rhs.result_type
        if not isinstance(rtype, (ast.NumericType, ast.ArrayType)):
            raise CCLTypeError(node.rhs, f'Only Numbers and Arrays can be assigned not {rtype}.')
        if isinstance(node.lhs, ast.Name):
            s = self.current_table.resolve(node.lhs.val)
            if s is not None:
                if s.name in self._iterating_over:
                    raise CCLTypeError(node, f'Cannot assign to loop variable {s.name}.')
                if isinstance(s, SubstitutionSymbol):
                    raise CCLSymbolError(node.lhs, f'Cannot assign to a substitution symbol {s.name}.')
                if check_types(s.symbol_type(), rtype):
                    node.lhs.result_type = s.symbol_type()
                else:
                    raise CCLTypeError(node,
                                       f'Cannot assign {rtype} to the variable {s.name} of type {s.symbol_type()}.')
            else:
                # New symbols are defined at method scope
                self.symbol_table.define(VariableSymbol(node.lhs.val, node, rtype))
                node.lhs.result_type = rtype
        elif isinstance(node.lhs, ast.Subscript):  # ast.Subscript
            s = self.current_table.resolve(node.lhs.name.val)
            index_types = []
            for idx in node.lhs.indices:
                self.visit(idx)
                index_types.append(idx.result_type)
            if s is not None:
                # Check whether indices are correct
                if isinstance(s, SubstitutionSymbol):
                    raise CCLSymbolError(node.lhs, f'Cannot assign to a substitution symbol {s.name}.')
                if not isinstance(s.symbol_type(), ast.ArrayType):
                    raise CCLTypeError(node.lhs, f'Cannot assign to non Array type {s.symbol_type()}.')
                index_types = []
                for idx in node.lhs.indices:
                    self.visit(idx)
                    index_types.append(idx.result_type)
                if s.symbol_type().indices != tuple(index_types):
                    indices_str = ', '.join(str(i) for i in index_types)
                    raise CCLTypeError(node.lhs, f'Cannot index Array of type {s.symbol_type()} '
                                                 f'using index/indices of type(s) {indices_str}.')

                node.lhs.name.result_type = s.symbol_type()
            else:
                if not all(isinstance(i, ast.ObjectType) for i in index_types):
                    raise CCLTypeError(node.lhs, f'Cannot index with something different than Atom or Bond')
                self.symbol_table.define(VariableSymbol(node.lhs.name.val, node, ast.ArrayType(*index_types)))
                node.lhs.name.result_type = ast.ArrayType(*index_types)
            node.lhs.result_type = rtype
        else:
            raise Exception('Should not get here!')

    def visit_Function(self, node: ast.Function) -> None:
        # Functions have only one numerical argument
        def check_args(expected: ast.Type, given: ast.Type):
            if expected == given:
                return True
            elif given == ast.NumericType.INT and expected == ast.NumericType.FLOAT:
                return True

            return False

        self.visit(node.arg)

        try:
            f = FUNCTIONS[node.name]
        except KeyError:
            raise CCLSymbolError(node, f'Function {node.name} is not known.')

        if not check_args(f.type.args[0], node.arg.result_type):
            raise CCLTypeError(node.arg, f'Incompatible argument type for function {f.name}. '
                                         f'Got {node.arg.result_type}, expected {f.type.args[0]}')

        node.result_type = f.type.return_type

    def visit_BinaryOp(self, node: ast.BinaryOp) -> None:
        self.visit(node.left)
        self.visit(node.right)
        ltype = node.left.result_type
        rtype = node.right.result_type

        if isinstance(ltype, ast.NumericType) and isinstance(rtype, ast.NumericType):
            if ltype == ast.NumericType.FLOAT or rtype == ast.NumericType.FLOAT:
                node.result_type = ast.NumericType.FLOAT
            else:
                node.result_type = ast.NumericType.INT
        elif isinstance(ltype, ast.ArrayType) and isinstance(rtype, ast.ArrayType):
            if node.op in (ast.BinaryOp.Ops.ADD, ast.BinaryOp.Ops.SUB):
                if ltype.indices == rtype.indices:
                    node.result_type = ltype
                else:
                    raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')
            elif node.op == ast.BinaryOp.Ops.MUL:
                if ltype.dim() == rtype.dim() == 2:
                    if ltype.indices[1] != rtype.indices[0]:
                        raise CCLTypeError(node, f'Cannot multiply matrices of types {ltype} and {rtype}')
                    else:
                        node.result_type = ast.ArrayType(ltype.indices[0], rtype.indices[1])
                elif ltype.dim() == 1 and rtype.dim() == 2:
                    if ltype.indices[0] != rtype.indices[0]:
                        raise CCLTypeError(node, f'Cannot multiply vector of type {ltype} and matrix of type {rtype}')
                    else:
                        node.result_type = ast.ArrayType(rtype.indices[1])
                elif ltype.dim() == 2 and rtype.dim() == 1:
                    if ltype.indices[1] != rtype.indices[0]:
                        raise CCLTypeError(node, f'Cannot multiply matrix of type {ltype} with vector of type {rtype}')
                    else:
                        node.result_type = ast.ArrayType(ltype.indices[0])
                elif ltype.dim() == rtype.dim() == 1:
                    if ltype != rtype:
                        raise CCLTypeError(node, f'Cannot perform dot product of vectors of types {ltype} and {rtype}')
                    else:
                        node.result_type = ast.NumericType.FLOAT
            else:
                raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')
        #  One is Array, second Number
        elif isinstance(ltype, (ast.ArrayType, ast.NumericType)) and \
                isinstance(rtype, (ast.ArrayType, ast.NumericType)):
            if isinstance(ltype, ast.ArrayType):
                node.result_type = ltype
            else:
                node.result_type = rtype
        else:
            raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        self.visit(node.expr)
        node.result_type = node.expr.result_type

    def visit_For(self, node: ast.For) -> None:
        s = self.current_table.resolve(node.name.val)
        if s is not None:
            raise CCLSymbolError(node.name, f'Symbol {node.name.val} already defined.')

        self._iterating_over.add(node.name.val)
        table = SymbolTable(self.current_table)
        node.symbol_table = table
        table.define(VariableSymbol(node.name.val, node, ast.NumericType.INT))
        self.current_table = table
        for statement in node.body:
            self.visit(statement)

        self._iterating_over.remove(node.name.val)
        self.current_table = self.current_table.parent

    def visit_ForEach(self, node: ast.ForEach) -> None:
        s = self.current_table.resolve(node.name.val)
        if s is not None:
            raise CCLSymbolError(node.name, f'Symbol {node.name.val} already defined.')

        table = SymbolTable(self.current_table)

        atom_indices = set()
        if node.atom_indices is not None:
            i1, i2 = node.atom_indices
            s1 = self.current_table.resolve(i1)
            s2 = self.current_table.resolve(i2)
            if s1 is not None or s2 is not None:
                raise CCLSymbolError(node, f'Decomposition of bond symbol {node.name.val} used already defined names.')

            table.define(ObjectSymbol(i1, node, ast.ObjectType.ATOM, None))
            table.define(ObjectSymbol(i2, node, ast.ObjectType.ATOM, None))
            atom_indices = {i1, i2}

        self._iterating_over |= atom_indices | {node.name.val}

        node.symbol_table = table
        table.define(ObjectSymbol(node.name.val, node, node.type, node.constraints))
        self.current_table = table
        for statement in node.body:
            self.visit(statement)

        self._iterating_over -= atom_indices | {node.name.val}
        self.current_table = self.current_table.parent

    def visit_Sum(self, node: ast.Sum) -> None:
        s = self.current_table.resolve(node.name.val)
        if s is None:
            raise CCLSymbolError(node.name, f'Symbol {node.name.val} not defined.')

        node.name.result_type = s.symbol_type()

        if not isinstance(s, ObjectSymbol):
            raise CCLSymbolError(node.name, f'Sum has to iterate over Atom or Bond not {s.symbol_type()}.')

        self._iterating_over.add(node.name.val)
        if s.constraints is not None:
            self.visit(s.constraints)

        self.visit(node.expr)
        self._iterating_over.remove(node.name.val)
        node.result_type = node.expr.result_type

    def visit_EE(self, node: ast.EE) -> None:
        s1 = self.current_table.resolve(node.idx_row)
        s2 = self.current_table.resolve(node.idx_col)
        if s1 is not None or s2 is not None:
            raise CCLSymbolError(node, 'Index/indices for EE expression already defined.')

        table = SymbolTable(self.current_table)
        table.define(ObjectSymbol(node.idx_row, node, ast.ObjectType.ATOM, None))
        table.define(ObjectSymbol(node.idx_col, node, ast.ObjectType.ATOM, None))

        self._iterating_over |= {node.idx_row, node.idx_col}
        self.current_table = table
        self.visit(node.diag)
        self.visit(node.off)
        self.visit(node.rhs)

        if {node.diag.result_type, node.off.result_type, node.rhs.result_type} != {ast.NumericType.FLOAT}:
            raise CCLTypeError(node, f'EE expression has to have all parts with Float type.')

        self._iterating_over -= {node.idx_row, node.idx_col}
        self.current_table = self.current_table.parent

        node.result_type = ast.ArrayType(ast.ObjectType.ATOM)

    def visit_Substitution(self, node: ast.Substitution) -> None:
        if isinstance(node.lhs, ast.Name):
            name = node.lhs.val
            indices = None
            if node.constraints is not None:
                raise CCLSymbolError(node, f'Substitution symbol {name} cannot have a constraint.')
        else:  # ast.Subscript
            name = node.lhs.name.val
            indices = node.lhs.indices

        s = self.current_table.resolve(name)
        indices = tuple(indices) if indices is not None else tuple()
        if s is None:
            ns = SubstitutionSymbol(name, node, tuple(indices))
            self.symbol_table.define(ns)
            ns.rules[node.constraints] = node.rhs
        else:
            if not isinstance(s, SubstitutionSymbol):
                raise CCLSymbolError(node, f'Symbol {s.name} already defined as something else.')
            if indices != s.indices:
                raise CCLSymbolError(node, f'Substitution symbol {s.name} has different indices defined.')
            if node.constraints in s.rules:
                raise CCLTypeError(node, f'Same constraint already defined for symbol {s.name}.')
            s.rules[node.constraints] = node.rhs

    def visit_Predicate(self, node: ast.Predicate) -> None:
        try:
            f = PREDICATES[node.name]
        except KeyError:
            raise CCLSymbolError(node, f'Predicate {node.name} not defined.')

        if len(f.type.args) != len(node.args):
            raise CCLSymbolError(node, f'Predicate {f.name} should have {len(f.type.args)} arguments '
                                       f'but got {len(node.args)}')

        for arg_type, arg in zip(f.type.args, node.args):
            if isinstance(arg_type, ast.ObjectType):
                self.visit(arg)
                if arg.result_type != arg_type:
                    raise CCLTypeError(arg, f'Predicate\'s {node.name} argument is not {arg_type}')
            elif isinstance(arg_type, ast.StringType):
                # Note that name would not have result_type set as it's really a String
                if not isinstance(arg, ast.Name):
                    raise CCLTypeError(arg, f'Predicate {node.name} expected string argument')
            elif isinstance(arg_type, ast.NumericType):
                if not isinstance(arg.result_type, ast.NumericType):
                    raise CCLTypeError(arg, f'Predicate {node.name} expected numeric argument.')
            else:
                raise Exception('We should not get here!')
