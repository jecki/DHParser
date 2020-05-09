import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs=1)
    parser.add_argument('-s', '--switch', action='store_const', const='switch')
    args = parser.parse_args()
    print(args)
