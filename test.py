import sys
import antlr4

import antlr.CCLLexer
import antlr.CCLParser

from ccl_parser import Parser, CCLErrorListener
from ccl_symboltable import SymbolTable, CCLSymbolError, CCLTypeError


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
except SyntaxError as e:
    print(e)
    sys.exit(1)

ccl_parser = Parser()
ast = ccl_parser.visit(tree)
print('AST:')
ast.print_ast()

try:
    s = SymbolTable.create_from_ast(ast)
except (CCLTypeError, CCLSymbolError) as e:
    print('\n' + str(e))
    sys.exit(1)

print('\nGlobal symbol table:')
s.print()
