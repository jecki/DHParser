#!/usr/bin/env python3

"""test_syntaxtree.py - profiling of syntaxtree-module of DHParser

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2017 Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.syntaxtree import parse_xml
from DHParser.toolkit import json_dumps

def cpu_profile(func, repetitions=1):
    """Profile the function `func`.
    """
    import cProfile
    import pstats
    profile = cProfile.Profile()
    profile.enable()
    success = True
    for _ in range(repetitions):
        success = func()
        if not success:
            break
    profile.disable()
    # after your program ends
    stats = pstats.Stats(profile)
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(20)
    return success


def profile_serializing():
    with open(os.path.join(scriptpath, 'data', 'inferus.ausgabe.xml')) as f:
        data = f.read()
    tree = parse_xml(data)
    print('XML inferus')
    cpu_profile(tree.as_xml, 100)
    print('S-Expression inferus')
    cpu_profile(lambda :tree.as_sxpr(compact=True), 100)
    print('json inferus')
    cpu_profile(lambda :tree.as_json(indent=None), 100)
    print('toolkit.json_dumps inferus')
    cpu_profile(lambda :json_dumps(tree.to_json_obj()), 100)

    with open(os.path.join(scriptpath, 'data', 'testdoc3.xml')) as f:
        data = f.read()
    tree = parse_xml(data)
    print('XML testdoc3')
    cpu_profile(tree.as_xml, 100)
    print('S-Expression testdoc3')
    cpu_profile(lambda :tree.as_sxpr(compact=True), 100)
    print('json testdoc3')
    cpu_profile(lambda :tree.as_json(indent=None), 100)
    print('toolkit.json_dumps testdoc3')
    cpu_profile(lambda :json_dumps(tree.to_json_obj()), 100)


if __name__ == "__main__":
    profile_serializing()

