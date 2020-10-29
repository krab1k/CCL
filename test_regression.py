import sys

from ccl import CCLMethod

if len(sys.argv) < 4:
    print('Not enough arguments')
    sys.exit(1)

method = CCLMethod.from_file(sys.argv[1])

initial_seed = [
                'div(1.0, R(i, j))',
                'div(1.0, add(R(i, j), div(2.0, add(B(i), B(j)))',
                'div(1.2, add(R(i, j), div(2.4, add(B(i), B(j)))',
                'div(1.0, sqrt(add(square(R(i, j)), square(div(2.0, add(B(i), B(j)))))))',
                'div(1.0, sqrt(add(square(R(i, j)), square(add(div(0.5, B(i)), div(0.5, B(j)))))))',
                ]


options = {'population_size': 2000, 'generations': 10, 'top_results': 20, 'early_exit': True, 'require_symmetry': True,
           'seed': 35, 'initial_seed': [], 'initial_seed_mutations': 100, 'unique_population': True, 'metric': 'R2'}

parameters = sys.argv[4]
method.run_regression(molecules_file=sys.argv[2],
                      ref_chg_file=sys.argv[3],
                      parameters_file=parameters,
                      regression_options=options)
