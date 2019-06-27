"""Pytest invalid code"""

import pytest
import re

from ccl import translate
from ccl.errors import CCLCodeError


def test_bad(example):
    """Test invalid constructs in CCL"""
    name, code = example
    with pytest.raises(CCLCodeError, match=re.escape(name)):
        translate(code, None)
