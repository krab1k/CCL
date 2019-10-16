"""CCL's translator module"""

import importlib
from typing import Optional, Union

from ccl.parser import process_source
from ccl.errors import CCLError


def translate(source: str, output_language: Optional[str] = None, **kwargs: Union[str, bool]) -> Optional[str]:
    """Translate CCL into the given output language"""

    ast, table = process_source(source)
    if output_language is not None:
        try:
            module = importlib.import_module(f'ccl.generators.{output_language}')
        except ImportError:
            raise CCLError(f'No such generator {output_language}')

        try:
            generator = getattr(module, output_language.capitalize())
        except AttributeError:
            raise RuntimeError(f'No such language: {output_language}')

        g = generator(table, **kwargs)
        return str(g.visit(ast))
    else:
        return None
