"""Common highlighting definitions"""

# Modified code from from https://github.com/art1415926535/PyQt5-syntax-highlighting

from typing import List, Union
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter


def _format(color: Union[List[int], str], style: str = '') -> QTextCharFormat:
    """Return a QTextCharFormat with the given attributes."""
    _color = QColor()
    if isinstance(color, str):
        _color.setNamedColor(color)
    else:
        _color.setRgb(color[0], color[1], color[2])

    f = QTextCharFormat()
    f.setForeground(_color)
    if 'bold' in style:
        f.setFontWeight(QFont.Bold)
    if 'italic' in style:
        f.setFontItalic(True)

    return f

# Syntax styles that can be shared by all languages


STYLES = {
    'keyword': _format([200, 120, 50], 'bold'),
    'operator': _format([150, 150, 150]),
    'brace': _format('darkGray'),
    'defclass': _format([35, 135, 20], 'bold'),
    'string': _format([20, 110, 100]),
    'string2': _format([30, 120, 110]),
    'comment': _format([128, 128, 128]),
    'self': _format([150, 85, 140], 'italic'),
    'numbers': _format([100, 150, 240]),
}


class SyntaxHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text: str) -> None:
        """Apply syntax highlighting to the given block of text."""
        # Do other syntax formatting
        for expression, nth, fmt in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)
