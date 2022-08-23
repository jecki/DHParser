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

from DHParser.json_validation import type_check, validate_type, validate_uniform_sequence
from DHParser.lsp import RequestMessage, Message, ResponseMessage, Position, \
    shortlist, DocumentSymbol


@type_check
def type_checked_func(select_test: int, request: RequestMessage, position: Position) \
        -> ResponseMessage:
    validate_type(position, Position)
    if select_test == 1:
        return {'jsonrpc': 'jsonrpc-string',
                'id': request['id'],
                'error': {'code': -404, 'message': 'bad mistake'}}
    elif select_test == 2:
        # missing required field 'message' in the contained
        # error object should case an error
        return {'jsonrpc': 'jsonrpc-string',
                'id': request['id'],
                'error': {'code': -404}}
    elif select_test == 3:
        return {'jsonrpc': 'Response',
                'id': request['id'],
                'result': "All's well that ends well"}
    else:
        # Just a different way of creating the dictionary
        return ResponseMessage(jsonrpc='Response', id=request['id'],
                               result="All's well that ends well")


class TestLSP:
    def test_shortlist1(self):
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

    def test_shortlist2(self):
        l = [entry.strip().upper() for entry in
            '''* GISLEM. Droct.; 20 ((MGMer. III; p. 543,14))
               * GLOSS. med.; p. 96,19
               * GLOSS. med. cod. Mon.; p. 24,43
               * GLOSS. med. cod. Petropol.; p. 273,19
               * GLOSS. med. cod. Trev.; p.
               * GLOSS. psalt. Lunaelac.; 150,6
               * GLOSS. Roger. I A; 4,14 p. 724,20
               * GLOSS. Roger. I B; 4,17 p. 724,15
               * GLOSS. Roger. II; 643
               * GLOSS. Roger. III; 854
               * GLOSS. Salern.; p. 21,28
               * GLOSS. Sangall.; 111 ((ed. B. Bischoff, Anecdota. 1984.; p. 48))
               * GLOSS.; 16 ((Festschrift H. Kolb. 1989.; p. 28))
            '''.split('\n')]
        l.sort()
        a, b = shortlist(l, '* GLOSS. med.'.upper())
        assert l[a:b] == [
            '* GLOSS. MED. COD. MON.; P. 24,43',
            '* GLOSS. MED. COD. PETROPOL.; P. 273,19',
            '* GLOSS. MED. COD. TREV.; P.',
            '* GLOSS. MED.; P. 96,19']
        a, b = shortlist(l, '* GLOSS. med. cod.'.upper())
        assert l[a:b] == [
            '* GLOSS. MED. COD. MON.; P. 24,43',
            '* GLOSS. MED. COD. PETROPOL.; P. 273,19',
            '* GLOSS. MED. COD. TREV.; P.']
        a, b = shortlist(l, '* GLOSS. med. cod. P'.upper())
        assert l[a:b] == ['* GLOSS. MED. COD. PETROPOL.; P. 273,19']

    def test_type_validation(self):
        position = Position(line=1, character=2)
        validate_type(position, Position)
        try:
            validate_type(position, Message)
            assert False, "TypeError expected!"
        except TypeError:
            pass

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


class TestDataValidation:
    documentSymbols = [{
            "name": "LEMMA",
            "detail": "*satinus",
            "kind": 5,
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 15}},
            "selectionRange": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 15}},
            "children": [{
                "name": "GRAMMATIK",
                "detail": "",
                "kind": 8,
                "range": {
                    "start": {"line": 2, "character": 0},
                    "end": {"line": 2, "character": 9}},
                "selectionRange": {
                    "start": {"line": 2, "character": 0},
                    "end": {"line": 2, "character": 9}},
                "children": []}, {
                "name": "BEDEUTUNG",
                "detail": "pars tricesima secunda ponderis -- der zweiunddreißigste Teil eines Gewichtes, 'Satin'; de nummo ((* {de re cf.} B. Hilliger, Studien zu mittelalterlichen Maßen und Gewichten. HistVjSchr. 3. 1900.; p. 191sq.)):",
                "kind": 5,
                "range": {
                    "start": {"line": 12, "character": 0},
                    "end": {"line": 12, "character": 220}},
                "selectionRange": {
                    "start": {"line": 12, "character": 0},
                    "end": {"line": 12, "character": 220}},
                "children": []}]}]

    def test_documentSymbols(self):
        validate_uniform_sequence(self.documentSymbols, DocumentSymbol)
        pass

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
