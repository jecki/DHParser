# build.py - support for building cython extensions with poetry

from setuptools import setup

try:
    from Cython.Build import cythonize
except ImportError:
    def cythonize(filename, **options):
        return []


cythonize_modules = [
    'DHParser/stringview.py',
    'DHParser/toolkit.py',
    'DHParser/preprocess.py',
    'DHParser/error.py',
    'DHParser/syntaxtree.py',
    'DHParser/log.py',
    'DHParser/parse.py',
    'DHParser/trace.py',
    'DHParser/transform.py',
    'DHParser/compile.py',
    'DHParser/ebnf.py',
]


def build(setup_kwargs):
    setup(
        name='Hello world app',
        ext_modules=cythonize(cythonize_modules, nthreads=0, annotate=False),
        zip_safe=False,
    )
