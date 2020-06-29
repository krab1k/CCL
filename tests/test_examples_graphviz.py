"""Pytest Graphviz generator"""

import pytest
import tempfile
import shutil
import os
import subprocess

from ccl.method import CCLMethod
from ccl.errors import CCLCodeError


def test_examples_graphviz(method):
    """Check whether Graphviz generated code compiles successfully"""
    tmpdir = tempfile.mkdtemp()
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        code = CCLMethod(data).translate('graphviz', annotate_results=True)
        assert code is not None
        with open(os.path.join(tmpdir, 'method.dot'), 'w') as f:
            f.write(code)
    except CCLCodeError as e:
        shutil.rmtree(tmpdir)
        line = data.split('\n')[e.line - 1]
        pytest.fail(f'{method}:{e.line}:{e.column}: {line}: {e.message}')
    except Exception as e:
        pytest.fail(f'{method}: {e}')

    args = ['dot', 'method.dot']
    p = subprocess.run(args, cwd=tmpdir, stderr=subprocess.PIPE)
    if p.returncode:
        pytest.fail(f'dot failed ({tmpdir}): {p.stderr.decode("utf-8")}')

    shutil.rmtree(tmpdir)
