"""CCL's exceptions"""

from typing import Optional

from ccl.ast import ASTNode


class CCLError(Exception):
    """General error in CCL code"""


class CCLCodeError(CCLError):
    def __init__(self, node: Optional[ASTNode], message: str) -> None:
        super().__init__()
        if node is not None:
            self.line: int = node.line
            self.column: int = node.column
        else:
            self.line = -1
            self.column = -1
        self.message: str = message

    def __str__(self) -> str:
        return self.message


class CCLSyntaxError(CCLCodeError):
    pass


class CCLSymbolError(CCLCodeError):
    pass


class CCLTypeError(CCLCodeError):
    pass
