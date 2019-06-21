import pytest
import tempfile
import shutil
import os
import subprocess

from ccl import translate
from ccl.errors import CCLCodeError


def test_examples_latex(method):
    tmpdir = tempfile.mkdtemp()
    with open(f'examples/{method}') as f:
        data = f.read()
    try:
        latex = translate(data, 'latex', full_output=True)
        with open(os.path.join(tmpdir, 'method.tex'), 'w') as f:
            f.write(latex)
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
