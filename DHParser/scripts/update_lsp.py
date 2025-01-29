#!/usr/bin/env python3
# update_lsp.py - update the lsp-speciications in DHParser/lsp.py

import sys, os, re

scriptdir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
destfile = os.path.abspath(os.path.join(scriptdir, '..', 'lsp.py'))


LSP_SPEC_SOURCE = \
    "https://raw.githubusercontent.com/microsoft/language-server-protocol/gh-pages/_specifications/lsp/3.18/specification.md"


def no_declaration(l):
    if l[0:1] in ("{", "["):
        return True
    if re.match(r'\w+(?:\.\w+)*\(', l):
        return True
    return False


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
                if no_declaration(l):
                    copy_flag = False
                elif l[0:2] != "//":
                    ts.append(l)
    return '\n'.join(ts)


def download_specfile(url: str) -> str:
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
        if len(specs) < 255 and specs.find(b'\n') < 0:
            url = url[: url.rfind('/') + 1] + specs.decode('utf-8').strip()
            max_indirections -= 1
        else:
            max_indirections = 0
    return specs.decode('utf-8')


RX_INCLUDE = re.compile(r'{%\s*include_relative\s*(?P<relative>[A-Za-z0-9/.]+?\.md)\s*%}|{%\s*include\s*(?P<absolute>[A-Za-z0-9/.]+?\.md)\s*%}')


def download_specs(url: str) -> str:
    specfile = download_specfile(url)
    relurl_path = url[:url.rfind('/') + 1]
    absurl_path = url[:url.find('_specifications/')] + '_includes/'
    parts = []
    e = 0
    for m in RX_INCLUDE.finditer(specfile):
        s = m.start()
        parts.append(specfile[e:s])
        if m.group('relative') is not None:
            incpath = m.group('relative')
            incl_url = relurl_path + incpath
        else:
            assert m.group('absolute') is not None
            incpath = m.group('absolute')
            incl_url = absurl_path + incpath
        parts.append(f'\n```typescript\n\n/* source file: "{incpath}" */\n```\n')
        include = download_specs(incl_url)
        parts.append(include)
        e = m.end()
    parts.append(specfile[e:])
    specs = ''.join(parts)
    return specs


def transpile_ts_to_python(specs):
    sys.path.append(os.path.join(scriptdir, '..'))
    from ts2python import ts2pythonParser
    specs_py, errors = ts2pythonParser.compile_src(specs)
    if errors:
        not_just_warnings = False
        for err in errors:
            print(err)
            not_just_warnings |= err.code >= 1000
        if not_just_warnings:
            sys.exit(1)
    sys.path.pop()
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
    print(destfile + " updated.")

if __name__ == "__main__":
    run_update()
