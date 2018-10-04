from pygments.lexers.parsers import AntlrLexer


def setup(sphinx):
    sphinx.add_lexer('antlr', AntlrLexer())
