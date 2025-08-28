#!/usr/bin/env python3


import sys, os

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
scriptpath = os.path.abspath(scriptpath)

from reParser import reStripComments

class TestPreprocessor:
    def test_preprocessor(self):
        regex = """(?x)
            <(a)
            (
                [^>]*
                href=   # href is required
                ['"]?   # HTML5 attribute values do not have to be quoted
                [^#'"]  # We don't want to match href values that start with # (like footnotes)
            )
            """
        compact_regex = reStripComments(regex, "<memory>").preprocessed_text
        assert compact_regex == '''(?x)<(a)([^>]*href=['"]?[^#'"])'''


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())