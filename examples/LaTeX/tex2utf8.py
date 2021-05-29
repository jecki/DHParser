#!/usr/bin/env python3

"""tex2utf8 - converst all .tex files in a directory to utf-8."""


import sys, os

def convert(root_path: str):
    for dirpath, dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith('.tex'):
                fpath = os.path.join(dirpath, fname)
                with open(fpath, 'rb') as f:
                    data = f.read()
                try:
                    _ = data.decode('utf-8', errors='strict')
                    print(fpath + ' was already unicode')
                except UnicodeDecodeError:
                    txt = data.decode('cp1252')
                    data = txt.encode('utf-8')
                    os.rename(fpath, fpath + '.cp1252')
                    with open(fpath, 'wb') as f:
                        f.write(data)
                    print(fpath + ' converted to unicode')


if __name__ == "__main__":
    root = './'
    if len(sys.argv) > 1:
        root = sys.argv[1]
        assert os.path.exists(root)
        assert os.path.isdir(root)

    convert(root)