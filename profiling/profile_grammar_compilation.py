#!/usr/bin/env python

import sys, os

try:
    from DHParser import dsl
except ImportError:
    scriptpath = os.path.dirname(__file__) or '.'
    sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
    from DHParser import dsl


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


def recompile_MLW_grammar():
    dsl.recompile_grammar('data/MLW.ebnf', force=True,
                          notify=lambda: print('recompiling MLW.ebnf'))
    if os.path.exists('data/MLWParser.py'):
        os.remove('data/MLWParser.py')
    if os.path.exists('data/MLW_ebnf_ERRORS.txt'):
        os.remove('data/MLW_ebnf_ERRORS.txt')


if __name__ == '__main__':
    cpu_profile(recompile_MLW_grammar)
