"""gather_regexps.py - extracts regular expressions from python files"""

import os, re

RX_RXP = re.compile(r'(?:re\.compile\(|RegExp\(|= r)\s*(\'(?:\\.|[^\']|\'\s*\')*\'|"(?:\\.|[^"]|"\s*")*")\s*\)?')

def gather(directory: str) -> list[str]:
    regexps = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name[-3:] == '.py' and name[:5] != 'test_':
                with open(os.path.join(root, name), 'r', encoding='utf-8') as f:
                    py_src = f.read()
                    for m in RX_RXP.finditer(py_src):
                        rx = m.group(1)
                        rx = re.sub(r"'\n\s*'", '', rx)
                        rx = re.sub(r'"\n\s*"', '', rx)
                        regexps.append(rx)
                        print(name, rx)
    return regexps


if __name__ == '__main__':
    regexps = gather('..')
    # if __name__ == '__main__':
    #     for r in regexps:
    #         print(r)
