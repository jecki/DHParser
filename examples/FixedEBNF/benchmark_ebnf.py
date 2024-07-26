from FixedEBNFParser import parsing


def benchmark_parser_file(path, repetitions=1):
    import timeit
    parser = parsing.factory()
    assert path[-5:] == '.ebnf'
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    root = None
    def call_parser():
        nonlocal root
        root = parser(data)
    time = timeit.timeit(call_parser, number=repetitions)
    print(f'Parsing of "{path}" fnished in {time} seconds')
    if root.errors:
        for e in root.errors:
            print(e)
    return time


if __name__ == '__main__':
    time = benchmark_parser_file('FixedEBNF.ebnf', 1000)
    print(f'Time: {time} seconds')
    print("ready.")
