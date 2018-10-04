from pygments.lexer import RegexLexer, words
import pygments.token as token

KEYWORDS = ['to', 'such that', 'each', 'for', 'property', 'where', 'done', 'is', 'parameter', 'if', 'and', 'or', 'sum']

OPERATORS = [
    '=',
    # Comparison
    '==', '!=', '<', '<=', '>', '>=',
    # Arithmetic
    '\+', '-', '\*', '/', '\^'
]


class CCLLexer(RegexLexer):
    name = 'CCL'
    aliases = ['ccl']
    filenames = ['*.ccl']

    tokens = {
        'root': [
            (r'# .*?$', token.Comment.Single),
            (r'\s+', token.Whitespace),
            (r'[]():[,]', token.Punctuation),
            (r'(\d+\.\d*|\d*\.\d+)', token.Number),
            (r'(and|or|not)', token.Operator.Word),
            (r'=|==|!=|<|<=|>|>=|\+|\*|\^|-|/', token.Operator),
            (words(KEYWORDS, suffix=r'\b'), token.Keyword),
            (words(['atom', 'bond', 'common'], suffix=r'\b'), token.Name.Builtin),
            (r'("[^"]*")', token.String),
            (r'\w+', token.Text),
        ]
    }


def setup(sphinx):
    sphinx.add_lexer('ccl', CCLLexer())
