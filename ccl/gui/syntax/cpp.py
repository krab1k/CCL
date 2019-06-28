"""Syntax highlighter for the C++ language."""

from PyQt5.QtGui import QTextDocument, QTextCharFormat
from PyQt5.QtCore import QRegExp
from typing import List, Tuple

from ccl.gui.syntax.common import STYLES, SyntaxHighlighter


class CppHighlighter(SyntaxHighlighter):
    """Syntax highlighter for the C++ language."""
    # C++ keywords

    keywords = ['alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel', 'atomic_commit', 'atomic_noexcept',
                'auto', 'bitand', 'bitor', 'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t',
                'class', 'compl', 'concept', 'const', 'consteval', 'constexpr', 'const_cast', 'continue', 'co_await',
                'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast', 'else',
                'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend', 'goto', 'if', 'inline',
                'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator',
                'or', 'or_eq', 'private', 'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast', 'requires',
                'return', 'short', 'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct', 'switch',
                'synchronized', 'template', 'this', 'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid',
                'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor',
                'xor_eq',
                ]

    # C++ operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        r'\+', '-', r'\*', '/', r'\%',
        # In-place
        r'\+=', '-=', r'\*=', '/=', r'\%=',
        # Bitwise
        r'\^', r'\|', r'\&', r'\~', '>>', '<<',
        # Increment
        '++', '--'
    ]

    # C++ braces
    braces = [
        r'\{', r'\}', r'\(', r'\)', r'\[', r'\]',
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        rules: List[Tuple[str, int, QTextCharFormat]] = []

        # Keyword, operator, and brace rules
        rules += [(fr'\b{w}\b', 0, STYLES['keyword']) for w in self.keywords]
        rules += [(fr'{o}', 0, STYLES['operator']) for o in self.operators]
        rules += [(fr'{b}', 0, STYLES['brace']) for b in self.braces]

        # All other rules
        rules += [
            # 'this'
            (r'\bthis\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),

            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '//' until a newline
            (r'//[^\n]*', 0, STYLES['comment']),

            # Preprocessor directives
            (r'#[^\n]*', 0, STYLES['string']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]
