import importlib
from typing import Optional
import antlr4

import ccl.antlr.CCLLexer
import ccl.antlr.CCLParser
from ccl.errors import CCLError
from ccl.symboltable import SymbolTable
from ccl.parser import Parser, CCLErrorListener


def translate(source: str, output_language: Optional[str]) -> Optional[str]:
    if output_language is not None:
        try:
            module = importlib.import_module(f'ccl.generators.{output_language}')
        except ImportError:
            raise CCLError(f'No such generator {output_language}')

        generator = getattr(module, output_language.capitalize())

    lexer = ccl.antlr.CCLLexer.CCLLexer(antlr4.InputStream(source))
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = ccl.antlr.CCLParser.CCLParser(token_stream)
    parser._listeners = [CCLErrorListener()]

    tree = parser.method()
    ccl_parser = Parser()
    ast = ccl_parser.visit(tree)
    table = SymbolTable.create_from_ast(ast)

    if output_language is not None:
        g = generator(table)
        code = str(g.visit(ast))
        return code
