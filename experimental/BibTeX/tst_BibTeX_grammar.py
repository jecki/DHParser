#!/usr/bin/env python3

"""tst_BibTeX_grammar.py - runs the unit tests for the BibTeX grammar

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

import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('../../examples', '..'), '.'):
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)

try:
    from DHParser import configuration
    import DHParser.dsl
    from DHParser import testing
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


if __name__ == "__main__":
    configuration.access_presets()
    configuration.set_preset_value('test_parallelization', True)
    configuration.finalize_presets()
    if not DHParser.dsl.recompile_grammar('BibTeX.ebnf', force=False):  # recompiles Grammar only if it has changed
        print('\nErrors while recompiling "BibTeX.ebnf":\n--------------------------------------\n\n')
        with open('BibTeX_ebnf_ERRORS.txt') as f:
            print(f.read())
        sys.exit(1)

    sys.path.append('')
    # must be appended after module creation, because otherwise an ImportError is raised under Windows

    from BibTeXParser import get_grammar, get_transformer

    error_report = testing.grammar_suite('test_grammar', get_grammar,
                                         get_transformer, report='REPORT', verbose=True)
    if error_report:
        print('\n')
        print(error_report)
        sys.exit(1)
    else:
        print('\nSUCCESS! All tests passed :-)')
