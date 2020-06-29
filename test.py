import sys

from ccl.errors import CCLError
from ccl.method import CCLMethod

if len(sys.argv) != 2:
    print('Not enough arguments')
    sys.exit(1)

try:
    method = CCLMethod.from_file(sys.argv[1])
    print('\n*** CCL ****\n')
    print(method.source)
    print('\n*** Translated ****\n')
    print(method.translate('cpp', output_dir='/tmp/haha', full_output=True))
    print('Complexity: ', method.get_complexity(asymptotic=True))
except CCLError as e:
    print(e)
    sys.exit(1)
