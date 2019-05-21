import pytest

from ccl import translate
from ccl.errors import CCLCodeError


def test_examples(method):
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        translate(data, None)
    except CCLCodeError as e:
        line = data.split('\n')[e.line - 1]
        pytest.fail(f'{method}:{e.line}:{e.column}: {line}: {e.message}')
    except Exception as e:
        pytest.fail(f'{method}: {e}')
