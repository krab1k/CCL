"""CCC's implementation of a symbol table"""

from typing import Dict, Tuple, Optional, Union
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

# Add atom properties
for prop in ['electronegativity', 'covalent radius', 'van der waals radius', 'hardness', 'ionization potential',
             'electron affinity']:
    FUNCTIONS[prop] = Function(prop, ast.FunctionType(ast.NumericType.FLOAT, ast.ObjectType.ATOM))

# Add custom functions

FUNCTIONS['distance'] = Function('distance',
                                 ast.FunctionType(ast.NumericType.FLOAT, ast.ObjectType.ATOM, ast.ObjectType.ATOM))


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
        # All the expressions must have same type, so pick the first one
        return next(iter(self.rules.values())).result_type


class ConstantSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, property: str, element: str):
        super().__init__(name, def_node)
        self.property: str = property
        self.element: str = element

    def __repr__(self) -> str:
        return f'ConstantSymbol({self.name}, {self.property}, {self.element})'

    def symbol_type(self) -> ast.NumericType:
        return ast.NumericType.FLOAT


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

        # Add math function names to the global table
        for fn_name in MATH_FUNCTIONS_NAMES:
            self.global_table.define(FunctionSymbol(fn_name, None, FUNCTIONS[fn_name]))

        # q is always a vector of charges
        self.global_table.define(VariableSymbol('q', None, ast.ArrayType(ast.ObjectType.ATOM, )))

    def visit_Method(self, node: ast.Method) -> None:
        node.symbol_table = self.current_table
        for annotation in node.annotations:
            self.visit(annotation)

        for statement in node.statements:
            self.visit(statement)

    def visit_Parameter(self, node: ast.Parameter) -> None:
        self.current_table.define(ParameterSymbol(node.name, node, node.type))

    def visit_Object(self, node: ast.Object) -> None:
        self.current_table.define(ObjectSymbol(node.name, node, node.type, node.constraints))

    def visit_Constant(self, node: ast.Constant) -> None:
        self.current_table.define(ConstantSymbol(node.name, node, node.prop, node.element))

    def visit_Property(self, node: ast.Property) -> None:
        try:
            f = FUNCTIONS[node.prop]
        except KeyError:
            raise CCLSymbolError(node, f'Function {node.prop} is not known.')

        self.current_table.define(FunctionSymbol(node.name, node, f))

    def visit_Name(self, node: ast.Name) -> None:
        s = self.current_table.resolve(node.val)
        if s is not None:
            node.result_type = s.symbol_type()
        else:
            raise CCLSymbolError(node, f'Symbol {node.val} not defined.')

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
        if isinstance(node.lhs, ast.Name):
            s = self.current_table.resolve(node.lhs.val)
            if s is not None:
                if check_types(s.symbol_type(), rtype):
                    node.lhs.result_type = s.symbol_type()
                else:
                    raise CCLTypeError(node,
                                       f'Cannot assign {rtype} to the variable {s.name} of type {s.symbol_type()}.')
            else:
                # New symbols are defined at method scope
                self.symbol_table.define(VariableSymbol(node.lhs.val, node, rtype))
                node.lhs.result_type = rtype
        else:  # ast.Subscript
            # TODO
            pass

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
            else:
                raise CCLTypeError(node, f'Cannot perform {node.op.value} for types {ltype} and {rtype}')
        #  One is Array, second Number
        elif isinstance(ltype, (ast.ArrayType, ast.NumericType)) and isinstance(rtype, (ast.ArrayType, ast.NumericType)):
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

        table = SymbolTable(self.current_table)
        node.symbol_table = table
        table.define(VariableSymbol(node.name.val, node, ast.NumericType.INT))
        self.current_table = table
        for statement in node.body:
            self.visit(statement)

        self.current_table = self.current_table.parent

    def visit_ForEach(self, node: ast.ForEach) -> None:
        s = self.current_table.resolve(node.name.val)
        if s is not None:
            raise CCLSymbolError(node.name, f'Symbol {node.name.val} already defined.')

        table = SymbolTable(self.current_table)
        node.symbol_table = table
        table.define(ObjectSymbol(node.name.val, node, node.type, node.constraints))
        self.current_table = table
        for statement in node.body:
            self.visit(statement)

        self.current_table = self.current_table.parent
