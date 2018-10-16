import pytest

from ccl import translate
from ccl.errors import CCLCodeError


def test_bad(example):
    name, code = example
    with pytest.raises(CCLCodeError, message=name):
        translate(code, None)

