#!/usr/bin/env python3

"""test_server_utils.py - tests for utility-functions in the,
    server-module of DHParse.


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


import concurrent.futures
import collections.abc
import json
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.server import pp_json


class TestUtils:
    data = ('{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"processId":17666,'
            '"rootPath":"/home/eckhart/Entwicklung/DHParser/examples/EBNF_fork","rootUri":'
            '"file:///home/eckhart/Entwicklung/DHParser/examples/EBNF_fork","capabilities":'
            '{"workspace":{"applyEdit":true,"workspaceEdit":{"documentChanges":true},'
            '"didChangeConfiguration":{"dynamicRegistration":true},"didChangeWatchedFiles":'
            '{"dynamicRegistration":true},"symbol":{"dynamicRegistration":true,"symbolKind":'
            '{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,'
            '26]}},"executeCommand":{"dynamicRegistration":true},"configuration":true,'
            '"workspaceFolders":true},"textDocument":{"publishDiagnostics":'
            '{"relatedInformation":true},"synchronization":{"dynamicRegistration":true,'
            '"willSave":true,"willSaveWaitUntil":true,"didSave":true},"completion":'
            '{"dynamicRegistration":true,"contextSupport":true,"completionItem":'
            '{"snippetSupport":true,"commitCharactersSupport":true,"documentationFormat":'
            '["markdown","plaintext"],"deprecatedSupport":true,"preselectSupport":true},'
            '"completionItemKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,'
            '19,20,21,22,23,24,25]}},"hover":{"dynamicRegistration":true,"contentFormat":'
            '["markdown","plaintext"]},"signatureHelp":{"dynamicRegistration":true,'
            '"signatureInformation":{"documentationFormat":["markdown","plaintext"]}},'
            '"definition":{"dynamicRegistration":true},"references":{"dynamicRegistration":'
            'true},"documentHighlight":{"dynamicRegistration":true},"documentSymbol":'
            '{"dynamicRegistration":true,"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,'
            '12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},'
            '"hierarchicalDocumentSymbolSupport":true},"codeAction":{"dynamicRegistration":'
            'true,"codeActionLiteralSupport":{"codeActionKind":{"valueSet":["","quickfix",'
            '"refactor","refactor.extract","refactor.inline","refactor.rewrite","source",'
            '"source.organizeImports"]}}},"codeLens":{"dynamicRegistration":true},'
            '"formatting":{"dynamicRegistration":true},"rangeFormatting":'
            '{"dynamicRegistration":true},"onTypeFormatting":{"dynamicRegistration":true},'
            '"rename":{"dynamicRegistration":true},"documentLink":{"dynamicRegistration":'
            'true},"typeDefinition":{"dynamicRegistration":true},"implementation":'
            '{"dynamicRegistration":true},"colorProvider":{"dynamicRegistration":true},'
            '"foldingRange":{"dynamicRegistration":true,"rangeLimit":5000,"lineFoldingOnly":'
            'true}}},"trace":"off","workspaceFolders":[{"uri":'
            '"file:///home/eckhart/Entwicklung/DHParser/examples/EBNF_fork",'
            '"name":"EBNF_fork"}]}}')

    expected = """{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "processId": 17666,
    "rootPath": "/home/eckhart/Entwicklung/DHParser/examples/EBNF_fork",
    "rootUri": "file:///home/eckhart/Entwicklung/DHParser/examples/EBNF_fork",
    "capabilities": {
      "workspace": {
        "applyEdit": true,
        "workspaceEdit": {"documentChanges": true},
        "didChangeConfiguration": {"dynamicRegistration": true},
        "didChangeWatchedFiles": {"dynamicRegistration": true},
        "symbol": {
          "dynamicRegistration": true,
          "symbolKind": {
            "valueSet": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]}},
        "executeCommand": {"dynamicRegistration": true},
        "configuration": true,
        "workspaceFolders": true},
      "textDocument": {
        "publishDiagnostics": {"relatedInformation": true},
        "synchronization": {
          "dynamicRegistration": true,
          "willSave": true,
          "willSaveWaitUntil": true,
          "didSave": true},
        "completion": {
          "dynamicRegistration": true,
          "contextSupport": true,
          "completionItem": {
            "snippetSupport": true,
            "commitCharactersSupport": true,
            "documentationFormat": ["markdown","plaintext"],
            "deprecatedSupport": true,
            "preselectSupport": true},
          "completionItemKind": {
            "valueSet": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]}},
        "hover": {
          "dynamicRegistration": true,
          "contentFormat": ["markdown","plaintext"]},
        "signatureHelp": {
          "dynamicRegistration": true,
          "signatureInformation": {
            "documentationFormat": ["markdown","plaintext"]}},
        "definition": {"dynamicRegistration": true},
        "references": {"dynamicRegistration": true},
        "documentHighlight": {"dynamicRegistration": true},
        "documentSymbol": {
          "dynamicRegistration": true,
          "symbolKind": {
            "valueSet": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},
          "hierarchicalDocumentSymbolSupport": true},
        "codeAction": {
          "dynamicRegistration": true,
          "codeActionLiteralSupport": {
            "codeActionKind": {
              "valueSet": ["","quickfix","refactor","refactor.extract","refactor.inline","refactor.rewrite","source","source.organizeImports"]}}},
        "codeLens": {"dynamicRegistration": true},
        "formatting": {"dynamicRegistration": true},
        "rangeFormatting": {"dynamicRegistration": true},
        "onTypeFormatting": {"dynamicRegistration": true},
        "rename": {"dynamicRegistration": true},
        "documentLink": {"dynamicRegistration": true},
        "typeDefinition": {"dynamicRegistration": true},
        "implementation": {"dynamicRegistration": true},
        "colorProvider": {"dynamicRegistration": true},
        "foldingRange": {
          "dynamicRegistration": true,
          "rangeLimit": 5000,
          "lineFoldingOnly": true}}},
    "trace": "off",
    "workspaceFolders": [{
        "uri": "file:///home/eckhart/Entwicklung/DHParser/examples/EBNF_fork",
        "name": "EBNF_fork"}]}}"""

    def test_pp_json(self):
        obj = json.loads(self.data)
        serialized = pp_json(obj)
        # print()
        # print(pp_json(obj))
        assert serialized == self.expected


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
