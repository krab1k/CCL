"""Syntax highlighter for the Dot language."""

from PyQt5.QtGui import QTextDocument, QTextCharFormat
from PyQt5.QtCore import QRegExp
from typing import List, Tuple

from ccl.gui.syntax.common import STYLES, SyntaxHighlighter


class GraphvizHighlighter(SyntaxHighlighter):
    """Syntax highlighter for the Dot language."""
    braces = [r'\[', r'\]', r'\{', r'\}']
    keywords = ['digraph', 'label']
    operators = ['=', '->']

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        rules: List[Tuple[str, int, QTextCharFormat]] = []

        rules += [(fr'{w}', 0, STYLES['keyword']) for w in self.keywords]
        rules += [(fr'{o}', 0, STYLES['operator']) for o in self.operators]
        rules += [(fr'{b}', 0, STYLES['brace']) for b in self.braces]

        rules += [(r'node\d*', 0, STYLES['self']),
                  (r'"[^"]*"', 0, STYLES['string']),
                  (r'label = <(.*)>', 1, STYLES['string']),
                  (r'\b[+-]?[0-9]+(?:\.[0-9]+)?\b', 0, STYLES['numbers'])]

        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
