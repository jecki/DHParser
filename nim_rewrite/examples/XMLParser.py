import os
import sys

scriptdir = os.path.dirname(os.path.abspath(__file__))
dhparserdir = os.path.abspath(os.path.join(scriptdir, os.pardir, os.pardir))
if dhparserdir not in sys.path:
    sys.path.append(dhparserdir)

from DHParser.parsers import parse_HTML

if __name__ == "__main__":
    import K
    print(len(K.KSource))
    dom = parse_HTML(K.KSource)
    print('---')
    # print(dom.as_sxpr())
    print('---')
    for e in dom.errors:  print(e)


