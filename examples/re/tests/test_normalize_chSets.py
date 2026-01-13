#!/usr/bin/env python3


import sys, os

from examples.re.reParser import serialize_re

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
scriptpath = os.path.abspath(scriptpath)

from DHParser.configuration import set_config_value, read_local_config
from DHParser.nodetree import Node
from reParser import compile_src, mkR, sortAndMerge, sortAndMergeInPlace, \
    rangeUnion, rangeDifference, rangeIntersection, serialize_re

# read_local_config(os.path.join(scriptpath, 'reConfig.ini'))

class TestChRanages:
    def test_ch_ranges(self):
        rr = [mkR("2-5"), mkR("B-E"), mkR("H-K"), mkR("b-e"), mkR("h-p")]
        sortAndMergeInPlace(rr)
        assert serialize_re(Node('charset', tuple(rr))) == "[2-5B-EH-Kb-eh-p]"

        rr = [mkR("b-e"), mkR("2-5"), mkR("B-E"), mkR("C-K"), mkR("f-p")]
        sortAndMergeInPlace(rr)
        assert serialize_re(Node('charset', tuple(rr))) == "[2-5B-Kb-p]"

        rrA = (mkR("0-4"), mkR("F-H"), mkR("a-c"))
        rrB = (mkR("2-7"), mkR("B-G"), mkR("b-b"))
        rrC = rangeIntersection(rrA, rrB)
        print(serialize_re(Node('charset', tuple(rrC))))



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