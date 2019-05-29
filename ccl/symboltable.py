"""CCC's implementation of a symbol table"""

from typing import Dict, Tuple, Optional, Union
from abc import ABC, abstractmethod

from ccl import ast
from ccl.errors import CCLSymbolError


class Function:
    def __init__(self, name: str, fn_type: ast.FunctionType) -> None:
        self.name: str = name
        self.type: ast.FunctionType = fn_type


FUNCTIONS = {}

# Add common math functions
for fn in ['exp', 'sqrt', 'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh']:
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
        self.symbol_table: SymbolTable = SymbolTable(None)
        self.current_table: SymbolTable = self.symbol_table

    def visit_Method(self, node: ast.Method) -> None:
        node.symbol_table = self.current_table
        for annotation in node.annotations:
            self.visit(annotation)

        for statement in node.statements:
            self.visit(statement)

    def visit_Parameter(self, node: ast.Parameter) -> None:
        self.current_table.define(ParameterSymbol(node.name.val, node, node.type))

    def visit_Object(self, node: ast.Object) -> None:
        self.current_table.define(ObjectSymbol(node.name.val, node, node.type, node.constraints))

    def visit_Constant(self, node: ast.Constant) -> None:
        self.current_table.define(ConstantSymbol(node.name.val, node, node.prop.val, node.element.val))
