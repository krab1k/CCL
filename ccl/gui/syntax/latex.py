"""Syntax highlighter for the LaTeX language."""

from PyQt5.QtGui import QTextDocument, QTextCharFormat
from PyQt5.QtCore import QRegExp
from typing import List, Tuple

from ccl.gui.syntax.common import STYLES, SyntaxHighlighter


class LatexHighlighter(SyntaxHighlighter):
    """Syntax highlighter for the LaTeX language."""
    braces = [r'\{', r'\}']

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        rules: List[Tuple[str, int, QTextCharFormat]] = []

        rules += [(fr'{b}', 0, STYLES['brace']) for b in self.braces]

        rules += [(r'\\[a-z]+', 0, STYLES['keyword']),
                  (r'\$', 0, STYLES['defclass']),
                  (r'\&', 0, STYLES['self']),
                  (r'_', 0, STYLES['brace']),
                  (r'\b[+-]?[0-9]+(?:\.[0-9]+)?\b', 0, STYLES['numbers'])]

        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
