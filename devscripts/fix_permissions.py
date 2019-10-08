#!/usr/bin/python

import os


def fix_permissions(path):
    entries = os.listdir(path)
    for entry in entries:
        entry_path = os.path.join(path, entry)
        if os.path.isdir(entry_path):
            os.chmod(entry_path, 0o755)
            fix_permissions(entry_path)
        else:
            with open(entry_path, 'rb') as f:
                shebang = f.read(2)
            if entry.endswith('.bat') or (not entry.endswith('.pyi') and shebang == b'#!'):
                os.chmod(entry_path, 0o755)
            else:
                os.chmod(entry_path, 0o644)


if __name__ == "__main__":
    cwd = os.getcwd()
    while not os.getcwd().rstrip(r'\/').endswith('DHParser'):
        os.chdir('..')
    fix_permissions('.')
    os.chdir(cwd)
