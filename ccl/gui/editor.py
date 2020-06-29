"""Simple editor for CCL"""

import sys
import importlib
from typing import Optional
from PyQt5.QtWidgets import QApplication, QWidget, QPlainTextEdit, QVBoxLayout, QAction, QLabel, QComboBox
from PyQt5.QtGui import QFont, QTextCursor, QTextBlockFormat, QColor

import ccl.generators
from ccl.method import CCLMethod
from ccl.errors import CCLCodeError
from ccl.gui.syntax.common import SyntaxHighlighter
from ccl.gui.syntax.ccl import CCLHighlighter


class Editor(QWidget):
    def __init__(self, initial_file: Optional[str]) -> None:
        super().__init__()
        self.editor: QPlainTextEdit = QPlainTextEdit(self)
        self.code: QPlainTextEdit = QPlainTextEdit(self)
        self.status: QLabel = QLabel(self)
        self.language_box: QComboBox = QComboBox(self)
        self.language: str = ccl.generators.BACKENDS[0]
        self.editor_highlight: CCLHighlighter = CCLHighlighter(self.editor.document())
        self.code_highlight: Optional[SyntaxHighlighter] = None
        self.initUI()

        if initial_file is not None:
            self.load_file(initial_file)

    def load_file(self, filename: str) -> None:
        with open(filename) as f:
            data = f.read()

        self.editor.setPlainText(data)

    def highlight_error(self, line: int) -> None:
        block = self.editor.document().findBlockByLineNumber(line - 1)
        cursor = QTextCursor(block)
        fmt = QTextBlockFormat()
        fmt.setBackground(QColor(255, 220, 190))
        cursor.setBlockFormat(fmt)

    def clear_highlight(self) -> None:
        fmt = QTextBlockFormat()
        fmt.setBackground(QColor('white'))
        block = self.editor.document().firstBlock()
        while block.isValid():
            cursor = QTextCursor(block)
            cursor.setBlockFormat(fmt)
            block = block.next()

    def ccl_changed(self) -> None:
        self.editor.blockSignals(True)
        self.clear_highlight()
        data = self.editor.toPlainText()
        if data:
            try:
                code = CCLMethod(data).translate(self.language)
                assert code is not None
                self.code.setPlainText(code)
                self.status.setText('OK')

            except CCLCodeError as e:
                self.status.setText(f'{e.line}: {e.message}')
                self.code.setPlainText('')
                self.highlight_error(e.line)
            except NotImplementedError as e:
                self.status.setText(str(e))
        else:
            self.status.setText('')
            self.code.setPlainText('')

        self.editor.blockSignals(False)

    def language_changed(self) -> None:
        language = self.language_box.currentText()
        try:
            module = importlib.import_module(f'ccl.gui.syntax.{language}')
            highlighter = getattr(module, language.capitalize() + 'Highlighter')
            self.code_highlight = highlighter(self.code.document())
        except ModuleNotFoundError:
            self.code_highlight = None

        self.language = language
        self.ccl_changed()

    def initUI(self) -> None:
        quit_action = QAction(self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.close)  # type: ignore
        self.addAction(quit_action)

        font = QFont()
        font.setFamily('DejavuSansMono')
        font.setStyleHint(QFont.Monospace)

        self.editor.setFont(font)
        self.code.setFont(font)
        self.code.setReadOnly(True)

        self.editor.textChanged.connect(self.ccl_changed)  # type: ignore

        layout = QVBoxLayout(self)
        self.language_box.addItems(ccl.generators.BACKENDS)
        self.language_box.currentIndexChanged.connect(self.language_changed)
        self.language = self.language_box.currentText()
        self.language_changed()

        layout.addWidget(self.language_box)
        layout.addWidget(self.editor)
        layout.addWidget(self.status)
        layout.addWidget(self.code)
        self.setLayout(layout)

        self.showMaximized()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    file = sys.argv[1] if len(sys.argv) > 1 else None
    editor = Editor(file)
    sys.exit(app.exec_())
