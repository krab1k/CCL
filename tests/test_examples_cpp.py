"""Pytest C++ generator"""

import pytest
import tempfile
import subprocess
import shutil

from ccl.translate import translate
from ccl.errors import CCLCodeError


def test_examples_cpp(method):
    """Check whether C++ generated code compiles successfully"""
    tmpdir = tempfile.mkdtemp()
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        translate(data, 'cpp', output_dir=tmpdir)
    except CCLCodeError as e:
        shutil.rmtree(tmpdir)
        line = data.split('\n')[e.line - 1]
        pytest.fail(f'{method}:{e.line}:{e.column}: {line}: {e.message}')
    except Exception as e:
        pytest.fail(f'{method}: {e}')

    args = ['cmake', '.', '-DCHARGEFW2_DIR=/home/charge/chargefw2']
    p = subprocess.run(args, cwd=tmpdir, stderr=subprocess.PIPE)
    if p.returncode:
        pytest.fail(f'Cmake failed: {p.stderr.decode("utf-8")}')
    p = subprocess.run(['make'], cwd=tmpdir, stderr=subprocess.PIPE)
    if p.returncode:
        pytest.fail(f'Make failed: {p.stderr.decode("utf-8")}')

    shutil.rmtree(tmpdir)
