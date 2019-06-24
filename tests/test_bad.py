"""Pytest invalid code"""

import pytest

from ccl import translate
from ccl.errors import CCLCodeError


def test_bad(example):
    """Test invalid constructs in CCL"""
    name, code = example
    with pytest.raises(CCLCodeError):
        translate(code, None)
