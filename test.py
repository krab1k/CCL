import sys
import antlr4
import antlr.CCLLexer
import antlr.CCLParser

from ccl_parser import Parser, CCLErrorListener
from ccl_symboltable import SymbolTable
from ccl_errors import CCLError
from generators.python import Generator

if len(sys.argv) != 2:
    print('Not enough arguments')
    sys.exit(1)

with open(sys.argv[1]) as f:
    data = f.read()

lexer = antlr.CCLLexer.CCLLexer(antlr4.InputStream(data))
token_stream = antlr4.CommonTokenStream(lexer)
parser = antlr.CCLParser.CCLParser(token_stream)
parser._listeners = [CCLErrorListener()]

try:
    tree = parser.method()
    ccl_parser = Parser()
    ast = ccl_parser.visit(tree)
    table = SymbolTable.create_from_ast(ast)
except CCLError as e:
    print('\nERROR: ' + str(e.message))
    print(f'\n{e.line:2d}:', data.split('\n')[e.line - 1])
    print(' ' * (3 + e.column), '^')
    sys.exit(1)

print('\n*** CCL ****\n')
print(data)

print('\n*** Python ***\n')
g = Generator(table)
code = g.visit(ast)

print(code)
