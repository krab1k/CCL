"""Pytest LaTeX generator"""

import pytest
import tempfile
import shutil
import os
import subprocess

from ccl.method import CCLMethod
from ccl.errors import CCLCodeError


def test_examples_latex(method):
    """Check whether LaTeX generated code compiles successfully"""
    tmpdir = tempfile.mkdtemp()
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        code = CCLMethod(data).translate('latex', full_output=True)
        assert code is not None
        with open(os.path.join(tmpdir, 'method.tex'), 'w') as f:
            f.write(code)
    except CCLCodeError as e:
        shutil.rmtree(tmpdir)
        line = data.split('\n')[e.line - 1]
        pytest.fail(f'{method}:{e.line}:{e.column}: {line}: {e.message}')
    except Exception as e:
        pytest.fail(f'{method}: {e}')

    args = ['xelatex', 'method.tex']
    p = subprocess.run(args, cwd=tmpdir, stderr=subprocess.PIPE)
    if p.returncode:
        pytest.fail(f'XeLaTeX failed ({tmpdir}): {p.stderr.decode("utf-8")}')

    shutil.rmtree(tmpdir)
