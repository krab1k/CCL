"""Syntax highlighter for the CCL language."""

from PyQt5.QtGui import QTextDocument, QTextCharFormat
from PyQt5.QtCore import QRegExp
from typing import List, Tuple

from ccl.gui.syntax.common import STYLES, SyntaxHighlighter


class CCLHighlighter(SyntaxHighlighter):
    """Syntax highlighter for the CCL language."""

    types = ['atom', 'bond', 'common']
    keywords = ['parameter', 'such that', 'where', 'done', 'is', 'and', 'or', 'not', 'for each', 'for', 'to', 'if',
                'of', 'sum', 'cutoff', 'cover', 'EE']

    braces = [r'\(', r'\)', r'\[', r'\]']
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        r'\+', '-', r'\*', '/', r'\^'
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        rules: List[Tuple[str, int, QTextCharFormat]] = []

        rules += [(fr'\b{w}\b', 0, STYLES['self']) for w in self.types]
        rules += [(fr'\b{w}\b', 0, STYLES['keyword']) for w in self.keywords]
        rules += [(fr'{o}', 0, STYLES['operator']) for o in self.operators]
        rules += [(fr'{b}', 0, STYLES['brace']) for b in self.braces]
        rules += [(r'#[^\n]*', 0, STYLES['comment']),
                  (r'"[^"]*"', 0, STYLES['string']),
                  (r'\b[+-]?[0-9]+(?:\.[0-9]+)?\b', 0, STYLES['numbers'])]

        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
