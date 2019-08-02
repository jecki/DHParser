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
import fnmatch
import os
import pstats
import sys

sys.path.extend([os.path.join('..', '..'), '..', '.'])

import DHParser.dsl
import DHParser.log
from DHParser.log import log_parsing_history


LOGGING = ''

if not DHParser.dsl.recompile_grammar('LaTeX.ebnf', force=False):  # recompiles Grammar only if it has changed
    print('\nErrors while recompiling "LaTeX.ebnf":\n--------------------------------------\n\n')
    with open('LaTeX_ebnf_ERRORS.txt', encoding="utf-8") as f:
        print(f.read())
    sys.exit(1)


from LaTeXCompiler import get_grammar, get_transformer, get_compiler

parser = get_grammar()
transformer = get_transformer()
compiler = get_compiler()

def fail_on_error(src, result):
    if result.error_flag:
        print(result.as_sxpr())
        for e in result.errors_sorted:
            print(str(e))
        sys.exit(1)


def tree_size(tree) -> int:
    """
    Recursively counts the number of nodes in the tree including the root node.
    """
    return sum(tree_size(child) for child in tree.children) + 1


def tst_func():
    DHParser.log.start_logging(LOGGING)
    files = os.listdir('testdata')
    files.sort()
    for file in files:
        if fnmatch.fnmatch(file, '*.tex') and file.lower().find('error') < 0:
            with open(os.path.join('testdata', file), 'r', encoding='utf-8') as f:
                doc = f.read()

            print('\n\nParsing document: "%s"' % file)
            result = parser(doc)
            print("Number of CST-nodes: " + str(tree_size(result)))
            # print("Number of empty nodes: " + str(count_nodes(result,
            #                                                 lambda n: not bool(n.result))))
            if DHParser.log.is_logging():
                print('Saving CST')
                with open('LOGS/' + file[:-4] + '.cst', 'w', encoding='utf-8') as f:
                    f.write(result.as_sxpr(compact=True))
                print('Saving parsing history')
                log_parsing_history(parser, os.path.basename(file), html=True)

            print('\nTransforming document: "%s"' % file)
            fail_on_error(doc, result)
            transformer(result)
            fail_on_error(doc, result)
            print("Number of AST-nodes: " + str(tree_size(result)))
            if DHParser.log.is_logging():
                print('Saving AST')
                with open('LOGS/' + file[:-4] + '.ast', 'w', encoding='utf-8') as f:
                    f.write(result.as_sxpr(compact=True))
                with open('LOGS/' + file[:-4] + '.tex', 'w', encoding='utf-8') as f:
                    f.write(str(result))

            print('\nCompiling document: "%s"' % file)
            output = compiler(result)
            # print(output)


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


