"""CCL Method"""

import importlib
from typing import Union

import ccl.types
from ccl.parser import process_source
from ccl.symboltable import SymbolTable
from ccl.ast import Method
from ccl.errors import CCLError
from ccl.complexity import Complexity


class CCLMethod:
    """CCL method"""

    def __init__(self, source: str):
        ast, table = process_source(source)
        self.source: str = source
        self.symbol_table: SymbolTable = table
        self.ast: Method = ast

    @property
    def name(self) -> str:
        return self.ast.name

    def has_parameters(self) -> bool:
        for symbol in self.symbol_table.parent.symbols.values():
            if isinstance(symbol.symbol_type, ccl.types.ParameterType):
                return True
        return False

    @classmethod
    def from_file(cls, filename: str) -> 'CCLMethod':
        with open(filename) as f:
            data = f.read()

        return CCLMethod(data)

    def get_complexity(self, asymptotic: bool = True) -> str:
        """Return complexity of a method in CCL"""
        return Complexity(self.symbol_table, asymptotic=asymptotic).visit(self.ast)

    def translate(self, output_language: str, **kwargs: Union[str, bool]) -> str:
        """Translate CCL into the given output language"""

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
