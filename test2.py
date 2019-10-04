import sys
import antlr4

import ccl.antlr.CCL_Lexer as CCL_Lexer
import ccl.antlr.CCL as CCL_Parser
from ccl.errors import CCLError, CCLCodeError
from ccl.parser import Parser, CCLErrorListener
from ccl.translate import translate
from ccl.complexity import Complexity
from ccl.symboltable import SymbolTable


if len(sys.argv) != 2:
    print('Not enough arguments')
    sys.exit(1)

with open(sys.argv[1]) as f:
    data = f.read()


print('\n*** CCL ****\n')
print(data)

lexer = CCL_Lexer.CCL_Lexer(antlr4.InputStream(data))
token_stream = antlr4.CommonTokenStream(lexer)
parser = CCL_Parser.CCL(token_stream)
parser._listeners = [CCLErrorListener()]

tree = parser.method()  # type: ignore
ccl_parser = Parser()
ast = ccl_parser.visit(tree)
table = SymbolTable.create_from_ast(ast)

print('\n*** Complexity ****\n')
complexity = Complexity(table).visit(ast)
print(complexity)
