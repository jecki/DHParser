#!/usr/bin/env python3
# update_lsp.py - update the lsp-speciications in DHParser/lsp.py

import sys, os, re

scriptdir = os.path.dirname(os.path.abspath(__file__))
destfile = os.path.abspath(os.path.join(scriptdir, '..', 'lsp.py'))


LSP_SPEC_SOURCE = \
    "https://raw.githubusercontent.com/microsoft/language-server-protocol/" \
    "gh-pages/_specifications/specification-current.md"


def extract_ts_code(specs):
    lines = specs.split('\n')
    ts = []
    copy_flag = False
    for l in lines:
        if l.strip() == '```typescript':
            copy_flag = True
        elif l.strip() == '```':
            copy_flag = False
            ts.append('')
        else:
            if copy_flag:
                ts.append(l)
    return '\n'.join(ts)


def download_specs(url: str) -> str:
    import urllib.request
    max_indirections = 2
    while max_indirections > 0:
        if url.startswith('http:') or url.startswith('https:'):
            print('fetching: ' + url)
            with urllib.request.urlopen(url) as f:
                specs = f.read()
        else:
            with open(url, 'rb') as f:
                specs = f.read()
        if len(specs) < 255:
            url = url[: url.rfind('/') + 1] + specs.decode('utf-8').strip()
            max_indirections -= 1
        else:
            max_indirections = 0
    return specs.decode('utf-8')


def transpile_ts_to_python(specs):
    from ts2pythonParser import compile_src
    specs_py, errors = compile_src(specs)
    if errors:
        for err in errors:
            print(err)
        sys.exit(1)
    return specs_py


BEGIN_MARKER = "##### BEGIN OF LSP SPECS"
END_MARKER = "##### END OF LSP SPECS"

def update_lsp_module(specs, destfile):
    with open(destfile, 'r', encoding='utf-8') as f:
        lsp = f.read()

    # skip import block
    i = specs.find(BEGIN_MARKER) + len(BEGIN_MARKER)
    k = specs.find(END_MARKER)
    specs = specs[i:k]

    i = lsp.find(BEGIN_MARKER) + len(BEGIN_MARKER)
    k = lsp.find(END_MARKER)

    new_lsp = '\n'.join([lsp[:i], specs, lsp[k:]])

    os.rename(destfile, destfile + '.save')
    with open(destfile, 'w', encoding='utf-8') as f:
        f.write(new_lsp)
    os.remove(destfile + '.save')


def run_update():
    specs_md = download_specs(LSP_SPEC_SOURCE)
    specs_ts = extract_ts_code(specs_md)
    specs_py = transpile_ts_to_python(specs_ts)
    update_lsp_module(specs_py, destfile)

if __name__ == "__main__":
    run_update()
