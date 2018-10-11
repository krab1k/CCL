import pytest

from ccl import translate
from ccl.errors import CCLCodeError


def test_examples(method):
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        translate(data, None)
    except CCLCodeError as e:
        pytest.fail(f'{method}:{e.line}:{e.column}: {e.message}')


def test_bad(example):
    name, code = example
    with pytest.raises(CCLCodeError, message=name):
        translate(code, None)
