#!/usr/bin/python3

"""test_markdown.py - unit tests for the markdown showcase


Copyright 2016  by Eckhart Arnold

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
import re
import sys


scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('..', '..'), '.'):  # '../showcases' ?
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)


class test_regexps:
    def setup(self):
        self.rx = dict()
        with open("../grammars/Markdown.enbf") as f:
            for stmt in f:
                m = re.match(r'\s*@?\s*(?P<symbol>\w+)\s*=\s*~?/(?P<regex>.*(?<![^\\]/))/', stmt)
                if m:
                    gd = m.groupdict()
                    if 'symbol' in gd and 'regex' in gd:
                        self.rx[gd['symbol']] = gd['regex']


    def test_whitespace(self):
        assert 'WSPC' in self.rx, str(self.rx)
        rx = re.compile(self.rx['WSPC'])
        assert rx.match('    ').group(0) == '    '
        assert rx.match('  \t ').group(0) == '  \t '
        assert rx.match('\n') is None
        assert rx.match(' \n') == ' '
        assert rx.match('  \n') is None
        assert rx.match('   \n') == ' '
        assert rx.match('\t\n') is None

    def test_ST(self):
        assert 'ST' in self.rx, str(self.rx)
        rx = re.compile(self.rx['ST'])
        assert rx.match('**').group(0) == '**'
        assert rx.match('__').group(0) == '__'
        assert rx.match('* ').group(0) is None
        assert rx.match('_').group(0) is None
        assert rx.match('__ ').group(0) == '__'
        assert rx.match('***') is None
        assert rx.match('____') is None


    def test_EM(self):
        assert 'EM' in self.rx, str(self.rx)
        rx = re.compile(self.rx['EM'])
        assert rx.match('**').group(0) is None
        assert rx.match('__').group(0) is None
        assert rx.match('* ').group(0) == '*'
        assert rx.match('_').group(0) == '_'
        assert rx.match('__ ') is None

    def test_BT(self):
        assert 'EM' in self.rx, str(self.rx)
        rx = re.compile(self.rx['BT'])
        assert rx.match('`').group(0) == '`'
        assert rx.match("'").group(0) == "'"

    def test_chunk(self):
        assert 'chunk' in self.rx, str(self.rx)
        rx = re.compile(self.rx['chunk'])
        assert rx.match('lore').group(0) == 'lore'
        assert rx.match('ip*sum*').group(0) == 'ip'
        assert rx.match(' ipsum') is None

# PARAGRAPH_TEST = """
#   This is a paragraph.
# Here, the paragraph is being continued.
#
# This is a new paragraph.
# """
#
# CODE_TEST = """
# Code-Test
#
#     def f():
#
#         pass
# """
#
# FENCED_TEST = """
# Fenced Code Test
# ~~~ Info String
# def f():
#
#   pass
# ~~~
# More Text
# """
#
# LIST_TEST = """
# This is a paragraph with
# two lines of text
#
# This is a paragraph.
# * First List Item
#
#   A New Paragraph under the same item
# * A second Item
#  A lazy line
#
#   Another paragraph under the second item
#
#  End of the list and a New paragraph
#
#   1.  A Numbered List
#
#       With several paragraphs
#
#           def f():
#               pass
#
#       Item continued
#
#   2.  Point Number 2
#
#   3.  And three
#
# >   4.  this is just a quote
# >
# > Example for a lazy line in a quote
# lazyline...
#
# New Paragraph.
# """
#
#
# def mark_special(text):
#     return text.replace('\x1b', '<').replace('\x1c', '>')
#
#
# print(mark_special(markdown_scanner(FENCED_TEST)))
#
# sys.exit(0)
