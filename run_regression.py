import argparse

from ccl import CCLMethod


def main():
    parser = argparse.ArgumentParser()

    files = parser.add_argument_group('Files')
    files.add_argument('--ccl-code', type=str, required=True, help='CCL code skeleton')
    files.add_argument('--molecules', type=str, required=True, help='Input set of molecules')
    files.add_argument('--ref-charges', type=str, required=True, help='Reference charges to compare to')
    files.add_argument('--parameters', type=str, required=True, help='Parameters required for the method')
    files.add_argument('--seeded-individuals', type=str, default=None, help='File with individuals to start with')
    files.add_argument('--save-best', type=str, default=None, help='File to store the best individuals')

    options = parser.add_argument_group('Regression options')
    options.add_argument('--population-size', type=int, default=500, help='Size of the initial population')
    options.add_argument('--crossover-probability', type=float, default=0.8, help='Crossover probability')
    options.add_argument('--mutation-probability', type=float, default=0.3, help='Mutation probability')
    options.add_argument('--generations', type=int, default=50, help='Number of generations')
    options.add_argument('--no-unique-population', action='store_false', dest='unique_population',
                         help='Don\'t require unique initial population')
    options.add_argument('--seed', type=int, default=None, help='Seed for the random number generator')
    options.add_argument('--require-symmetry', action='store_true', default=False,
                         help='Require symmetry in atom/bond objects in the initial population')
    options.add_argument('--metric', type=str, choices=['R2', 'RMSD', 'COMBINED'], default='RMSD',
                         help='Metric to evaluate fitness')
    options.add_argument('--ncpus', type=int, default=None, help='Number of CPUs to use')
    options.add_argument('--early-exit', action='store_true', default=False,
                         help='Stop the computation if the individual has RMSD < 0.0001 or R2 > 0.9999 depending'
                              ' on the metric used')
    options.add_argument('--initial-seed-mutations', type=int, default=10,
                         help='Number of mutations to generate from each seeded individual')
    options.add_argument('--top-results', type=int, default=20, help='Number of results to report/save at the end')
    options.add_argument('--max-constant-allowed', type=int, default=None,
                         help='Max constant that can appear in the initial population')
    options.add_argument('--use-math-functions', action='store_true', default=False,
                         help='Allow additional math functions like sin or cos')
    options.add_argument('--allow-random-constants', action='store_true', default=False,
                         help='Allow to generate random constants in range [0; 2]')
    options.add_argument('--required-symbols', type=str, nargs='+', default=[],
                         help='List of symbols that must appear in each individual of the initial population')
    options.add_argument('--disabled-symbols', type=str, nargs='+', default=[],
                         help='List of symbols that must not appear in each individual of the initial population')

    sys_dirs = parser.add_argument_group('System directories')
    sys_dirs.add_argument('--eigen-include', type=str, default='/usr/include/eigen3',
                          help='Directory with Eigen3 include files')
    sys_dirs.add_argument('--chargefw2-dir', type=str, default='/opt/chargefw2',
                          help='ChargeFW2 installation directory')

    parsed_options = vars(parser.parse_args())

    parsed_options['required_symbols'] = set(parsed_options['required_symbols'])
    parsed_options['disabled_symbols'] = set(parsed_options['disabled_symbols'])

    method = CCLMethod.from_file(parsed_options['ccl_code'])

    method.run_regression(molecules_file=parsed_options['molecules'],
                          ref_chg_file=parsed_options['ref_charges'],
                          parameters_file=parsed_options['parameters'],
                          regression_options=parsed_options)


if __name__ == '__main__':
    main()
