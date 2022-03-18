#!/usr/bin/env python3
# build.py - support for building cython extensions with poetry


import os
import sys
from setuptools import setup


try:
    from Cython.Build import cythonize
    has_cython = True
except ImportError:
    has_cython = False
    def cythonize(filename, **options):
        return []


cythonize_modules = [
    'DHParser/stringview.py',
    # 'DHParser/toolkit.py',
    # 'DHParser/preprocess.py',
    # 'DHParser/error.py',
    # 'DHParser/nodetree.py',
    # 'DHParser/log.py',
    # 'DHParser/parse.py',
    # 'DHParser/trace.py',
    # 'DHParser/transform.py',
    # 'DHParser/compile.py',
    # 'DHParser/ebnf.py',
]


def build(setup_kwargs={}):
    if has_cython:

        # find path of DHParser-module
        scriptdir = os.path.dirname(os.path.abspath(__file__))
        i = scriptdir.find('DHParser')
        k = len('DHParser-submodule') if scriptdir[i:].startswith('DHParser-submodule') \
            else len('DHParser')
        if i >= 0:
            dhparserdir = scriptdir[:i + k]
            if dhparserdir not in sys.path:
                sys.path.append(dhparserdir)
        else:
            dhparserdir = ''

        print("assuming DHParser-directory: ", dhparserdir)

        save_cwd = os.getcwd()
        os.chdir(dhparserdir)

        # delete stale c and object-files
        for name in os.listdir(dhparserdir):
            if name.endswith('.c') or name.endswith('.pyd') or name.endswith('.so'):
                os.remove(name)

        # build cyhton modules inplace
        sys.argv.extend(['build_ext', '--inplace'])
        setup(
            name='DHParser',
            ext_modules=cythonize(cythonize_modules, nthreads=0, annotate=False),
            zip_safe=False,
        )

        os.chdir(save_cwd)

    else:
        print('DHParser.scripts.build_cython: Cannot build Cython modules, '
              'because Cython has not installed!\nTry running: pip install cython')


if __name__ == "__main__":
    build()
