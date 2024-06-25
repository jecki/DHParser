from HTMLParser import benchmark_parser_file

if __name__ == '__main__':
    time = benchmark_parser_file('testdata/G.html')
    print(f'Time: {time} seconds')
    print("ready.")

