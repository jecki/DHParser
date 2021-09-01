#!/usr/bin/env python3

"""test_lsp.py - tests of the language server protocol module
                 of DHParser

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2020 Bavarian Academy of Sciences and Humanities

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

try:
    from typing import TypedDict
except ImportError:
    from DHParser.externallibs.typing_extensions import TypedDict

from DHParser.lsp import RequestMessage, Message, ResponseMessage, Position, type_check, shortlist


@type_check
def type_checked_func(select_test: int, request: RequestMessage, position: Position) \
        -> ResponseMessage:
    if select_test == 1:
        return {'jsonrpc': 'jsonrpc-string',
                'id': request['id'],
                'error': {'code': -404, 'message': 'bad mistake'}}
    elif select_test == 2:
        return {'jsonrpc': 'jsonrpc-string',
                'id': request['id'],
                'error': {'code': -404}}
    elif select_test == 3:
        return {'jsonrpc': 'Response',
                'id': request['id'],
                'result': "All's well that ends well"}
    else:
        return ResponseMessage(jsonrpc='Response', id=request['id'],
                               result="All's well that ends well")


class TestLSP:
    def test_shortlist(self):
        long = ['ABBO', 'ABCO', 'ACBO', 'ACDO', 'BAC', 'BB']
        assert shortlist(long, 'A') == (0, 4)
        assert shortlist(long, 'AB') == (0,2)
        assert shortlist(long, 'AC') == (2, 4)
        assert shortlist(long, 'B') == (4, 6)
        assert shortlist(long, 'BA') == (4, 5)
        assert shortlist(long, 'BAC') == (4, 5)
        assert shortlist(long, 'BB') == (5, 6)
        assert shortlist(long, 'BBC') == (6, 6)
        assert shortlist(long, 'ABBO') == (0, 1)
        assert shortlist(long, 'AA') == (0, 0)

    def test_type_check(self):
        response = type_checked_func(0, {'jsonrpc': '2.0', 'id': 21, 'method': 'check'},
                                     Position(line=21, character=15))
        assert response['id'] == 21
        response = type_checked_func(1, {'jsonrpc': '2.0', 'id': 21, 'method': 'check'},
                                     Position(line=21, character=15))
        assert response['id'] == 21
        response = type_checked_func(3, RequestMessage(jsonrpc='2.0', id=21, method='check'),
                                     {'line': 21, 'character': 15})
        assert response['id'] == 21
        if sys.version_info < (3, 7, 0):
            return
        try:
            _ = type_checked_func(0, {'jsonrpc': '2.0', 'id': 21, 'method': 'check'})
            assert False, "Missing parameter not noticed"
        except TypeError:
            pass
        try:
            _ = type_checked_func(0, {'jsonrpc': '2.0', 'method': 'check'},
                                     Position(line=21, character=15))
            assert False, "Type Error in parameter not detected"
        except KeyError:
            if sys.version_info >= (3, 8):
                assert False, "Type Error in parameter not detected"
        except TypeError:
            pass
        try:
            _ = type_checked_func(2, {'jsonrpc': '2.0', 'id': 21, 'method': 'check'},
                                     Position(line=21, character=15))
            if sys.version_info >= (3, 8):
                assert False, "Type Error in nested return type not detected"
        except TypeError:
            pass


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
