#!/usr/bin/python3

import cProfile as profile
import fnmatch
import os
import pstats
import sys

sys.path.extend(['../../', '../', './'])

from DHParser.toolkit import logging
from DHParser.parsers import compile_source
from DHParser.dsl import recompile_grammar

if not recompile_grammar('MLW.ebnf', force=False):  # recompiles Grammar only if it has changed
    with open('MLW_ebnf_ERRORS.txt') as f:
        print(f.read())
    sys.exit(1)


from MLWCompiler import get_preprocessor, get_grammar, get_transformer, get_compiler

def tst_func():
    for root, dirs, files in os.walk('Beispiele'):
        for fname in files:
            entry = os.path.join(root, fname)
            if fnmatch.fnmatch(entry, '*.mlw'):
                print('\n Parse: ' + entry)
                raw_name = os.path.splitext(entry)[0]
                with logging(True):
                    result, messages, AST = compile_source(entry,
                                                           get_preprocessor(),
                                                           get_grammar(),
                                                           get_transformer(),
                                                           get_compiler())
                if AST:
                    with open(raw_name + '.ast', 'w', encoding='utf-8') as f:
                        f.write(AST.as_sxpr(compact=False))
                if messages:
                    print("Errors in: " + entry)
                    with open(raw_name + '.messages', 'w', encoding='utf-8') as f:
                        for m in messages:
                            s = str(m)
                            print(s)
                            f.write(s)
                            f.write('\n')
                else:
                    print("\nParsing of %s successfull :-)\n" % entry)

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
    # cpu_profile(tst_func)
    tst_func()