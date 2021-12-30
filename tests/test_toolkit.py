#!/usr/bin/env python3

"""test_toolkit.py - tests of the toolkit-module of DHParser


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

import concurrent.futures
import collections.abc
import json
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.toolkit import has_fenced_code, load_if_file, re, normalize_docstring, \
    issubtype, typing, concurrent_ident, JSONstr, JSONnull, json_dumps, json_rpc, \
    matching_brackets, RX_ENTITY, validate_XML_attribute_value, fix_XML_attribute_value
from DHParser.log import log_dir, start_logging, is_logging, suspend_logging, resume_logging


class TestLoggingAndLoading:
    def setup(self):
        self.tmpname = 'tmp_' + concurrent_ident()
        self.filename = os.path.join("test", self.tmpname, "key_value_example.py") if os.path.isdir('test') \
            else os.path.join(self.tmpname, "key_value_example.py")
        self.dirname = os.path.dirname(self.filename)
        self.code1 = "x = 46\n"
        self.code2 = "def f():\n    return 46"
        if not os.path.exists(self.dirname):
            os.mkdir(self.dirname)
        with open(self.filename, 'w') as f:
            f.write(self.code2)
        self.LOGDIR = os.path.abspath(os.path.join(scriptpath, "TESTLOGS" + str(os.getpid())))

    def teardown(self):
        if os.path.exists(self.filename):  os.remove(self.filename)
        pycachedir = os.path.join(self.dirname,'__pycache__')
        if os.path.exists(pycachedir):
            for fname in os.listdir(pycachedir):
                os.remove(os.path.join(pycachedir, fname))
            os.rmdir(pycachedir)
        if os.path.exists(self.dirname):  os.rmdir(self.dirname)
        if os.path.exists(self.LOGDIR):
            # for fname in os.listdir(self.LOGDIR):
            #     os.remove(os.path.join(self.LOGDIR, fname))
            os.remove(os.path.join(self.LOGDIR, "info.txt"))
            os.rmdir(self.LOGDIR)

    def test_load_if_file(self):
        # an error should be raised if file expected but not found
        error_raised = False
        try:
            load_if_file('this_is_code_and_not_a_file')
        except FileNotFoundError:
            error_raised = True
        assert error_raised

        # multiline text will never be mistaken for a file
        assert load_if_file('this_is_code_and_not_a_file\n')

        # neither will text that does not look like a file name
        s = "this is code * and not a file"
        assert s == load_if_file(s)

        # not a file and not mistaken for a file
        assert self.code1 == load_if_file(self.code1)

        # not a file and not mistaken for a file either
        assert self.code2 == load_if_file(self.code2)

        # file correctly loaded
        assert self.code2 == load_if_file(self.filename)

    def test_has_fenced_code(self):
        code1="has fenced code block\n~~~ ebnf\nstart = 'start'\n~~~\n"
        code2="no fenced code block ~~~ ebnf\nstart = 'start'\n~~~\n"
        code3="\n~~~ ebnd\nstart = 'start'\n~~"
        assert has_fenced_code(code1)
        assert not has_fenced_code(code2)
        assert not has_fenced_code(code3)


    def test_logging(self):
        # try:
        #     log_dir()
        #     assert False, "AttributeError should be raised when log_dir() is called outside " \
        #                   "a logging context."
        # except AttributeError:
        #     pass
        res = log_dir()
        if res:
            suspend_logging()
        start_logging(self.LOGDIR)
        assert not os.path.exists(self.LOGDIR), \
            "Log dir should be created lazily!"
        dirname = log_dir()
        # print(type(dirname), dirname)
        assert dirname == self.LOGDIR
        assert is_logging(), "is_logging() should return True, if logging is on"
        save_log_dir = suspend_logging()
        assert not is_logging(), \
            "is_logging() should return False, if innermost logging context " \
            "has logging turned off."
        resume_logging(save_log_dir)
        assert is_logging(), "is_logging() should return True after logging off " \
                             "context has been left"
        info_path = os.path.join(self.LOGDIR, 'info.txt')
        assert os.path.exists(info_path), "an 'info.txt' file should be " \
            "created within a newly created log dir"
        # cleanup
        os.remove(info_path)
        os.rmdir(self.LOGDIR)

    def logging_task(self):
        log_dir()
        assert is_logging(), "Logging should be on inside logging context"
        save_log_dir = suspend_logging()
        assert not is_logging(), "Logging should be off outside logging context"
        resume_logging(save_log_dir)
        # TODO: Some race condition occurs here, but which and why???
        #       Maybe: Some other thread has created logdir but not yet info.txt
        #       Solution: Just return True, cause log_dir() does not guarantee
        #                 existence of 'info.txt', anyway...
        return True

    def test_logging_multiprocessing(self):
        start_logging(self.LOGDIR)
        with concurrent.futures.ProcessPoolExecutor() as ex:
            f1 = ex.submit(self.logging_task)
            f2 = ex.submit(self.logging_task)
            f3 = ex.submit(self.logging_task)
            f4 = ex.submit(self.logging_task)
        assert f1.result()
        assert f2.result()
        assert f3.result()
        assert f4.result()


class TestStringHelpers:
    def test_lstrip_docstring(self):
        str1 = """line
        
            indented line
        line
        """
        assert normalize_docstring(str1) == 'line\n\n    indented line\nline'
        str2 = """
            line
            line
                indented line
                    indented indented line"""
        assert normalize_docstring(str2) == 'line\nline\n    indented line\n        indented ' \
                                         'indented line'


class TestTypeSystemSupport:
    def test_issubtype(self):
        assert issubtype(typing.List, collections.abc.Sequence)
        assert issubtype(typing.Tuple, type(tuple()))
        assert issubtype(typing.Callable, collections.abc.Callable)
        assert issubtype(typing.Tuple[typing.Callable], tuple)


class TestJSONSupport:
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

    def test_stepwise_encoding(self):
        params = {'height': 640, 'width': 480}
        params_literal = JSONstr(json_dumps(params, partially_serialized=True))
        rpc = json_rpc('open_window', params_literal)
        if sys.version_info >= (3, 6):
            assert rpc == '{"jsonrpc":"2.0","method":"open_window","params":{"height":640,"width":480}}', rpc
        else:
            obj = json.loads(rpc)
            assert obj == json.loads('{"jsonrpc":"2.0","method":"open_window","params":{"height":640,"width":480}}')

    def test_custom_null_value(self):
        assert json_dumps(JSONnull) == "null"
        assert json_dumps(JSONnull, partially_serialized=True) == "null"
        assert json.loads(json_dumps(JSONnull)) is None
        null = JSONnull()
        assert json_dumps(null) == "null"
        assert json_dumps(null, partially_serialized=True) == "null"
        assert json.loads(json_dumps(null)) is None

    def test_bool_and_None(self):
        data = [True, False, None, 1, 2.0, "abc"]
        jsons = json_dumps(data, partially_serialized=True)
        assert jsons == '[true,false,null,1,2.0,"abc"]', jsons

    def test_str_escaping(self):
        data = 'The dragon said "hush"!'
        jsons = json_dumps(data, partially_serialized=True)
        assert jsons == r'"The dragon said \"hush\"!"', jsons

    def test_boundary_cases(self):
        assert json_dumps([], partially_serialized=True) == "[]"
        assert json_dumps({}, partially_serialized=True) == "{}"
        assert json_dumps(None, partially_serialized=True) == "null"

    def test_roundtrip(self):
        if sys.version_info >= (3, 6):
            obj = json.loads(self.data)
            jsons = json_dumps(obj, partially_serialized=True)
            assert jsons == self.data


class TestXMLSupport:

    def test_RX_ENTITY(self):
        assert RX_ENTITY.match('&amp;')
        assert not RX_ENTITY.match('&...')

    def test_validate_attribute_value(self):
        assert validate_XML_attribute_value('attribute value test') == '"attribute value test"'
        assert validate_XML_attribute_value("'single quoted string'") \
               == '''"'single quoted string'"'''
        assert validate_XML_attribute_value('"double quoted string"') \
               == """'"double quoted string"'"""
        assert validate_XML_attribute_value("&amp;") == '"&amp;"'

        try:
            validate_XML_attribute_value("&...")
            assert False, "ValueError expected!"
        except ValueError:
            pass

        try:
            validate_XML_attribute_value("<")
            assert False, "ValueError expected!"
        except ValueError:
            pass

        try:
            validate_XML_attribute_value("""'"'""")
            assert False, "ValueError expected!"
        except ValueError:
            pass

    def test_fix_attribute_value(self):
        assert fix_XML_attribute_value("<") == '"&lt;"'
        assert fix_XML_attribute_value("&") == '"&amp;"'
        assert fix_XML_attribute_value("""'"'""") == """'&apos;"&apos;'"""
        assert fix_XML_attribute_value('''" "''') == """'" "'"""
        assert fix_XML_attribute_value("""' '""") == '''"' '"'''

    def test_other_value_types_than_str(self):
        fix_XML_attribute_value(3)
        validate_XML_attribute_value(3)



class TestMisc:
    def test_matching_brackets(self):
        s = """'‘diviniores’, id est digniores, ‘-es’ (PG 3,505C ἁγιαστείαν), sicut est """ \
            """consecratio chrismatis et altaris (sc. divina lex distribuit pontificali ordini). '"""
        unmatched = []
        matches = matching_brackets(s, '(', ')', unmatched)
        assert matches == [(39, 60), (107, 152)] and not unmatched

        s = "a)b(c"
        unmatched = []
        matches = matching_brackets(s, '(', ')', unmatched)
        assert len(matches) == 0 and unmatched == [1, 3]

        s = "a((b)c"
        unmatched = []
        matches = matching_brackets(s, '(', ')', unmatched)
        assert matches == [(2, 4)] and unmatched == [1]

        s= "a(b))c"
        unmatched = []
        matches = matching_brackets(s, '(', ')', unmatched)
        assert matches == [(1, 3)] and unmatched == [4]

        s = "a)(b)(c)(d"
        unmatched = []
        matches = matching_brackets(s, '(', ')', unmatched)
        assert matches == [(2, 4), (5, 7)] and unmatched == [1, 8]

        unmatched = []
        matches = matching_brackets('ab(c', '(', ')', unmatched)
        assert unmatched == [2] and not matches

        unmatched = []
        matches = matching_brackets('ab)c', '(', ')', unmatched)
        assert unmatched == [2] and not matches

        matching_brackets('ab)c', '(', ')')
        matching_brackets('ab)c', '(', ')')


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
