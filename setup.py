#from distutils.core import setup
from setuptools import setup, find_packages
try:
    from Cython.Build import cythonize
except ImportError:
    def cythonize(filename, **options):
        return []
from DHParser.versionnumber import __version__


with open('README.md', encoding='utf-8') as f:
    read_me = f.read()

setup(
    name='DHParser',
    version=__version__,
    packages=['DHParser', 'DHParser.scripts'],
    ext_modules=cythonize(['DHParser/stringview.py',
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
                           ],
                          nthreads=0, annotate=False),
    url='https://gitlab.lrz.de/badw-it/DHParser',
    license='[Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)',
    author='Eckhart Arnold',
    author_email='arnold@badw.de',
    description='DHParser - Parser generator and DSL-construction-kit',
    long_description = read_me,
    long_description_content_type="text/markdown",
    keywords='parser generator, domain specific languages, Digital Humanities, parser combinators, EBNF',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Text Processing :: Markup',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers'
    ],
    scripts=['DHParser/scripts/dhparser.py',
             'DHParser/scripts/dhparser_rename.py'],
    entry_points={
        'console_scripts': [
            'dhparser=DHParser.scripts.dhparser:main'
        ]
    }
)
