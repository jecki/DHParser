#!/usr/bin/env python3

"""test_server_utils.py - tests for utility-functions in the
    server-module of DHParser.


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


import asyncio
import concurrent.futures
import collections.abc
import json
import os
import sys
import traceback

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.server import pp_json, ExecutionEnvironment, asyncio_run, Server,\
    rpc_table_info
from DHParser.toolkit import json_encode_string


class TestExecutionEnvironment:
    def test_execenv(self):
        def fault():
            raise AssertionError

        async def main():
            loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            env = ExecutionEnvironment(loop)
            return await env.execute(None, fault, [])

        result, rpc_error = asyncio_run(main())
        json_str = '{"jsonrpc": "2.0", "error": {"code": %i, "message": %s}}' % \
                   (rpc_error[0], json_encode_string(rpc_error[1]))
        assert json_str.find('Traceback') >= 0


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
        assert sys.version_info < (3, 6) or serialized == self.expected, serialized

    def test_pp_json_stacktrace(self):
        try:
            raise AssertionError()
        except AssertionError:
            tb = traceback.format_exc()
        ppjsn = pp_json({'error' : tb}).replace('\\\\', '/')
        expected = '{"error": "Traceback (most recent call last):"\n' \
            '  "  File \\"$SCRIPTPATH/test_server_utils.py\\", ' \
            'line 179, in test_pp_json_stacktrace"\n' \
            '  "    raise AssertionError()"\n' \
            '  "AssertionError"\n  ""}'.\
            replace('$SCRIPTPATH', scriptpath.replace('\\', '/'), 1).replace('./', '')
        expected_py311 = '{"error": "Traceback (most recent call last):"\n' \
            '  "  File \\"$SCRIPTPATH/test_server_utils.py\\", ' \
            'line 179, in test_pp_json_stacktrace"\n' \
            '  "    raise AssertionError()"\n' \
            '  "    ^^^^^^^^^^^^^^^^^^^^^^"\n' \
            '  "AssertionError"\n  ""}'.\
            replace('$SCRIPTPATH', scriptpath.replace('\\', '/'), 1).replace('./', '')            
        # print(ppjsn)
        # print(expected)
        assert ppjsn == expected or ppjsn == expected_py311, '\n\n' + ppjsn + '\n\n' + expected


class TestRPCTable:
    def test_rpc_table_info(self):
        s = Server({'default': lambda *args, **kwargs: 'dummy'})
        info_str = rpc_table_info(s.rpc_table)
        assert info_str.find('identify(') >= 0
        assert info_str.find('logging(') >= 0
        info_html = rpc_table_info(s.rpc_table, html=True)
        assert info_html.find('<b>identify(') >= 0
        assert info_html.find('<b>logging(') >= 0


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
