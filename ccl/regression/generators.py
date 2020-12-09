"""Generate sympy or ccl code from an individual"""

import decimal

import sympy
from deap import gp


def generate_sympy_expr(expr: gp.PrimitiveTree, ccl_objects: dict) -> sympy.Expr:
    """Generates optimized sympy expression from an individual"""
    string = ''
    stack = []
    distance_name = ccl_objects.get('distance', None)
    variables = {}

    atom_names = ccl_objects['atom_objects']

    if distance_name is not None:
        variables[distance_name] = sympy.Function(distance_name, positive=True, real=True)

    for fn in ccl_objects['single_argument']:
        variables[fn] = sympy.Function(fn, real=True)

    for node in expr:
        stack.append((node, []))
        while len(stack[-1][1]) == stack[-1][0].arity:
            prim, args = stack.pop()
            if prim.name == 'add':
                string = f'({args[0]}) + ({args[1]})'
            elif prim.name == 'sub':
                string = f'({args[0]}) - ({args[1]})'
            elif prim.name == 'mul':
                string = f'({args[0]}) * ({args[1]})'
            elif prim.name == 'div':
                string = f'({args[0]}) / ({args[1]})'
            elif prim.name in {'sqrt', 'cbrt', 'exp'}:
                string = f'{prim.name}({args[0]})'
            elif prim.name == 'square':
                string = f'({args[0]}) ** 2'
            elif prim.name == 'cube':
                string = f'({args[0]}) ** 3'
            elif prim.name == 'inv':
                string = f'(1 / ({args[0]}))'
            elif prim.name == 'double':
                string = f'(2 * ({args[0]}))'
            elif prim.name == 'half':
                string = f'(0.5 * ({args[0]}))'
            elif distance_name is not None and prim.name == distance_name:
                string = f'{distance_name}({atom_names[0]}{atom_names[1]})'
            elif prim.name.startswith('_term'):
                name, atom_name = prim.name.split('_')[-2:]
                string = f'{name}({atom_name})'
            elif prim.name.startswith('_sym_add'):
                name = prim.name.split('_')[-1]
                string = f'({name}({atom_names[0]}) + {name}({atom_names[1]}))'
            elif prim.name.startswith('_sym_inv_add'):
                name = prim.name.split('_')[-1]
                string = f'(1 / {name}({atom_names[0]}) + 1 / {name}({atom_names[1]}))'
            elif prim.name.startswith('_sym_mul'):
                name = prim.name.split('_')[-1]
                string = f'({name}({atom_names[0]}) * {name}({atom_names[1]}))'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    try:
        sympy_expr = sympy.sympify(string, locals=variables).evalf(2)
    except:
        raise RuntimeError('Sympy cannot process the expression')

    return sympy_expr


def generate_optimized_ccl_code(expr: gp.PrimitiveTree, ccl_objects: dict) -> str:
    """Generates somewhat optimized CCL code for an individual"""
    string = ''
    stack = []
    distance_name = ccl_objects.get('distance', None)
    atom_names = ccl_objects['atom_objects']

    for node in expr:
        stack.append((node, []))
        while len(stack[-1][1]) == stack[-1][0].arity:
            prim, args = stack.pop()
            if prim.name == 'add':
                try:
                    string = str(decimal.Decimal(args[0]) + decimal.Decimal(args[1]))
                except decimal.InvalidOperation:
                    if args[0] < args[1]:
                        string = f'({args[0]} + {args[1]})'
                    else:
                        string = f'({args[1]} + {args[0]})'
            elif prim.name == 'sub':
                if args[1] == '0.0':
                    string = f'({args[0]})'
                else:
                    try:
                        string = str(decimal.Decimal(args[0]) - decimal.Decimal(args[1]))
                    except decimal.InvalidOperation:
                        string = f'({args[0]} - {args[1]})'
            elif prim.name == 'mul':
                if args[0] == '0.0' or args[1] == '0.0':
                    string = '0.0'
                elif args[0] == '1.0':
                    string = f'({args[1]})'
                elif args[1] == '1.0':
                    string = f'({args[0]})'
                elif args[0] < args[1]:
                    string = f'({args[0]}) * ({args[1]})'
                else:
                    string = f'({args[1]}) * ({args[0]})'
            elif prim.name == 'div':
                if args[0] == args[1]:
                    string = '1.0'
                elif args[1] == '1.0':
                    string = f'({args[0]})'
                else:
                    string = f'({args[0]}) / ({args[1]})'
            elif prim.name == 'sqrt':
                string = f'sqrt({args[0]})'
            elif prim.name == 'cbrt':
                string = f'({args[0]}) ^ (1.0 / 3.0)'
            elif prim.name == 'square':
                string = f'({args[0]}) ^ 2.0'
            elif prim.name == 'cube':
                string = f'({args[0]}) ^ 3.0'
            elif prim.name == 'exp':
                string = f'exp({args[0]})'
            elif prim.name == 'inv':
                string = f'(1.0 / ({args[0]}))'
            elif prim.name == 'double':
                string = f'(2.0 * ({args[0]}))'
            elif prim.name == 'half':
                string = f'(0.5 * ({args[0]}))'
            elif prim.name.startswith('_sym_add'):
                name = prim.name.split('_')[-1]
                string = f'({name}[{atom_names[0]}] + {name}[{atom_names[1]}])'
            elif prim.name.startswith('_sym_inv_add'):
                name = prim.name.split('_')[-1]
                string = f'(1 / {name}[{atom_names[0]}] + 1.0 / {name}[{atom_names[1]}])'
            elif prim.name.startswith('_sym_mul'):
                name = prim.name.split('_')[-1]
                string = f'({name}[{atom_names[0]}] * {name}[{atom_names[1]}])'
            elif distance_name is not None and prim.name == distance_name:
                string = f'{distance_name}[{atom_names[0]}, {atom_names[1]}]'
            elif prim.name.startswith('_term'):
                name, atom_name = prim.name.split('_')[-2:]
                string = f'{name}[{atom_name}]'
            else:
                string = prim.format(*args)
            if len(stack) == 0:
                break  # If stack is empty, all nodes should have been seen
            stack[-1][1].append(string)

    return string
