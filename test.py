import sys
import antlr4
import ccl.antlr.CCLLexer
import ccl.antlr.CCLParser

from ccl.parser import Parser, CCLErrorListener
from ccl.symboltable import SymbolTable
from ccl.errors import CCLError
from ccl.generators.python import Python

if len(sys.argv) != 2:
    print('Not enough arguments')
    sys.exit(1)

with open(sys.argv[1]) as f:
    data = f.read()

lexer = ccl.antlr.CCLLexer.CCLLexer(antlr4.InputStream(data))
token_stream = antlr4.CommonTokenStream(lexer)
parser = ccl.antlr.CCLParser.CCLParser(token_stream)
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
g = Python(table)
code = g.visit(ast)

print(code)
