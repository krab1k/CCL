"""Regression options"""


default_options = {
    'use_math_functions': False,
    'population_size': 200,
    'crossover_probability': 0.8,
    'mutation_probability': 0.2,
    'generations': 15,
    'top_results': 5,
    'unique_population': True,
    'ncpus': None,
    'seed': None,
    'chargefw2_dir': '/opt/chargefw2',
    'eigen_include': '/usr/include/eigen3',
    'early_exit': False,
    'require_symmetry': False,
    'seeded_individuals': None,
    'initial_seed_mutations': 10,
    'symbol_counts': {'exp': (None, 1)},
    'results': None,
    'max_tree_height': 17,
    'max_constant_allowed': None,
    'allow_random_constants': False,
    'metric': 'RMSD'
}


def print_options(options: dict):
    """Prints options for the regression"""
    print('*** Settings ***')
    max_size = max(len(opt) for opt in options)
    for opt, value in options.items():
        print(f'{opt:<{max_size + 1}}', value)
