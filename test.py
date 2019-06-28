import sys

from ccl.errors import CCLError, CCLCodeError
from ccl.translate import translate

if len(sys.argv) != 2:
    print('Not enough arguments')
    sys.exit(1)

with open(sys.argv[1]) as f:
    data = f.read()


print('\n*** CCL ****\n')
print(data)


print('\n*** Translated ****\n')
try:
    print(translate(data, 'cpp', output_dir='/tmp/output'))
except CCLCodeError as e:
    print('\nERROR: ' + str(e.message))
    print(f'\n{e.line:2d}:', data.split('\n')[e.line - 1])
    print(' ' * (3 + e.column), '^')
    sys.exit(1)
except CCLError as e:
    print(e)
    sys.exit(1)
