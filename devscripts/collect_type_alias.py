#!/usr/bin/env python

"""find_type_alias.py - Find all TypeAlias types for sphinx

Copyright 2022  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import sys, os, re

def find_type_alias(path: str) -> dict:
    alias_dict = {}
    for fname in os.listdir(path):
        if fname.endswith('.py'):
            fpath = os.path.join(path, fname)
            with open(fpath, 'r', encoding='utf-8') as f:  pysrc = f.read()
            for m in re.finditer(r'\n(\w+): TypeAlias', pysrc):
                s = m.group(1)
                alias_dict[s] = s
    return alias_dict

if __name__ == '__main__':
    tas = find_type_alias(sys.argv[1] if len(sys.argv) > 1 else "DHParser")
    l = list(tas.keys())
    l.sort()
    print('{')
    for key in l:
        print(f'  "{key}": "{tas[key]}",')
    print('}')

