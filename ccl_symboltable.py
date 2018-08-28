from typing import Dict, Set

from ccl_ast import *
from ccl_errors import CCLSymbolError, CCLTypeError


class ObjectType(Enum):
    ATOM = 'Atom'
    BOND = 'Bond'


class ParameterType(Enum):
    ATOM = 'Atom'
    BOND = 'Bond'
    COMMON = 'Common'


class NumericType(Enum):
    INT = 'Int'
    FLOAT = 'Float'


class Symbol:
    def __init__(self, name: str, def_node: Optional[ASTNode]):
        self.name: str = name
        self.def_node: Optional[ASTNode] = def_node

    @property
    def symbol_type(self):
        raise NotImplemented('We should not get here!')


class ParameterSymbol(Symbol):
    def __init__(self, name, def_node: ASTNode, kind: ParameterType):
        super().__init__(name, def_node)
        self.kind: ParameterType = kind

    def __repr__(self):
        return f'ParameterSymbol({self.name}, {self.kind.value})'

    @property
    def symbol_type(self):
        if self.kind == ParameterType.COMMON:
            return NumericType.FLOAT
        else:
            return f'{self.kind.value}Parameter'


class ObjectSymbol(Symbol):
    def __init__(self, name: str, def_node: ASTNode, kind: ObjectType, constraints: Constraint):
        super().__init__(name, def_node)
        self.kind: ObjectType = kind
        self.constraints: Constraint = constraints

    def __repr__(self):
        return f'ObjectSymbol({self.name}, {self.kind.value}, {self.constraints})'

    @property
    def symbol_type(self):
        return self.kind


class FunctionSymbol(Symbol):
    pass


class ExprSymbol(Symbol):
    def __init__(self, name: str, def_node: ASTNode, indices: Tuple[str, ...]):
        super().__init__(name, def_node)
        self.indices: Tuple[str, ...] = indices
        self.rules: Dict[Constraint, Expression] = {}

    def __repr__(self):
        return f'ExprSymbol({self.name}, {self.indices})'

    def __str__(self):
        return f'ExprSymbol({self.name}, {self.indices}) = {self.rules}'


class VariableSymbol(Symbol):
    def __init__(self, name: str, def_node: Optional[ASTNode], kind: NumericType, types: Tuple[ObjectType, ...]):
        super().__init__(name, def_node)
        self.kind: NumericType = kind
        self.types: Tuple[ObjectType, ...] = types

    def __repr__(self):
        return f'VariableSymbol({self.name}, {self.kind.value}, {self.types})'

    @property
    def dim(self):
        return len(self.types)

    @property
    def symbol_type(self):
        if self.dim > 0:
            return 'Array'
        else:
            return self.kind


class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable']):
        self.parent: Optional['SymbolTable'] = parent
        self.symbols: Dict[str, Symbol] = {}

    def resolve(self, s: str):
        if s in self.symbols:
            return self.symbols[s]

        if self.parent:
            return self.parent.resolve(s)

        return None

    def define(self, symbol: Symbol):
        if self.resolve(symbol.name):
            raise CCLSymbolError(symbol.def_node, f'Symbol {symbol.name} already defined.')

        self.symbols[symbol.name] = symbol

    def define_expr(self, symbol: ExprSymbol, constraint: Optional[Constraint], value: Expression):
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

    def find_parent_table(self, symbols: Set[str]):
        if not symbols:
            return self

        return self.parent.find_parent_table(symbols - set(self.symbols.keys()))

    @classmethod
    def create_from_ast(cls, ast: Method):
        visitor = SymbolTableBuilder()
        visitor.visit(ast)
        table = visitor.symbol_table
        table.check_expr_annotations()
        return table

    def print(self):
        for symbol in self.symbols.values():
            print(symbol)

    def check_expr_annotations(self):
        for symbol in self.symbols.values():
            if isinstance(symbol, ExprSymbol):
                if all(symbol.rules.keys()):
                    raise CCLSymbolError(symbol.def_node, f'No default option specified for expression {symbol.name}')


# noinspection PyPep8Naming
class SymbolTableBuilder(ASTVisitor):
    def __init__(self):
        super().__init__()
        self.symbol_table: SymbolTable = SymbolTable(None)
        self.current_table: SymbolTable = self.symbol_table

        self.iterating_over: Set[str] = set()
        self.inside_constraint = False

        # Define common symbols
        self.current_table.define(VariableSymbol('q', None, NumericType.FLOAT, (ObjectType.ATOM,)))

    def visit_Method(self, node: Method):
        for a in node.annotations:
            self.visit(a)

        for s in node.statements:
            self.visit(s)

    def visit_ParameterAnnotation(self, node: ParameterAnnotation):
        self.current_table.define(ParameterSymbol(node.name.name, node, ParameterType(node.kind)))

    def visit_ObjectAnnotation(self, node: ObjectAnnotation):
        self.current_table.define(ObjectSymbol(node.name.name, node, ObjectType(node.kind), node.constraints))

    def visit_For(self, node: For):
        self.visit(node.value_from)
        self.visit(node.value_to)
        if node.value_from.result_type != NumericType.INT:
            raise CCLTypeError(node.value_from, f'For loop lower bound not Int')
        if node.value_to.result_type != NumericType.INT:
            raise CCLTypeError(node.value_to, f'For loop upper bound not Int')
        self.current_table = SymbolTable(self.current_table)
        self.current_table.define(VariableSymbol(node.name.name, node, NumericType.INT, ()))
        for statement in node.body:
            self.visit(statement)

        self.current_table = self.current_table.parent

    def visit_ForEach(self, node: ForEach):
        name = node.name.name
        self.current_table = SymbolTable(self.current_table)
        self.current_table.define(ObjectSymbol(name, node, ObjectType(node.kind), node.constraints))
        self.iterating_over.add(node.name.name)

        for statement in node.body:
            self.visit(statement)

        self.iterating_over.remove(node.name.name)
        self.current_table = self.current_table.parent

    def visit_ExprAnnotation(self, node: ExprAnnotation):
        if isinstance(node.lhs, Name):
            if node.constraints:
                raise CCLSymbolError(node, f'Constraints not possible for expression {node.lhs.name}')
            self.current_table.define_expr(ExprSymbol(node.lhs.name, node, ()), None, node.rhs)
        elif isinstance(node.lhs, Subscript):
            indices = tuple(idx.name for idx in node.lhs.indices)
            self.current_table.define_expr(ExprSymbol(node.lhs.name.name, node, indices), node.constraints, node.rhs)
        else:
            raise RuntimeError('We should not get here')

    def visit_Name(self, node: Name):
        symbol = self.current_table.resolve(node.name)
        if symbol:
            if isinstance(symbol, ObjectSymbol):
                if node.name not in self.iterating_over:
                    raise CCLTypeError(node, f'Symbol {node.name} not bound to For/ForEach/Sum')

                if node.ctx == VarContext.LOAD and not self.inside_constraint:
                    if symbol.constraints is not None:
                        self.inside_constraint = True
                        self.visit(symbol.constraints)
                        self.inside_constraint = False
                node.result_type = symbol.symbol_type
            elif isinstance(symbol, ExprSymbol):
                self.visit(list(symbol.rules.values())[0])
            else:
                node.result_type = symbol.symbol_type
        if node.ctx == VarContext.LOAD and symbol is None:
            raise CCLSymbolError(node, f'Symbol {node.name} used but not defined')

    def visit_Subscript(self, node: Subscript):
        self.visit(node.name)
        for idx in node.indices:
            self.visit(idx)

        symbol = self.current_table.resolve(node.name.name)
        if isinstance(symbol, ParameterSymbol) and symbol.kind == ParameterType.ATOM:
            if len(node.indices) != 1:
                raise CCLTypeError(node, f'Atom parameter {node.name.name} must have one index only')
            if node.indices[0].result_type != ObjectType.ATOM:
                raise CCLTypeError(node, f'Atom parameter {node.name.name} was indexed by {node.indices[0].result_type}'
                                         ' not Atom')

            node.result_type = NumericType.FLOAT
        elif isinstance(symbol, ParameterSymbol) and symbol.kind == ParameterType.BOND:
            if len(node.indices) != 1:
                raise CCLTypeError(node, f'Bond parameter {node.name.name} must have one index only')
            if node.indices[0].result_type != ObjectType.BOND:
                raise CCLTypeError(node, f'Bond parameter {node.name.name} was indexed by {node.indices[0].result_type}'
                                         ' not Bond')

            node.result_type = NumericType.FLOAT
        elif isinstance(symbol, VariableSymbol) and symbol.types:
            index_types = tuple(idx.result_type for idx in node.indices)
            if symbol.types != index_types:
                raise CCLTypeError(node,
                                   f'Cannot index {node.name.name} with {index_types}, expected was {symbol.types}')

            node.result_type = symbol.kind
        elif isinstance(symbol, ExprSymbol):
            types = set()
            for constraint, expr in symbol.rules.items():
                self.visit(expr)
                types.add(expr.result_type)

            if len(types) > 1:
                raise CCLTypeError(node, f'Expressions for {node.name.name} have different types')

            node.result_type = list(types)[0]
        else:
            raise CCLTypeError(node, f'Cannot index type {node.name.result_type}')

    def visit_Assign(self, node: Assign):
        def check_compatible_types(lt, rt):
            if (rt == lt and rt in NumericType) or (lt == NumericType.FLOAT and rt == NumericType.INT):
                pass
            elif rt == NumericType.FLOAT and lt == NumericType.INT:  # Rounding not allowed
                raise CCLTypeError(node, f'Cannot assign Float to Int')
            else:  # Incompatible types
                raise CCLTypeError(node, f'Cannot assign {rt} to {lt}, only numeric types allowed for assignment')

        self.visit(node.rhs)
        rtype = node.rhs.result_type

        if isinstance(node.lhs, Subscript):
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
                if any(t not in ObjectType for t in types):
                    raise CCLTypeError(node, 'Cannot index by type other than Atom or Bond')

                table = self.current_table.find_parent_table(names)
                table.define(VariableSymbol(node.lhs.name.name, node, rtype, types))
        elif isinstance(node.lhs, Name):
            self.visit(node.lhs)
            ltype = node.lhs.result_type
            if ltype is None:  # Create a new symbol
                if rtype not in NumericType:
                    raise CCLTypeError(node, f'Cannot assign non numeric expression of type {rtype}')
                symbol = VariableSymbol(node.lhs.name, node, rtype, ())
                self.current_table.define(symbol)
            else:
                check_compatible_types(ltype, rtype)
        else:
            raise RuntimeError('We should not get here.')

    def visit_PredicateConstraint(self, node: Predicate):
        # TODO check for predicate name
        for arg in node.args:
            if isinstance(arg, Name) and not self.current_table.resolve(arg.name):
                raise CCLSymbolError(node, f'Predicate argument {arg.name} unknown')

    def visit_Number(self, node: Number):
        if isinstance(node.n, int):
            node.result_type = NumericType.INT
        else:
            node.result_type = NumericType.FLOAT

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.expr)
        if node.expr.result_type not in NumericType:
            raise CCLTypeError(node, f'Incompatible type for unary {node.op}')
        node.result_type = node.expr.result_type

    def visit_BinaryOp(self, node: BinaryOp):
        self.visit(node.left)
        self.visit(node.right)

        ltype = node.left.result_type
        rtype = node.right.result_type

        if ltype in NumericType and rtype in NumericType:
            if ltype == NumericType.INT and rtype == NumericType.INT:
                node.result_type = NumericType.INT
            else:
                node.result_type = NumericType.FLOAT
        else:
            raise CCLTypeError(node, f'Incompatible types for {node.op.value}: ' +
                               '{node.left.result_type} and {node.right.result_type}')

    def visit_Sum(self, node: Sum):
        self.iterating_over.add(node.name.name)
        self.visit(node.name)
        self.visit(node.expr)
        self.iterating_over.remove(node.name.name)

        if node.name.result_type not in ObjectType:
            raise CCLTypeError(node, f'Sum index has to be Atom or Bond, not {node.name.result_type}')

        node.result_type = node.expr.result_type
