"""CCL's implementation of a symbol table"""

from typing import Dict, Optional, Set
from abc import ABC, abstractmethod

from ccl import ast
from ccl.common import ELEMENT_NAMES
from ccl.functions import Function, FUNCTIONS, MATH_FUNCTIONS, PREDICATES
from ccl.types import *
from ccl.errors import CCLSymbolError, CCLTypeError


class Symbol(ABC):
    """Abstract class for every symbol"""
    @abstractmethod
    def __init__(self, name: str, def_node: Optional[ast.ASTNode]) -> None:
        self.name: str = name
        self.def_node: Optional[ast.ASTNode] = def_node

    @abstractmethod
    def symbol_type(self) -> Union[NumericType, ArrayType, ObjectType, ArrayType, ParameterType, FunctionType]:
        pass


class ParameterSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, ptype: ParameterType) -> None:
        super().__init__(name, def_node)
        self.type: ParameterType = ptype

    def __repr__(self) -> str:
        return f'ParameterSymbol({self.name}, {self.type})'

    def symbol_type(self) -> ParameterType:
        return self.type


class ObjectSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, otype: ObjectType,
                 constraints: Optional[ast.Constraint]) -> None:
        super().__init__(name, def_node)
        self.type: ObjectType = otype
        self.constraints: Optional[ast.Constraint] = constraints

    def __repr__(self) -> str:
        return f'ObjectSymbol({self.name}, {self.type}, {self.constraints})'

    def symbol_type(self) -> ObjectType:
        return self.type


class FunctionSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ast.ASTNode], f: Function) -> None:
        super().__init__(name, def_node)
        self.function: Function = f

    def __repr__(self) -> str:
        return f'FunctionSymbol({self.name}, {self.function})'

    def symbol_type(self) -> FunctionType:
        return self.function.type


class VariableSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ast.ASTNode],
                 vtype: Union[NumericType, ArrayType]) -> None:
        super().__init__(name, def_node)
        self.type: Union[NumericType, ArrayType] = vtype

    def __repr__(self) -> str:
        return f'VariableSymbol({self.name}, {self.type})'

    def symbol_type(self) -> Union[NumericType, ArrayType]:
        return self.type


class SubstitutionSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, indices: Tuple[ast.Name, ...]) -> None:
        super().__init__(name, def_node)
        self.indices: Tuple[ast.Name, ...] = indices
        self.rules: Dict[Optional[ast.Constraint], ast.Expression] = {}

    def __repr__(self) -> str:
        return f'SubstitutionSymbol({self.name}, {self.indices})'

    def symbol_type(self) -> Union[NumericType, ArrayType, ObjectType, ArrayType, ParameterType]:
        # All the expressions must have same type, so pick the default one
        return self.rules[None].result_type


class ConstantSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, f: Function, element: str):
        super().__init__(name, def_node)
        self.property: Function = f
        self.element: str = element

    def __repr__(self) -> str:
        return f'ConstantSymbol({self.name}, {self.property}, {self.element})'

    def symbol_type(self) -> NumericType:
        return self.property.type.return_type


class SymbolTable:
    """CCL's symbol table"""
    def __init__(self, parent: Optional['SymbolTable']) -> None:
        self.parent: Optional['SymbolTable'] = parent
        self.symbols: Dict[str, Symbol] = {}

    def __repr__(self) -> str:
        return 'SymbolTable'

    def __getitem__(self, item):
        return self.symbols[item]

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

    @classmethod
    def get_table_for_node(cls, node: ast.ASTNode):
        if hasattr(node, 'symbol_table'):
            return node.symbol_table

        assert node.parent is not None
        return cls.get_table_for_node(node.parent)


# noinspection PyPep8Naming
class SymbolTableBuilder(ast.ASTVisitor):
    """Build symbol table from AST"""
    def __init__(self) -> None:
        super().__init__()
        self.global_table: SymbolTable = SymbolTable(None)
        self.symbol_table: SymbolTable = SymbolTable(self.global_table)
        self.current_table: SymbolTable = self.symbol_table

        self._iterating_over: Set[str] = set()
        self._indices_mapping: Dict[str, str] = {}

        # Add math function names to the global table
        for fn_name in MATH_FUNCTIONS:
            self.global_table.define(FunctionSymbol(fn_name, None, FUNCTIONS[fn_name]))

        # q is always a vector of charges
        self.global_table.define(VariableSymbol('q', None, ArrayType(ObjectType.ATOM, )))

    @property
    def iterating_over(self) -> Set[str]:
        return {self._indices_mapping.get(i, i) for i in self._iterating_over}

    def check_substitutions_default(self) -> None:
        for symbol in self.global_table.symbols.values():
            if isinstance(symbol, SubstitutionSymbol):
                if None not in symbol.rules:
                    raise CCLSymbolError(symbol.def_node,
                                         f'No default option specified for Substitution symbol {symbol.name}.')

    def visit_Method(self, node: ast.Method) -> None:
        node.symbol_table = self.current_table
        for annotation in node.annotations:
            self.visit(annotation)

        for statement in node.statements:
            self.visit(statement)

        self.check_substitutions_default()

    def visit_Parameter(self, node: ast.Parameter) -> None:
        assert self.current_table.parent is not None
        self.current_table.parent.define(ParameterSymbol(node.name, node, node.type))

    def visit_Object(self, node: ast.Object) -> None:
        if node.atom_indices is not None:
            i1, i2 = node.atom_indices
            s1 = self.current_table.resolve(i1)
            s2 = self.current_table.resolve(i2)
            if s1 is not None or s2 is not None:
                raise CCLSymbolError(node, f'Decomposition of bond symbol {node.name} used already defined names.')

            self.global_table.define(ObjectSymbol(i1, node, ObjectType.ATOM, None))
            self.global_table.define(ObjectSymbol(i2, node, ObjectType.ATOM, None))
        self.global_table.define(ObjectSymbol(node.name, node, node.type, node.constraints))

    def visit_Constant(self, node: ast.Constant) -> None:
        try:
            f = FUNCTIONS[node.prop]
        except KeyError:
            raise CCLSymbolError(node, f'Property {node.prop} is not known.')

        if len(f.type.args) != 1 or f.type.args[0] != ObjectType.ATOM:
            raise CCLTypeError(node, f'Function {node.prop} is not a property')

        self.global_table.define(ConstantSymbol(node.name, node, f, node.element))

    def visit_Property(self, node: ast.Property) -> None:
        try:
            f = FUNCTIONS[node.prop]
        except KeyError:
            raise CCLSymbolError(node, f'Function {node.prop} is not known.')

        self.global_table.define(FunctionSymbol(node.name, node, f))

    def visit_Name(self, node: ast.Name) -> None:
        name = self._indices_mapping.get(node.val, node.val)
        s = self.current_table.resolve(name)
        if s is not None:
            if isinstance(s, SubstitutionSymbol):
                self.visit(s.rules[None])
            if s.symbol_type() == ParameterType.COMMON:
                node.result_type = NumericType.FLOAT
            else:
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
            if isinstance(idx.result_type, ObjectType) and \
                    mapped_val not in self.iterating_over:
                raise CCLSymbolError(idx, f'Object {mapped_val} not bound to any For/ForEach/Sum.')
        index_types = tuple(index_types)
        index_types_str = ', '.join(str(i) for i in index_types)

        if isinstance(s, ParameterSymbol):
            if symbol_type == ParameterType.ATOM and index_types != (ObjectType.ATOM,) or \
               (symbol_type == ParameterType.BOND and
                    index_types not in [(ObjectType.BOND,), (ObjectType.ATOM, ObjectType.ATOM)]):
                raise CCLTypeError(node, f'Cannot index parameter symbol of type {symbol_type} with {index_types_str}.')
            if symbol_type == ParameterType.COMMON:
                raise CCLTypeError(node, f'Cannot index common parameter.')
        elif isinstance(s, VariableSymbol) and isinstance(symbol_type, ArrayType):
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
            if not all(isinstance(t, ObjectType) for t in index_types):
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
        node.result_type = NumericType.FLOAT

    def visit_Assign(self, node: ast.Assign) -> None:
        def check_types(lhs: Type, rhs: Type):
            if isinstance(lhs, ArrayType) and isinstance(rhs, ArrayType):
                return lhs == rhs
            # Can assign number to all elements of the vector/matrix
            if isinstance(lhs, ArrayType) and isinstance(rhs, NumericType):
                return True
            if isinstance(lhs, NumericType) and isinstance(rhs, NumericType):
                # Cannot assign Float to Int, OK otherwise
                if lhs == NumericType.INT and rhs == NumericType.FLOAT:
                    return False
                return True

            return False

        self.visit(node.rhs)
        rtype = node.rhs.result_type
        if not isinstance(rtype, (NumericType, ArrayType)):
            raise CCLTypeError(node.rhs, f'Only Numbers and Arrays can be assigned not {rtype}.')
        if isinstance(node.lhs, ast.Name):
            s = self.current_table.resolve(node.lhs.val)
            if s is not None:
                if s.name in self._iterating_over:
                    raise CCLTypeError(node, f'Cannot assign to loop variable {s.name}.')
                if isinstance(s, SubstitutionSymbol):
                    raise CCLSymbolError(node.lhs, f'Cannot assign to a substitution symbol {s.name}.')
                if isinstance(s, ParameterSymbol):
                    raise CCLSymbolError(node.lhs, f'Cannot assign to a parameter symbol {s.name}.')
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
                if not isinstance(s.symbol_type(), ArrayType):
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
                if not all(isinstance(i, ObjectType) for i in index_types):
                    raise CCLTypeError(node.lhs, f'Cannot index with something different than Atom or Bond')
                self.symbol_table.define(VariableSymbol(node.lhs.name.val, node, ArrayType(*index_types)))
                node.lhs.name.result_type = ArrayType(*index_types)
            node.lhs.result_type = rtype
        else:
            raise Exception('Should not get here!')

    def visit_Function(self, node: ast.Function) -> None:
        # Functions have only one numerical argument
        def check_args(expected: Type, given: Type):
            if expected == given:
                return True
            if given == NumericType.INT and expected == NumericType.FLOAT:
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

        if isinstance(ltype, NumericType) and isinstance(rtype, NumericType):
            if ltype == NumericType.FLOAT or rtype == NumericType.FLOAT:
                node.result_type = NumericType.FLOAT
            else:
                node.result_type = NumericType.INT
        elif isinstance(ltype, ArrayType) and isinstance(rtype, ArrayType):
            if node.op in (ast.BinaryOp.Ops.ADD, ast.BinaryOp.Ops.SUB):
                if ltype.indices == rtype.indices:
                    node.result_type = ltype
                else:
                    raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')
            elif node.op == ast.BinaryOp.Ops.MUL:
                if ltype.dim() == rtype.dim() == 2:
                    if ltype.indices[1] != rtype.indices[0]:
                        raise CCLTypeError(node, f'Cannot multiply matrices of types {ltype} and {rtype}')
                    node.result_type = ArrayType(ltype.indices[0], rtype.indices[1])
                elif ltype.dim() == 1 and rtype.dim() == 2:
                    if ltype.indices[0] != rtype.indices[0]:
                        raise CCLTypeError(node, f'Cannot multiply vector of type {ltype} and matrix of type {rtype}')
                    node.result_type = ArrayType(rtype.indices[1])
                elif ltype.dim() == 2 and rtype.dim() == 1:
                    if ltype.indices[1] != rtype.indices[0]:
                        raise CCLTypeError(node, f'Cannot multiply matrix of type {ltype} with vector of type {rtype}')
                    node.result_type = ArrayType(ltype.indices[0])
                elif ltype.dim() == rtype.dim() == 1:
                    if ltype != rtype:
                        raise CCLTypeError(node, f'Cannot perform dot product of vectors of types {ltype} and {rtype}')
                    node.result_type = NumericType.FLOAT
            else:
                raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')
        #  One is Array, second Number
        elif isinstance(ltype, (ArrayType, NumericType)) and \
                isinstance(rtype, (ArrayType, NumericType)):
            if node.op not in (ast.BinaryOp.Ops.MUL, ast.BinaryOp.Ops.DIV):
                raise CCLTypeError(node, f'Cannot perform operation other than * or / between Number and Array.')
            if node.op == ast.BinaryOp.Ops.DIV and isinstance(ltype, NumericType) and \
                    isinstance(rtype, ArrayType):
                raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')
            if isinstance(ltype, ArrayType):
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
        table.define(VariableSymbol(node.name.val, node, NumericType.INT))
        self.current_table = table
        for statement in node.body:
            self.visit(statement)

        self._iterating_over.remove(node.name.val)

        assert self.current_table.parent is not None
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

            table.define(ObjectSymbol(i1, node, ObjectType.ATOM, None))
            table.define(ObjectSymbol(i2, node, ObjectType.ATOM, None))
            atom_indices = {i1, i2}

        self._iterating_over |= atom_indices | {node.name.val}

        node.symbol_table = table
        table.define(ObjectSymbol(node.name.val, node, node.type, node.constraints))
        self.current_table = table
        for statement in node.body:
            self.visit(statement)

        self._iterating_over -= atom_indices | {node.name.val}

        assert self.current_table.parent is not None
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
        table.define(ObjectSymbol(node.idx_row, node, ObjectType.ATOM, None))
        table.define(ObjectSymbol(node.idx_col, node, ObjectType.ATOM, None))

        self._iterating_over |= {node.idx_row, node.idx_col}
        self.current_table = table
        self.visit(node.diag)
        self.visit(node.off)
        self.visit(node.rhs)

        if {node.diag.result_type, node.off.result_type, node.rhs.result_type} != {NumericType.FLOAT}:
            raise CCLTypeError(node, f'EE expression has to have all parts with Float type.')

        self._iterating_over -= {node.idx_row, node.idx_col}

        assert self.current_table.parent is not None
        self.current_table = self.current_table.parent

        node.result_type = ArrayType(ObjectType.ATOM)

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
            self.global_table.define(ns)
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
            if isinstance(arg_type, ObjectType):
                self.visit(arg)
                name = self._indices_mapping.get(arg.val, arg.val)
                if name not in self.iterating_over:
                    raise CCLSymbolError(arg, f'Symbol {arg.val} not bound to ForEach or Sum.')
                if arg.result_type != arg_type:
                    raise CCLTypeError(arg, f'Predicate\'s {node.name} argument is not {arg_type}')
            elif isinstance(arg_type, StringType):
                # Note that name would not have result_type set as it's really a String
                if not isinstance(arg, ast.Name):
                    raise CCLTypeError(arg, f'Predicate {node.name} expected string argument')
            elif isinstance(arg_type, NumericType):
                if not isinstance(arg.result_type, NumericType):
                    raise CCLTypeError(arg, f'Predicate {node.name} expected numeric argument.')
            else:
                raise Exception('We should not get here!')

        if f.name == 'element' and node.args[1].val.lower() not in ELEMENT_NAMES:
            raise CCLTypeError(node.args[1], f'Unknown element {node.args[1].val}')


class NameGetter:
    """Get all names used within a particular AST node"""
    @classmethod
    def visit(cls, node: ast.ASTNode, table: SymbolTable) -> Set[str]:
        names = set()
        if isinstance(node, ast.Name):
            if node.val.lower() not in ELEMENT_NAMES:
                names.add(node.val)
            symbol = table.resolve(node.val)
            if symbol is not None and isinstance(symbol, SubstitutionSymbol):
                for cond, expr in symbol.rules.items():
                    if cond is not None:
                        names |= cls.visit(cond, table)
                    names |= cls.visit(expr, table)
                names -= {idx.val for idx in symbol.indices}
        for _, value in node:
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.ASTNode):
                        names = names | cls.visit(item, table)
            elif isinstance(value, ast.ASTNode):
                names = names | cls.visit(value, table)

        return names
