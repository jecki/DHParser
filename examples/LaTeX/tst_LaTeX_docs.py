#!/usr/bin/python3

"""tst_LaTeX_doc.py - tests with full documents in subdir 'testdata'

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

import cProfile as profile
import os
import pstats
import sys

sys.path.extend(['../../', '../', './'])

import DHParser.dsl
from DHParser import toolkit

if not DHParser.dsl.recompile_grammar('LaTeX.ebnf', force=False):  # recompiles Grammar only if it has changed
    print('\nErrors while recompiling "LaTeX.ebnf":\n--------------------------------------\n\n')
    with open('LaTeX_ebnf_ERRORS.txt') as f:
        print(f.read())
    sys.exit(1)


from LaTeXCompiler import get_grammar, get_transformer

parser = get_grammar()
transformer = get_transformer()

def fail_on_error(src, result):
    if result.error_flag:
        print(result.as_sxpr())
        for e in result.collect_errors():
            print(str(e))
        sys.exit(1)


def tst_func():
    with toolkit.logging(False):
        files = os.listdir('testdata')
        files.sort()
        for file in files:
            if file.lower().endswith('.tex') and file.lower().find('error') < 0:
                with open(os.path.join('testdata', file), 'r', encoding="utf-8") as f:
                    doc = f.read()
                print('\n\nParsing document: "%s"\n' % file)
                result = parser(doc)
                parser.log_parsing_history__()
                fail_on_error(doc, result)
                transformer(result)
                fail_on_error(doc, result)
                # print(result.as_sxpr())


def cpu_profile(func):
    pr = profile.Profile()
    pr.enable()
    func()
    pr.disable()
    st = pstats.Stats(pr)
    st.strip_dirs()
    st.sort_stats('time').print_stats(40)


def mem_profile(func):
    import tracemalloc
    tracemalloc.start()
    func()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    print("[ Top 20 ]")
    for stat in top_stats[:40]:
        print(stat)

if __name__ == "__main__":
    cpu_profile(tst_func)




