import sys

from ccl import CCLMethod

if len(sys.argv) < 4:
    print('Not enough arguments')
    sys.exit(1)

method = CCLMethod.from_file(sys.argv[1])

options = {'parallelization': True,
           'seed': 11,
           'population_size': 100}
parameters = sys.argv[4] if len(sys.argv) == 5 else None
method.run_regression(molecules_file=sys.argv[2],
                      ref_chg_file=sys.argv[3],
                      parameters_file=parameters,
                      regression_options=options)
