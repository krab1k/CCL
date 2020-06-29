"""Pytest invalid code"""

import pytest
import re

from ccl.method import CCLMethod
from ccl.errors import CCLCodeError


def test_bad(example):
    """Test invalid constructs in CCL"""
    name, code = example
    with pytest.raises(CCLCodeError, match=re.escape(name)):
        CCLMethod(code)
