from ccl.ast import ASTNode


class CCLError(Exception):
    def __init__(self, node: ASTNode, message: str) -> None:
        super().__init__()
        self.line: int = node._line
        self.column: int = node._column
        self.message: str = message


class CCLSyntaxError(CCLError):
    pass


class CCLSymbolError(CCLError):
    pass


class CCLTypeError(CCLError):
    pass
