#!/usr/bin/env python3


import sys, os

from examples.re.reParser import serialize_re

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
scriptpath = os.path.abspath(scriptpath)

from DHParser.configuration import set_config_value, read_local_config
from DHParser.nodetree import Node
from reParser import compile_src, chRanges, serialize_re
from runeranges import RRstr, sort_and_merge, range_intersection

# read_local_config(os.path.join(scriptpath, 'reConfig.ini'))

class TestChRanages:
    def test_ch_ranges(self):
        rr = [RRstr("2-5"), RRstr("B-E"), RRstr("H-K"), RRstr("b-e"), RRstr("h-p")]
        sort_and_merge(rr)
        assert serialize_re(Node('charset', chRanges(rr))) == "[2-5B-EH-Kb-eh-p]"

        rr = [RRstr("b-e"), RRstr("2-5"), RRstr("B-E"), RRstr("C-K"), RRstr("f-p")]
        sort_and_merge(rr)
        assert serialize_re(Node('charset', chRanges(rr))) == "[2-5B-Kb-p]"

        rrA = (RRstr("0-4"), RRstr("F-H"), RRstr("a-c"))
        rrB = (RRstr("2-7"), RRstr("B-G"), RRstr("b-b"))
        rrC = range_intersection(rrA, rrB)
        assert serialize_re(Node('charset', chRanges(rrC))) == "[2-4F-Gb]"


class TestNormalizer:
    def setup_class(self):
        set_config_value('re.KeepFixedCharSets', True, allow_new_key=True)

    def test_normalizer(self):
        result, errors = compile_src('\ufeff(?a)[^a\d\S]', 'normalized')
        assert not errors
        assert serialize_re(result) == r'[[^a]&&\D&&\s]', serialize_re(result)

        result, errors = compile_src('\ufeff(?a)[a\d\S]', 'normalized')
        assert not errors
        assert serialize_re(result) == r'[a]|\d|\S', serialize_re(result)



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())