"""CCL's exceptions"""

from typing import Optional

from ccl.ast import ASTNode


class CCLError(Exception):
    def __init__(self, node: Optional[ASTNode], message: str) -> None:
        super().__init__()
        if node is not None:
            self.line: int = node.line
            self.column: int = node.column
        else:
            self.line = -1
            self.column = -1
        self.message: str = message


class CCLSyntaxError(CCLError):
    pass


class CCLSymbolError(CCLError):
    pass


class CCLTypeError(CCLError):
    pass
