from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import QRegExp

from .common import STYLES, SyntaxHighlighter


class LatexHighlighter(SyntaxHighlighter):
    braces = ['\{', '\}']

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        rules: list = []

        rules += [(fr'{b}', 0, STYLES['brace']) for b in self.braces]

        rules += [(r'\\[a-z]+', 0, STYLES['keyword']),
                  (r'\$', 0, STYLES['defclass']),
                  (r'\&', 0, STYLES['self']),
                  (r'_', 0, STYLES['brace']),
                  (r'\b[+-]?[0-9]+(?:\.[0-9]+)?\b', 0, STYLES['numbers'])]

        self.rules: list = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
