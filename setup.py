from distutils.core import setup

with open('README.md', encoding='utf-8') as f:
    read_me = f.read()

setup(
    name='DHParser',
    version='0.6.0',
    packages=['DHParser'],
    url='https://gitlab.lrz.de/badw-it/DHParser',
    license='APACHE 2.0 (http://www.apache.org/licenses/LICENSE-2.0)',
    author='Eckhart Arnold',
    author_email='arnold@badw.de',
    description='DHParser - Domain specific language support for the Digital Humanities',
    long_description = read_me,
    keywords='Digital Humanities, domain specific languages, parser combinators, EBNF',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Text Processing :: Markup',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers'
    ]
)
