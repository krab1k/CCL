"""Pytest common empirical methods"""

import pytest

from ccl.method import CCLMethod
from ccl.errors import CCLCodeError


def test_examples(method):
    """Check whether all example methods are valid in CCL"""
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        CCLMethod(data)
    except CCLCodeError as e:
        line = data.split('\n')[e.line - 1]
        pytest.fail(f'{method}:{e.line}:{e.column}: {line}: {e.message}')
    except Exception as e:
        pytest.fail(f'{method}: {e}')
