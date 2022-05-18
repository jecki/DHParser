#!/usr/bin/env python3

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

import fnmatch
import os
import sys


scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('..', '..'), '.'):
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)

import DHParser.configuration
import DHParser.dsl
from DHParser.error import ERROR
import DHParser.log
from DHParser.log import log_parsing_history


LOGGING = 'LOGS'

grammar_path = os.path.join(fullpath, 'LaTeX.ebnf')
if not DHParser.dsl.recompile_grammar(grammar_path, force=False):
    # recompiles Grammar only if it has changed
    print('\nErrors while recompiling "LaTeX.ebnf":\n--------------------------------------\n\n')
    with open('LaTeX_ebnf_ERRORS.txt', encoding="utf-8") as f:
        print(f.read())
    sys.exit(1)


from LaTeXParser import get_preprocessor, get_grammar, get_transformer, get_compiler

preprocessor = get_preprocessor()
parser = get_grammar()
transformer = get_transformer()
compiler = get_compiler()


def fail_on_error(src, result):
    if result.error_flag:
        for e in result.errors_sorted:
            print(str(e))
        if result.error_flag >= ERROR:
            sys.exit(1)


def tree_size(tree) -> int:
    """
    Recursively counts the number of nodes in the tree including the root node.
    """
    return sum(tree_size(child) for child in tree.children) + 1


def tst_func():
    DHParser.log.start_logging(LOGGING)
    test_dir = os.path.join(fullpath, 'testdata')
    files = os.listdir(test_dir)
    files.sort()
    for file in files:
        if fnmatch.fnmatch(file, '*.tex') and file.lower().find('error') < 0:
            filepath = os.path.join(test_dir, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                doc = f.read()

            print(f'\n\nPreprocessing document: "{file}"')
            preprocessed, _, source_mapper, _ = preprocessor(doc, file)
            print(f'\n\nParsing document: "{file}"')
            result = parser(preprocessed)
            print("Number of CST-nodes: " + str(tree_size(result)))
            # print("Number of empty nodes: " + str(count_nodes(result,
            #                                                 lambda n: not bool(n.result))))
            if DHParser.log.is_logging():
                print('Saving CST')
                logs = DHParser.log.log_dir().rstrip('/') + '/'
                with open(logs + file[:-4] + '.cst', 'w', encoding='utf-8') as f:
                    f.write(result.as_sxpr(compact=False))
                print('Saving parsing history')
                log_parsing_history(parser, os.path.basename(file), as_html=True)

            print('\nTransforming document: "%s"' % file)
            fail_on_error(doc, result)
            transformer(result)
            fail_on_error(doc, result)
            print("Number of AST-nodes: " + str(tree_size(result)))
            if DHParser.log.is_logging():
                logs = DHParser.log.log_dir().rstrip('/') + '/'
                print('Saving AST')
                with open(logs + file[:-4] + '.ast', 'w', encoding='utf-8') as f:
                    f.write(result.as_sxpr(compact=True))
                with open(logs + file[:-4] + '.tex', 'w', encoding='utf-8') as f:
                    f.write(str(result))

            print('\nCompiling document: "%s"' % file)
            output = compiler(result)
            with open(os.path.splitext(filepath)[0] + '.xml', 'w', encoding='utf-8') as f:
                f.write(output.as_xml())
            with open(os.path.splitext(filepath)[0] + '.sxpr', 'w', encoding='utf-8') as f:
                f.write(output.serialize('S-expression'))

def cpu_profile(func):
    import cProfile as profile
    import pstats
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
    from DHParser import nodetree
#    for k, v in nodetree.CALLERS.items():
#        print(k, v)

