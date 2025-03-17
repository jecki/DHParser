#!/usr/bin/env python3

"""test_stringview.py - tests of the stringview-module of DHParser

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
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.toolkit import re
from DHParser.stringview import StringView, TextBuffer, EMPTY_STRING_VIEW, real_indices


class TestStringView:
    def test_slow_real_indices(self):
        assert real_indices(3, 5, 10) == (3, 5)
        assert real_indices(None, None, 10) == (0, 10)
        assert real_indices(-2, -1, 10) == (8, 9)
        assert real_indices(-3, 11, 10) == (7, 10)
        assert real_indices(-5, -12, 10) == (5, 0)
        assert real_indices(-12, -5, 10) == (0, 5)
        assert real_indices(7, 6, 10) == (7, 6)
        assert real_indices(None, 0, 10) == (0, 0)

    def test_creation(self):
        s = "0123456789"
        assert str(StringView(s)) == s
        assert str(StringView(s, 3, 4)) == '3'
        assert str(StringView(s, -4)) == '6789'

    def test_equality(self):
        s = "0123456789"
        assert StringView(s) == s
        assert StringView(s, 3, 4) == '3'
        assert StringView(s, -4) == '6789'

    def test_slicing(self):
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert sv == '0123456789'
        assert sv[3:4] == '3'
        assert sv[-3:-1] == '78'
        assert sv[4:3] == ''
        assert sv[:4] == '0123'
        assert sv[4:] == '456789'
        assert sv[-2:] == '89'
        assert sv[:-5] == '01234'
        assert isinstance(sv[3:5], StringView)

    def test_len(self):
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert len(sv) == 10
        # assert sv.len == 10
        assert len(sv[5:5]) == 0
        assert len(sv[7:4]) == 0
        assert len(sv[-12:-2]) == 8
        assert len(sv[-12:12]) == 10

    def test_bool(self):
        assert not StringView('')
        assert StringView('x')
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert not sv[5:4]
        assert sv[4:5], str(sv[4:5])
        assert not sv[3:3]
        assert not sv[12:13]
        assert sv[0:20]

    def test_sv_match(self):
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert sv.match(re.compile(r'\d'))
        assert sv.match(re.compile(r'\d+'))
        assert not sv.match(re.compile(r' '))
        assert sv[4:].match(re.compile(r'45'))

    def test_sv_special_match(self):
        """Difference of string- and StringView-slicing w.r.t regular expression matching."""
        s = " 0123456789 "
        RE_BEGIN = re.compile('^')
        RE_END = re.compile('$')
        assert re.match(RE_BEGIN, s)
        assert not re.match(RE_END, s)
        end = s[len(s):]
        assert re.match(RE_END, end)
        assert re.match(RE_BEGIN, end)              # string-sliced ending will be matched by /^/
        middle = s[5:]
        assert re.match(RE_BEGIN, middle)           # string-sliced middle will be matched by /^/
        assert not re.match(RE_END, middle)

        sv = StringView(s)
        RE_BEGIN = re.compile('^')
        RE_END = re.compile('$')
        assert sv.match(RE_BEGIN)
        assert not sv.match(RE_END)
        end = sv[len(sv):]
        assert end.match(RE_END)
        assert not end.match(RE_BEGIN)              # StringView-sliced ending will not be matched by /^/
        middle = sv[5:]
        assert not middle.match(RE_BEGIN)           # String-sliced middle will not be matched by /^/
        assert not middle.match(RE_END)

    def test_sv_search(self):
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert sv.search(re.compile(r'5'))
        assert not sv.search(re.compile(r' '))
        assert sv[5:].search(re.compile(r'5'))
        assert not sv[:9].search(re.compile(r'9'))

    def test_find(self):
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert sv.find('5') == 5
        assert sv.find(' ') == -1
        assert sv.find('0', 1) == -1
        assert sv.find('9', 0, 8) == -1
        assert sv.find('45', 1, 8) == 4

    def test_rfind(self):
        s = " 123321 "
        sv = StringView(s, 1, -1)
        assert sv.rfind('3') == 3
        assert sv.find('3') == 2
        assert sv.rfind('a') == -1

    def test_startswith(self):
        s = " 0123456789 "
        sv = StringView(s, 1, -1)
        assert sv.startswith('012')
        assert sv.startswith('123', 1)
        assert not sv.startswith('123', 1, 3)

    def test_EMPTY_STRING_VIEW(self):
        assert len(EMPTY_STRING_VIEW) == 0
        assert EMPTY_STRING_VIEW.find('x') < 0
        assert not EMPTY_STRING_VIEW.match(re.compile(r'x'))
        assert EMPTY_STRING_VIEW.match(re.compile(r'.*'))
        assert len(EMPTY_STRING_VIEW[0:1]) == 0

    def test_strip(self):
        s = StringView('  test  ', 1, -1)
        assert s.strip() == "test"
        assert s.lstrip() == "test "
        assert s.rstrip() == " test"
        s = StringView(' test ', 1, -1)
        assert s.strip() == "test"
        s = StringView('(a (b c))')
        assert s.strip() == '(a (b c))'
        assert s[1:].strip() == 'a (b c))'
        s = StringView('"22"')
        assert s.strip('"') == '22'

    def test_split(self):
        s = StringView(' 1,2,3,4,5 ', 1, -1)
        assert s.split(',') == ['1', '2', '3', '4', '5']

    def test_index_error(self):
        s = StringView('0123456789')
        try:
            s[25]
            assert False, "IndexError expected!"
        except IndexError:
            pass


class TestTextBuffer:
    test_text = "\n".join([
    "To be or not to be",
    "that is the question.",
    "Whether it is nobler in mind to suffer",
    "the slings and arrows of misfortune,",
    "or, by opposing them, end them."
    ])

    def test_buffer_update(self):
        t = TextBuffer(self.test_text)
        # single line
        t.update(1, 8, 1, 11, 'a')
        assert str(t).startswith('To be or not to be\nthat is a question.\nWhether ')
        # several lines
        t.update(1, 10, 2, 7, 'question;\nwhether')
        assert str(t).startswith("To be or not to be\nthat is a question;\nwhether ")


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
