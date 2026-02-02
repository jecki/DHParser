#!/usr/bin/env python3

"""converEBNF.py -- converts between different EBNF syntax-styles."""


import sys, os

from tests.link_checker import dhparserdir

scriptdir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

try:
    import DHParser
except ImportError:
    search_path = scriptdir
    last_search_path = ''
    while (last_search_path != search_path
           and not os.path.isdir(os.path.join(search_path, 'DHParser'))):
        search_path = os.path.abspath(os.path.join(search_path, os.pardir))
    dhparserdir = os.path.join(search_path, 'DHParser')
    sys.path.append(dhparserdir)

from DHParser.ebnf import ebnf_to_ast, ebnf_from_ast


if __name__ == "__main__":
    ... # use argparse
