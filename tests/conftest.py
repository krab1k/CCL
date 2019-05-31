import os


def pytest_generate_tests(metafunc):
    if 'method' in metafunc.fixturenames:
        method_names = os.listdir('examples/')
        metafunc.parametrize('method', method_names)
    if 'example' in metafunc.fixturenames:
        with open('tests/bad_cases') as f:
            data = f.readlines()

        methods = {}
        method_src = ''
        name = ''
        for line in data:
            if not line.strip():
                continue
            elif line.startswith('#'):
                name = line[2:].strip()
                continue
            elif line.strip() == '===':
                methods[name] = method_src
                method_src = 'name bad\n'
            else:
                method_src += line

        metafunc.parametrize('example', methods.items())
