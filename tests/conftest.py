import os


def pytest_generate_tests(metafunc):
    if 'method' in metafunc.fixturenames:
        method_names = os.listdir('examples/')
        metafunc.parametrize('method', method_names)
    if 'example' in metafunc.fixturenames:
        with open('tests/bad_cases') as f:
            data = f.readlines()

        methods = {}
        method = ''
        name = ''
        for line in data:
            if not line.strip():
                continue
            elif line.startswith('#'):
                name = line[2:]
                continue
            elif line.strip() == '===':
                methods[name] = method
                method = ''
            else:
                method += line

        metafunc.parametrize('example', methods.items())
