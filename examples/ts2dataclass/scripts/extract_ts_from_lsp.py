#!/usr/bin/env python3

"""extract_ts_from_lsp.py - extracts the typescript parts from the
specification of the language server protocol:
https://github.com/microsoft/language-server-protocol/tree/gh-pages/_specifications
"""

def extract(source, dest):
    with open(source, 'r', encoding='utf-8') as f:
        src = f.read()
    lines = src.split('\n')
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
    with open(dest, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ts))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        source = sys.argv[1]
    else:
        source = "lsp-specification_3.16.md"
    i = source.rfind('.')
    if i < 0:
        i = len(source)
    dest = source[:i] + '.ts'
    extract(source, dest)

