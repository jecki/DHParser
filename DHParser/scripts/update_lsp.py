#!/usr/bin/env python3
# update_lsp.py - update the lsp-speciications in DHParser/lsp.py

import sys, os, re

scriptdir = os.path.dirname(os.path.abspath(__file__))
sourcedir = os.path.abspath(os.path.join(
    scriptdir, '..', '..', 'examples', 'ts2dataclass', 'testdata'))
destfile = os.path.abspath(os.path.join(scriptdir, '..', 'lsp.py'))

BEGIN_MARKER = "##### BEGIN OF LSP SPECS"
END_MARKER = "##### END OF LSP SPECS"

def update(sourcedir, destfile):
    files = [os.path.join(sourcedir, name) for name in os.listdir(sourcedir)
             if name.endswith('.py') and name.startswith('lsp-specification')]
    if not files:
        print(f'No Python-version of the lsp-specification found in "{sourcedir}"!')
        sys.exit(1)
    files.sort()
    srcfile = files[-1]
    with open(srcfile, 'r', encoding='utf-8') as f:
        specs = f.read()
    with open(destfile, 'r', encoding='utf-8') as f:
        lsp = f.read()

    # skip import block
    i = 0
    for m in re.finditer(r'\n *(?!from|import)\w', specs):
        i = m.start()
        break
    specs = specs[i:]

    i = lsp.find(BEGIN_MARKER) + len(BEGIN_MARKER)
    k = lsp.find(END_MARKER)

    new_lsp = '\n'.join([lsp[:i], specs, lsp[k:]])

    os.rename(destfile, destfile + '.save')
    with open(destfile, 'w', encoding='utf-8') as f:
        f.write(new_lsp)
    os.remove(destfile + '.save')


if __name__ == "__main__":
    update(sourcedir, destfile)
