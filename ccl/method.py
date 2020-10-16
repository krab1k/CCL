"""CCL Method"""

import importlib
from typing import Union, Optional

import ccl.ast
import ccl.types
from ccl.parser import process_source
from ccl.symboltable import SymbolTable
from ccl.errors import CCLError
from ccl.complexity import Complexity
from ccl.regression import generate


class CCLMethod:
    """CCL method"""

    def __init__(self, source: str):
        ast, table = process_source(source)
        self.source: str = source
        self.symbol_table: SymbolTable = table
        self.ast: ccl.ast.Method = ast

    @classmethod
    def from_file(cls, filename: str) -> 'CCLMethod':
        """Create CCL method from a source file"""
        with open(filename) as f:
            data = f.read()

        return CCLMethod(data)

    @property
    def name(self) -> str:
        """Returns name of the method"""
        return self.ast.name

    def has_parameters(self) -> bool:
        """Checks whether the method uses some parameters that has to be loaded from file"""
        for symbol in self.symbol_table.parent.symbols.values():
            if isinstance(symbol.symbol_type, ccl.types.ParameterType):
                return True
        return False

    def get_regression_expr(self) -> ccl.ast.ASTNode:
        """Return the expression node {} used for symbolic regression"""
        return ccl.ast.search_ast_element(self.ast, ccl.ast.RegressionExpr((-1, -1)))

    def get_complexity(self, asymptotic: bool = True) -> str:
        """Return complexity of a method in CCL"""

        if self.get_regression_expr() is not None:
            raise CCLError(f'Cannot compute complexity if the method has an regression expression')

        return Complexity(self.symbol_table, asymptotic=asymptotic).visit(self.ast)

    def translate(self, output_language: str, **kwargs: Union[str, bool]) -> str:
        """Translate CCL into the given output language"""

        if self.get_regression_expr() is not None:
            raise CCLError(f'Cannot translate the method if it contains an regression expression')

        try:
            module = importlib.import_module(f'ccl.generators.{output_language}')
        except ImportError:
            raise CCLError(f'No such generator {output_language}')

        try:
            generator = getattr(module, output_language.capitalize())
        except AttributeError:
            raise RuntimeError(f'No such language: {output_language}')

        g = generator(self.symbol_table, **kwargs)
        return str(g.visit(self.ast))

    def run_regression(self, molecules_file: str, ref_chg_file: str, parameters_file: Optional[str] = None,
                       regression_options: Optional[dict] = None):
        """Run a symbolic regression for the method to find which expression to use instead of {} placeholder"""

        generate(self, molecules_file, ref_chg_file, parameters_file, regression_options)
