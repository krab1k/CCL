from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import QRegExp

from .common import STYLES, SyntaxHighlighter


class CCLHighlighter(SyntaxHighlighter):

    types = ['atom', 'bond', 'common']
    keywords = ['to', 'such that', 'each', 'for', 'property', 'where', 'done', 'is', 'parameter', 'if',
                'and', 'or', 'sum']

    braces = ['\(', '\)', '\[', '\]']
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '\^'
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        rules: list = []

        rules += [(fr'\b{w}\b', 0, STYLES['self']) for w in self.types]
        rules += [(fr'\b{w}\b', 0, STYLES['keyword']) for w in self.keywords]
        rules += [(fr'{o}', 0, STYLES['operator']) for o in self.operators]
        rules += [(fr'{b}', 0, STYLES['brace']) for b in self.braces]
        rules += [(r'#[^\n]*', 0, STYLES['comment']),
                  (r'"[^"]*"', 0, STYLES['string']),
                  (r'\b[+-]?[0-9]+(?:\.[0-9]+)?\b', 0, STYLES['numbers'])]

        self.rules: list = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
