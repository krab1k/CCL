"""CCL's translator module"""

import importlib
from typing import Optional, Union
import antlr4

import ccl.antlr.CCL_Lexer as CCL_Lexer
import ccl.antlr.CCL as CCL_Parser
from ccl.errors import CCLError
from ccl.symboltable import SymbolTable
from ccl.parser import Parser, CCLErrorListener


def translate(source: str, output_language: Optional[str] = None, **kwargs: Union[str, bool]) -> Optional[str]:
    """Translate CCL into the given output language"""

    lexer = CCL_Lexer.CCL_Lexer(antlr4.InputStream(source))
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = CCL_Parser.CCL(token_stream)
    parser._listeners = [CCLErrorListener()]

    tree = parser.method()  # type: ignore
    ccl_parser = Parser()
    ast = ccl_parser.visit(tree)
    table = SymbolTable.create_from_ast(ast)

    if output_language is not None:
        try:
            module = importlib.import_module(f'ccl.generators.{output_language}')
        except ImportError:
            raise CCLError(f'No such generator {output_language}')

        try:
            generator = getattr(module, output_language.capitalize())
        except AttributeError:
            raise RuntimeError(f'No such language: {output_language}')

        g = generator(table, **kwargs)
        code = str(g.visit(ast))
        return code
    else:
        return None
