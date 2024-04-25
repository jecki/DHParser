#!/usr/bin/env python3

"""test_parsers.py - tests of DHParser's stock-parsers


Author: Eckhart Arnold <arnold@badw.de>

Copyright 2024 Bavarian Academy of Sciences and Humanities

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

from DHParser.parsers import parse_HTML

class TestHTMLParser:
    def test_CharRef(self):
        tree = parse_HTML("<p><span>68</span><i>&#68;</i><b>&#68;</b><span>Δ</span></p>")
        assert tree.as_xml(inline_tags={'p'}) == \
               "<p><span>68</span><i>&#x68;</i><b>&#x68;</b><span>Δ</span></p>"
        assert tree.as_sxpr() == \
               '(p (span "68") (i (:CharRef "68")) (b (:CharRef "68")) (span "Δ"))'

    def test_EntityRef(self):
        tree = parse_HTML("<p><span>68</span><i>&nbsp;</i><b>&#68;</b><span>Δ</span></p>")
        assert tree.as_xml(inline_tags={'p'}) == "<p><span>68</span><i>&nbsp;</i><b>&#x68;</b><span>Δ</span></p>"
        assert tree.as_sxpr() == '(p (span "68") (i (:EntityRef "nbsp")) (b (:CharRef "68")) (span "Δ"))'


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())