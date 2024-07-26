#!/usr/bin/env python3

import sys
sys.path.append("../")

import outlineParser

BAD_NESTING_EXAMPLE = """# Main Heading
## Section 1
#### BADLY NESTED SubSubSection 1.1.1
## Section 2"""

class TestErrorReporting:
    def test_bad_nesting(self):
        html, errors = outlineParser.compile_src(BAD_NESTING_EXAMPLE)
        for e in errors: print(e)
        assert len(errors) == 1, '\n'.join(str(e) for e in errors)
        assert errors[0].code == 2010

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
