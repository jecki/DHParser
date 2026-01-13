#!/usr/bin/env python3


import sys, os

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
scriptpath = os.path.abspath(scriptpath)

from reParser import reStripComments, compile_src, INVALID_REGULAR_EXPRESSION

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

    def test_invalid_regular_expression(self):
        result, errors = compile_src('\ufeff[a-Z]', 'AST')
        assert result is None
        assert errors
        err = errors[0]
        assert err.code == INVALID_REGULAR_EXPRESSION
        assert err.pos == 1


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())