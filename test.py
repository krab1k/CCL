import sys
import antlr4
import antlr.CCLLexer
import antlr.CCLParser

from ccl_parser import Parser


if len(sys.argv) != 2:
    print('Not enough arguments')
    sys.exit(1)

with open(sys.argv[1]) as f:
    data = f.read()

lexer = antlr.CCLLexer.CCLLexer(antlr4.InputStream(data))
token_stream = antlr4.CommonTokenStream(lexer)
parser = antlr.CCLParser.CCLParser(token_stream)

tree = parser.method()

ccl_parser = Parser()
ccl_parser.visit(tree)

for a in ccl_parser.annotations:
    print(a)

for s in ccl_parser.statements:
    print(s)

