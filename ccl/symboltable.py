"""CCC's implementation of a symbol table"""

from typing import Dict, Set, Tuple, Optional, Union

from ccl import ast
from ccl.errors import CCLSymbolError, CCLTypeError


class Function:
    def __init__(self, name: str, arg_types: Tuple[ast.ObjectType, ...], result_type: ast.NumericType, comment: str) -> None:
        self.name: str = name
        self.arg_types: Tuple[ast.ObjectType, ...] = arg_types
        self.result_type: ast.NumericType = result_type
        self.comment: str = comment


FUNCTIONS = {'distance': Function('distance', (ast.ObjectType.ATOM, ast.ObjectType.ATOM), ast.NumericType.FLOAT, 'distance'),
             'covradius': Function('cov_radius', (ast.ObjectType.ATOM,), ast.NumericType.FLOAT, 'covalent radius'),
             'vdwradius': Function('vdw_radius', (ast.ObjectType.ATOM,), ast.NumericType.FLOAT, 'van der Waals radius')}


class Symbol:
    def __init__(self, name: str, def_node: Optional[ast.ASTNode]) -> None:
        self.name: str = name
        self.def_node: Optional[ast.ASTNode] = def_node

    @property
    def symbol_type(self) -> Union[ast.ParameterType, ast.ObjectType, ast.NumericType, ast.ComplexType]:
        raise NotImplementedError('We should not get here!')


class ParameterSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, kind: ast.ParameterType) -> None:
        super().__init__(name, def_node)
        self.kind: ast.ParameterType = kind

    def __repr__(self) -> str:
        return f'ParameterSymbol({self.name}, {self.kind.value})'

    @property
    def symbol_type(self) -> Union[ast.ParameterType, ast.NumericType]:
        if self.kind == ast.ParameterType.COMMON:
            return ast.NumericType.FLOAT

        return self.kind


class ObjectSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, kind: ast.ObjectType, constraints: ast.Constraint) -> None:
        super().__init__(name, def_node)
        self.kind: ast.ObjectType = kind
        self.constraints: ast.Constraint = constraints

    def __repr__(self) -> str:
        return f'ObjectSymbol({self.name}, {self.kind.value}, {self.constraints})'

    @property
    def symbol_type(self) -> ast.ObjectType:
        return self.kind


class FunctionSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ast.ASTNode], fn: Function) -> None:
        super().__init__(name, def_node)
        self.function: Function = fn

    @property
    def symbol_type(self) -> ast.ComplexType:
        return ast.ComplexType.FUNCTION


class ExprSymbol(Symbol):
    def __init__(self, name: str, def_node: ast.ASTNode, indices: Tuple[str, ...]) -> None:
        super().__init__(name, def_node)
        self.indices: Tuple[str, ...] = indices
        self.rules: Dict[Optional[ast.Constraint], ast.Expression] = {}

    def __repr__(self) -> str:
        return f'ExprSymbol({self.name}, {self.indices})'

    def __str__(self) -> str:
        return f'ExprSymbol({self.name}, {self.indices}) = {self.rules}'


class VariableSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ast.ASTNode], kind: ast.NumericType,
                 types: Tuple[ast.ObjectType, ...]) -> None:
        super().__init__(name, def_node)
        self.kind: ast.NumericType = kind
        self.types: Tuple[ast.ObjectType, ...] = types

    def __repr__(self) -> str:
        return f'VariableSymbol({self.name}, {self.kind.value}, {self.types})'

    @property
    def dim(self) -> int:
        return len(self.types)

    @property
    def symbol_type(self) -> ast.NumericType:
        return self.kind


class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable']) -> None:
        if parent is None:  # Root table
            self.parent = self
        else:
            self.parent: 'SymbolTable' = parent

        self.symbols: Dict[str, Symbol] = {}

    def resolve(self, s: str) -> Optional[Symbol]:
        if s in self.symbols:
            return self.symbols[s]

        if self.parent != self:
            return self.parent.resolve(s)

        return None

    def define(self, symbol: Symbol) -> None:
        if self.resolve(symbol.name):
            raise CCLSymbolError(symbol.def_node, f'Symbol {symbol.name} already defined.')

        self.symbols[symbol.name] = symbol

    def get_table(self, s: str) -> Optional['SymbolTable']:
        if s in self.symbols:
            return self

        if self.parent != self:
            return self.parent.get_table(s)

        return None

    def is_global(self, s: str) -> bool:
        table = self.get_table(s)
        return table.parent == table

    def define_expr(self, symbol: ExprSymbol, constraint: Optional[ast.Constraint], value: ast.Expression) -> None:
        resolved_symbol = self.resolve(symbol.name)
        if resolved_symbol is None:
            self.symbols[symbol.name] = symbol
            resolved_symbol = symbol
        else:
            if not isinstance(resolved_symbol, ExprSymbol):
                raise CCLSymbolError(symbol.def_node, f'Symbol {symbol.name} already defined as something else')

            if resolved_symbol.indices != symbol.indices:
                raise CCLSymbolError(symbol.def_node, f'Symbol {symbol.name} has different indices defined.')

        if constraint in resolved_symbol.rules:
            raise CCLSymbolError(symbol.def_node, f'Symbol {symbol.name} is already defined for same constraint')
        else:
            resolved_symbol.rules[constraint] = value

    def find_parent_table(self, symbols: Set[str]) -> 'SymbolTable':
        if not symbols:
            return self

        if self.parent != self:
            return self.parent.find_parent_table(symbols - set(self.symbols.keys()))

        return self

    @classmethod
    def create_from_ast(cls, node: ast.Method) -> 'SymbolTable':
        visitor = SymbolTableBuilder()
        visitor.visit(node)
        table = visitor.symbol_table
        table.check_expr_annotations()
        return table

    @classmethod
    def get_table_for_node(cls, node: ast.ASTNode) -> 'SymbolTable':
        if hasattr(node, 'symbol_table'):
            return node.symbol_table

        return cls.get_table_for_node(node.parent)

    def print(self) -> None:
        for symbol in self.symbols.values():
            print(symbol)

    def check_expr_annotations(self) -> None:
        for symbol in self.symbols.values():
            if isinstance(symbol, ExprSymbol):
                if all(symbol.rules.keys()):
                    raise CCLSymbolError(symbol.def_node, f'No default option specified for expression {symbol.name}')


# noinspection PyPep8Naming
class SymbolTableBuilder(ast.ASTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.global_table: SymbolTable = SymbolTable(None)
        self.symbol_table: SymbolTable = SymbolTable(self.global_table)
        self.current_table: SymbolTable = self.symbol_table

        self._iterating_over: Set[str] = set()
        self.indices_mapping: Dict[str, str] = dict()
        self.inside_constraint: bool = False

        # Define common symbols
        self.global_table.define(VariableSymbol('q', None, ast.NumericType.FLOAT, (ast.ObjectType.ATOM,)))
        self.global_table.define(FunctionSymbol('R', None, FUNCTIONS['distance']))

    @property
    def iterating_over(self) -> set:
        return {self.indices_mapping.get(key, key) for key in self._iterating_over}

    def visit_Method(self, node: ast.Method) -> None:
        node.symbol_table = self.current_table
        for a in node.annotations:
            self.visit(a)

        for s in node.statements:
            self.visit(s)

    def visit_ParameterAnnotation(self, node: ast.ParameterAnnotation) -> None:
        self.current_table.define(ParameterSymbol(node.name.name, node, ast.ParameterType(node.kind)))

    def visit_ObjectAnnotation(self, node: ast.ObjectAnnotation) -> None:
        self.current_table.define(ObjectSymbol(node.name.name, node, ast.ObjectType(node.kind), node.constraints))

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.value_from)
        self.visit(node.value_to)
        if node.value_from.result_type != ast.NumericType.INT:
            raise CCLTypeError(node.value_from, f'For loop lower bound not Int')
        if node.value_to.result_type != ast.NumericType.INT:
            raise CCLTypeError(node.value_to, f'For loop upper bound not Int')
        self.current_table = SymbolTable(self.current_table)
        node.symbol_table = self.current_table
        self.current_table.define(VariableSymbol(node.name.name, node, ast.NumericType.INT, ()))
        for statement in node.body:
            self.visit(statement)

        self.current_table = self.current_table.parent

    def visit_ForEach(self, node: ast.ForEach) -> None:
        name = node.name.name
        self.current_table = SymbolTable(self.current_table)
        node.symbol_table = self.current_table
        self.current_table.define(ObjectSymbol(name, node, ast.ObjectType(node.kind), node.constraints))
        self._iterating_over.add(node.name.name)

        for statement in node.body:
            self.visit(statement)

        self._iterating_over.remove(node.name.name)
        self.current_table = self.current_table.parent

    def visit_ExprAnnotation(self, node: ast.ExprAnnotation) -> None:
        if isinstance(node.lhs, ast.Name):
            if node.constraints:
                raise CCLSymbolError(node, f'Constraints not possible for expression {node.lhs.name}')
            self.current_table.define_expr(ExprSymbol(node.lhs.name, node, ()), None, node.rhs)
        elif isinstance(node.lhs, ast.Subscript):
            indices = tuple(idx.name for idx in node.lhs.indices)
            self.current_table.define_expr(ExprSymbol(node.lhs.name.name, node, indices), node.constraints, node.rhs)
        else:
            raise RuntimeError('We should not get here')

    def visit_Name(self, node: ast.Name) -> None:
        name = self.indices_mapping.get(node.name, node.name)

        symbol = self.current_table.resolve(name)
        if symbol:
            if isinstance(symbol, ObjectSymbol):
                if name not in self.iterating_over:
                    raise CCLTypeError(node, f'Symbol {node.name} not bound to For/ForEach/Sum')

                if node.ctx == ast.VarContext.LOAD and not self.inside_constraint:
                    if symbol.constraints is not None:
                        self.inside_constraint = True
                        self.visit(symbol.constraints)
                        self.inside_constraint = False
                node.result_type = symbol.symbol_type
            elif isinstance(symbol, ExprSymbol):
                self.visit(symbol.rules[None])
                node.result_type = symbol.rules[None].result_type
            else:
                node.result_type = symbol.symbol_type
        if node.ctx == ast.VarContext.LOAD and symbol is None:
            raise CCLSymbolError(node, f'Symbol {name} used but not defined')

    def visit_Subscript(self, node: ast.Subscript) -> None:

        symbol = self.current_table.resolve(node.name.name)
        if isinstance(symbol, ParameterSymbol) and symbol.kind == ast.ParameterType.ATOM:
            self.visit(node.name)
            if len(node.indices) != 1:
                raise CCLTypeError(node, f'Atom parameter {node.name.name} must have one index only')

            self.visit(node.indices[0])
            if node.indices[0].result_type != ast.ObjectType.ATOM:
                raise CCLTypeError(node, f'Atom parameter {node.name.name} was indexed by {node.indices[0].result_type}'
                                         ' not Atom')

            node.result_type = ast.NumericType.FLOAT
        elif isinstance(symbol, ParameterSymbol) and symbol.kind == ast.ParameterType.BOND:
            self.visit(node.name)
            for idx in node.indices:
                self.visit(idx)
            if len(node.indices) == 1 and node.indices[0].result_type != ast.ObjectType.BOND:
                raise CCLTypeError(node, f'Bond parameter {node.name.name} must be indexed with Bond')
            if len(node.indices) == 2 and \
                    node.indices[0].result_type != node.indices[1].result_type != ast.ObjectType.ATOM:
                raise CCLTypeError(node, f'Bond parameter {node.name.name} was indexed by {node.indices[0].result_type}'
                                         ' not Bond or two Atoms')

            node.result_type = ast.NumericType.FLOAT
        elif isinstance(symbol, VariableSymbol) and symbol.types:
            self.visit(node.name)
            for idx in node.indices:
                self.visit(idx)
            index_types = tuple(idx.result_type for idx in node.indices)
            if symbol.types != index_types:
                raise CCLTypeError(node,
                                   f'Cannot index {node.name.name} with {index_types}, expected was {symbol.types}')

            node.result_type = symbol.kind
        elif isinstance(symbol, FunctionSymbol):
            self.visit(node.name)
            for idx in node.indices:
                self.visit(idx)
            index_types = tuple(idx.result_type for idx in node.indices)
            if symbol.function.arg_types != index_types:
                raise CCLTypeError(node,
                                   f'Cannot index {node.name.name} with {index_types}, expected was'
                                   f'{symbol.function.arg_types}')
            node.result_type = symbol.function.result_type
        elif isinstance(symbol, ExprSymbol):
            types = set()
            for expr in symbol.rules.values():
                node_indices = [idx.name for idx in node.indices]
                self.indices_mapping.update({ei: ni for ni, ei in zip(node_indices, symbol.indices)})
                self.visit(expr)
                types.add(expr.result_type)
                for name in symbol.indices:
                    self.indices_mapping.pop(name)

            if len(types) > 1:
                raise CCLTypeError(node, f'Expressions for {node.name.name} have different types')

            node.result_type = list(types)[0]
        else:
            raise CCLTypeError(node, f'Cannot index type {node.name.result_type}')

    def visit_Assign(self, node: ast.Assign) -> None:
        def check_compatible_types(lt, rt) -> None:
            if (rt == lt and rt in ast.NumericType) or (lt == ast.NumericType.FLOAT and rt == ast.NumericType.INT):
                pass
            elif rt == ast.NumericType.FLOAT and lt == ast.NumericType.INT:  # Rounding not allowed
                raise CCLTypeError(node, f'Cannot assign Float to Int')
            else:  # Incompatible types
                raise CCLTypeError(node, f'Cannot assign {rt} to {lt}, only numeric types allowed for assignment')

        self.visit(node.rhs)
        rtype = node.rhs.result_type
        if rtype not in ast.NumericType:
            raise CCLTypeError(node, 'Right hand side must have numeric type')

        if isinstance(node.lhs, ast.Subscript):
            symbol = self.current_table.resolve(node.lhs.name.name)
            if symbol is not None:
                self.visit(node.lhs)
                ltype = node.lhs.result_type
                if not isinstance(symbol, VariableSymbol):
                    raise CCLTypeError(node, 'Cannot assign to something different than Array')

                check_compatible_types(ltype, rtype)
            else:
                names = set(idx.name for idx in node.lhs.indices)
                types = tuple(self.current_table.resolve(idx.name).kind for idx in node.lhs.indices)
                if any(t not in ast.ObjectType for t in types):
                    raise CCLTypeError(node, 'Cannot index by type other than Atom or Bond')

                table = self.current_table.find_parent_table(names)
                table.define(VariableSymbol(node.lhs.name.name, node, rtype, types))
        elif isinstance(node.lhs, ast.Name):
            symbol = self.current_table.resolve(node.lhs.name)
            if symbol is not None and isinstance(symbol, ExprSymbol):
                raise CCLTypeError(node, f'Cannot assign to expression symbol {node.lhs.name}')
            self.visit(node.lhs)
            ltype = node.lhs.result_type
            if ltype is None:  # Create a new symbol
                if rtype not in ast.NumericType:
                    raise CCLTypeError(node, f'Cannot assign non numeric expression of type {rtype}')
                symbol = VariableSymbol(node.lhs.name, node, rtype, ())
                self.current_table.define(symbol)
            else:
                check_compatible_types(ltype, rtype)
        else:
            raise RuntimeError('We should not get here.')

    def visit_PredicateConstraint(self, node: ast.Predicate) -> None:
        # TODO check for predicate name
        for arg in node.args:
            if isinstance(arg, ast.Name) and not self.current_table.resolve(arg.name):
                raise CCLSymbolError(node, f'Predicate argument {arg.name} unknown')

    def visit_Number(self, node: ast.Number) -> None:
        if isinstance(node.n, int):
            node.result_type = ast.NumericType.INT
        else:
            node.result_type = ast.NumericType.FLOAT

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        self.visit(node.expr)
        if node.expr.result_type not in ast.NumericType:
            raise CCLTypeError(node, f'Incompatible type for unary {node.op}')
        node.result_type = node.expr.result_type

    def visit_BinaryOp(self, node: ast.BinaryOp) -> None:
        self.visit(node.left)
        self.visit(node.right)

        ltype = node.left.result_type
        rtype = node.right.result_type

        if ltype in ast.NumericType and rtype in ast.NumericType:
            if ltype == ast.NumericType.INT and rtype == ast.NumericType.INT:
                node.result_type = ast.NumericType.INT
            else:
                node.result_type = ast.NumericType.FLOAT
        else:
            raise CCLTypeError(node, f'Incompatible types for {node.op.value}: ' +
                               f'{node.left.result_type} and {node.right.result_type}')

    def visit_Sum(self, node: ast.Sum) -> None:
        self._iterating_over.add(node.name.name)
        self.visit(node.name)
        self.visit(node.expr)
        self._iterating_over.remove(node.name.name)

        if node.name.result_type not in ast.ObjectType:
            raise CCLTypeError(node, f'Sum index has to be Atom or Bond, not {node.name.result_type}')

        node.result_type = node.expr.result_type

    def visit_Property(self, node: ast.Property) -> None:
        fname = node.prop.name
        try:
            f = FUNCTIONS[fname]
        except KeyError:
            raise CCLSymbolError(node, f'Function/property {fname} not implemented')
        self.current_table.define(FunctionSymbol(node.name.name, node, f))
