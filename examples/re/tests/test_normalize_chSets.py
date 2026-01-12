#!/usr/bin/env python3


import sys, os

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
scriptpath = os.path.abspath(scriptpath)

from DHParser.configuration import set_config_value, read_local_config
from reParser import compile_src

# read_local_config(os.path.join(scriptpath, 'reConfig.ini'))

class TestNormalizer:
    def setup_class(self):
        set_config_value('re.KeepFixedCharSets', True, allow_new_key=True)

    def test_normalizer(self):
        result, errors = compile_src('\ufeff(?a)[^a\d\S]', 'normalized')
        assert not errors
        print()
        print(result.as_sxpr())

        result, errors = compile_src('\ufeff(?a)[a\d\S]', 'normalized')
        assert not errors
        print()
        print(result.as_sxpr())

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())