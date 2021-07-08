import asyncio
import json
import os
import sys
import threading
import time

testpath = os.path.abspath(os.path.dirname(__file__))
mainpath = os.path.dirname(testpath)
dhparserpath = os.path.dirname(os.path.dirname(mainpath))

sys.path.append(mainpath)

from DHParser.error import ERROR
from DHParser.server import ExecutionEnvironment, asyncio_run, StreamReaderProxy, \
    StreamWriterProxy,spawn_stream_server, stop_stream_server, split_header
from DHParser.testing import add_header, read_full_content, MockStream
from DHParser.toolkit import json_dumps

import EBNFServer, EBNFParser


class TestCPUBoundTasks:
    def test_cpubound(self):
        diagnostics = EBNFServer.compile_EBNF('')
        json_obj = json.loads(diagnostics)
        assert json_obj[0]['code'] >= ERROR
        diagnostics = EBNFServer.compile_EBNF('document = /.*/')
        assert diagnostics == '[]'

    def test_compile_process(self):
        async def main():
            loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            exec = ExecutionEnvironment(loop)

            diagnostics, rpc_error = await exec.execute(
                exec.process_executor, EBNFServer.compile_EBNF, ('',)
            )
            json_obj = json.loads(diagnostics)
            assert json_obj[0]['code'] >= ERROR

            diagnostics, rpc_error = await exec.execute(
                exec.process_executor, EBNFServer.compile_EBNF, ('document = /.*/',)
            )
            assert diagnostics == '[]'

            diagnostics, rpc_error = await exec.execute(
                exec.thread_executor, EBNFServer.compile_EBNF, ('',)
            )
            json_obj = json.loads(diagnostics)
            assert json_obj[0]['code'] >= ERROR

            diagnostics, rpc_error = await exec.execute(
                exec.thread_executor, EBNFServer.compile_EBNF, ('document = /.*/',)
            )
            assert diagnostics == '[]'

            exec.shutdown()

        asyncio_run(main())


    def test_compileEBNFFork(self):
        fname = os.path.join(dhparserpath, 'examples/EBNF/FixedEBNF.ebnf')
        with open(fname, 'r') as f:
            source = f.read()
        diagnostics, signature = EBNFServer.compile_EBNF(source, b'')
        diag_json = json.loads(diagnostics)
        assert len(diag_json) == 6, str(len(diag_json))
        assert len(signature) == 6 * 8, str(len(signature))


# class TestServerStatic:
#     def test_EBNFServer(self):
#         server = EBNFServer.EBNFLanguageServerProtocol()
#         print(json_dumps(server.completion_items))
#         print(json_dumps(server.completion_labels))


initialize_request = {'jsonrpc': '2.0',
 'id': 0,
 'method': 'initialize',
 'params': {'processId': 17400,
  'rootPath': 'c:\\Users\\di68kap\\PycharmProjects\\DHParser\\examples\\EBNF',
  'rootUri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF',
  'capabilities': {'workspace': {'applyEdit': True,
    'workspaceEdit': {'documentChanges': True},
    'didChangeConfiguration': {'dynamicRegistration': True},
    'didChangeWatchedFiles': {'dynamicRegistration': True},
    'symbol': {'dynamicRegistration': True,
     'symbolKind': {'valueSet': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                                 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]}},
    'executeCommand': {'dynamicRegistration': True},
    'configuration': True,
    'workspaceFolders': True},
   'textDocument': {'publishDiagnostics': {'relatedInformation': True},
    'synchronization': {'dynamicRegistration': True,
     'willSave': True,
     'willSaveWaitUntil': True,
     'didSave': True},
    'completion': {'dynamicRegistration': True,
     'contextSupport': True,
     'completionItem': {'snippetSupport': True,
      'commitCharactersSupport': True,
      'documentationFormat': ['markdown', 'plaintext'],
      'deprecatedSupport': True,
      'preselectSupport': True},
     'completionItemKind': {'valueSet': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                                         15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]}},
    'hover': {'dynamicRegistration': True,
     'contentFormat': ['markdown', 'plaintext']},
    'signatureHelp': {'dynamicRegistration': True,
     'signatureInformation': {'documentationFormat': ['markdown',
       'plaintext']}},
    'definition': {'dynamicRegistration': True},
    'references': {'dynamicRegistration': True},
    'documentHighlight': {'dynamicRegistration': True},
    'documentSymbol': {'dynamicRegistration': True,
     'symbolKind': {'valueSet': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                                 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]},
     'hierarchicalDocumentSymbolSupport': True},
    'codeAction': {'dynamicRegistration': True,
     'codeActionLiteralSupport': {'codeActionKind': {'valueSet': ['',
        'quickfix',
        'refactor',
        'refactor.extract',
        'refactor.inline',
        'refactor.rewrite',
        'source',
        'source.organizeImports']}}},
    'codeLens': {'dynamicRegistration': True},
    'formatting': {'dynamicRegistration': True},
    'rangeFormatting': {'dynamicRegistration': True},
    'onTypeFormatting': {'dynamicRegistration': True},
    'rename': {'dynamicRegistration': True},
    'documentLink': {'dynamicRegistration': True},
    'typeDefinition': {'dynamicRegistration': True},
    'implementation': {'dynamicRegistration': True},
    'colorProvider': {'dynamicRegistration': True},
    'foldingRange': {'dynamicRegistration': True,
     'rangeLimit': 5000,
     'lineFoldingOnly': True}}},
  'trace': 'off',
  'workspaceFolders': [{'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF',
    'name': 'EBNF'}]}}

initialized_notification = {"jsonrpc": "2.0", "method": "initialized", "params": {}}

didOpen_notification = {'jsonrpc': '2.0',
 'method': 'textDocument/didOpen',
 'params': {'textDocument': {'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF/EBNF.ebnf',
   'languageId': 'ebnf',
   'version': 1,
   'text': r"""# EBNF-Grammar in EBNF
# This grammar is tuned for flexibility, that is, it supports as many
# different flavors of EBNF as possible. However, this flexibility
# comes at the cost of some ambiguities. In particular:
#
#    1. the alternative OR-operator / could be mistaken for the start
#       of a regular expression and vice versa, and
#    2. character ranges [a-z] can be mistaken for optional blocks
#       and vice versa
#
# A strategy to avoid these ambiguities is to do all of the following:
#
#     - replace the free_char-parser by a never matching parser
#     - if this is done, it is safe to replace the char_range_heuristics-
#       parser by an always matching parser
#     - replace the regex_heuristics by an always matching parser
#
# Ambiguities can also be avoided by NOT using all the syntactic variants
# made possible by this EBNF-grammar within one and the same EBNF-document
@ comment    = /(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/|\(\*(?:.|\n)*?\*\)/
    # comments can be either C-Style: /* ... */
    # or pascal/modula/oberon-style: (* ... *)
    # or python-style: # ... \n, excluding, however, character markers: #x20
@ whitespace = /\s*/                            # whitespace includes linefeed
@ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
@ disposable = pure_elem, countable, FOLLOW_UP, SYM_REGEX, ANY_SUFFIX, EOF
@ drop       = whitespace, EOF                  # do not include these even in the concrete syntax tree
@ RNG_BRACE_filter = matching_bracket()         # filter or transform content of RNG_BRACE on retrieve
# re-entry-rules for resuming after parsing-error
@ definition_resume = /\n\s*(?=@|\w+\w*\s*=)/
@ directive_resume  = /\n\s*(?=@|\w+\w*\s*=)/
# specialized error messages for certain cases
@ definition_error  = /,/, 'Delimiter "," not expected in definition!\nEither this was meant to '
                           'be a directive and the directive symbol @ is missing\nor the error is '
                           'due to inconsistent use of the comma as a delimiter\nfor the elements '
                           'of a sequence.'
#: top-level
syntax     = ~ { definition | directive } EOF
definition = symbol §:DEF~ [ :OR~ ] expression :ENDL~ & FOLLOW_UP  # [:OR~] to support v. Rossum's syntax
directive  = "@" §symbol "=" (regexp | literals | procedure | symbol !DEF)
             { "," (regexp | literals | procedure | symbol !DEF) } & FOLLOW_UP
literals   = { literal }+                       # string chaining, only allowed in directives!
procedure  = SYM_REGEX "()"                     # procedure name, only allowed in directives!
FOLLOW_UP  = `@` | symbol | EOF
#: components
expression = sequence { :OR~ sequence }
sequence   = ["§"] ( interleave | lookaround )  # "§" means all following terms mandatory
             { :AND~ ["§"] ( interleave | lookaround ) }
interleave = difference { "°" ["§"] difference }
lookaround = flowmarker § (oneormore | pure_elem)
difference = term ["-" § (oneormore | pure_elem)]
term       = oneormore | counted | repetition | option | pure_elem
#: elements
countable  = option | oneormore | element
pure_elem  = element § !ANY_SUFFIX              # element strictly without a suffix
element    = [retrieveop] symbol !:DEF          # negative lookahead to be sure it's not a definition
           | literal
           | plaintext
           | regexp
           | char_range
           | character ~
           | any_char
           | whitespace
           | group
ANY_SUFFIX = /[?*+]/
#: flow-operators
flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
           | "<-!" | "<-&"                      # '<-!' negative lookbehind, '<-&' positive lookbehind
retrieveop = "::" | ":?" | ":"                  # '::' pop, ':?' optional pop, ':' retrieve
#: groups
group      = "(" no_range §expression ")"
oneormore  = "{" no_range expression "}+" | element "+"
repetition = "{" no_range §expression "}" | element "*" no_range
option     = !char_range "[" §expression "]" | element "?"
counted    = countable range | countable :TIMES~ multiplier | multiplier :TIMES~ §countable
range      = RNG_BRACE~ multiplier [ :RNG_DELIM~ multiplier ] ::RNG_BRACE~
no_range   = !multiplier | &multiplier :TIMES
multiplier = /[1-9]\d*/~
#: leaf-elements
symbol     = SYM_REGEX ~                        # e.g. expression, term, parameter_list
literal    = /"(?:(?<!\\)\\"|[^"])*?"/~         # e.g. "(", '+', 'while'
           | /'(?:(?<!\\)\\'|[^'])*?'/~         # whitespace following literals will be ignored tacitly.
plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~         # like literal but does not eat whitespace
           | /´(?:(?<!\\)\\´|[^´])*?´/~
regexp     = :RE_LEADIN RE_CORE :RE_LEADOUT ~   # e.g. /\w+/, ~/#.*(?:\n|$)/~
# regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~     # e.g. /\w+/, ~/#.*(?:\n|$)/~
char_range = `[` &char_range_heuristics
                 [`^`] (character | free_char) { [`-`] character | free_char } "]"
character  = :CH_LEADIN HEXCODE
free_char  = /[^\n\[\]\\]/ | /\\[nrt`´'"(){}\[\]\/\\]/
any_char   = "."
whitespace = /~/~                               # insignificant whitespace
#: delimiters
EOF = !/./ [:?DEF] [:?OR] [:?AND] [:?ENDL]      # [:?DEF], [:?OR], ... clear stack by eating stored value
           [:?RNG_DELIM] [:?BRACE_SIGN] [:?CH_LEADIN] [:?TIMES] [:?RE_LEADIN] [:?RE_LEADOUT]
DEF        = `=` | `:=` | `::=` | `<-` | /:\n/ | `: `  # with `: `, retrieve markers mustn't be followed by a blank!
OR         = `|` | `/` !regex_heuristics
AND        = `,` | ``
ENDL       = `;` | ``
RNG_BRACE  = :BRACE_SIGN
BRACE_SIGN = `{` | `(`
RNG_DELIM  = `,`
TIMES      = `*`
RE_LEADIN  = `/` &regex_heuristics | `^/`
RE_LEADOUT = `/`
CH_LEADIN  = `0x` | `#x`
#: heuristics
char_range_heuristics  = ! ( /[\n\t ]/
                           | ~ literal_heuristics
                           | [`::`|`:?`|`:`] SYM_REGEX /\s*\]/ )
literal_heuristics     = /~?\s*"(?:[\\]\]|[^\]]|[^\\]\[[^"]*)*"/
                       | /~?\s*'(?:[\\]\]|[^\]]|[^\\]\[[^']*)*'/
                       | /~?\s*`(?:[\\]\]|[^\]]|[^\\]\[[^`]*)*`/
                       | /~?\s*´(?:[\\]\]|[^\]]|[^\\]\[[^´]*)*´/
                       | /~?\s*\/(?:[\\]\]|[^\]]|[^\\]\[[^\/]*)*\//
regex_heuristics       = /[^ ]/ | /[^\/\n*?+\\]*[*?+\\][^\/\n]\//
#: basic-regexes
RE_CORE    = /(?:(?<!\\)\\(?:\/)|[^\/])*/       # core of a regular expression, i.e. the dots in /.../
SYM_REGEX  = /(?!\d)\w+/                        # regular expression for symbols
HEXCODE    = /[A-Fa-f0-9]{1,8}/
"""}}}

didChange_notifictaion_1 = {'jsonrpc': '2.0',
 'method': 'textDocument/didChange',
 'params': {'textDocument': {'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF/EBNF.ebnf',
   'version': 2},
  'contentChanges': [{'range': {'start': {'line': 20, 'character': 0},
     'end': {'line': 20, 'character': 0}},
    'rangeLength': 0,
    'text': '@'}]}}

completion_request = {'jsonrpc': '2.0',
 'id': 1,
 'method': 'textDocument/completion',
 'params': {'textDocument': {'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF/EBNF.ebnf'},
  'position': {'line': 20, 'character': 1},
  'context': {'triggerKind': 2, 'triggerCharacter': '@'}}}

didSave_notification_1 = {'jsonrpc': '2.0',
 'method': 'textDocument/didSave',
 'params': {'textDocument': {'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF/EBNF.ebnf',
   'version': 2}}}

didChange_notification_2 = {'jsonrpc': '2.0',
 'method': 'textDocument/didChange',
 'params': {'textDocument': {'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF/EBNF.ebnf',
   'version': 3},
  'contentChanges': [{'range': {'start': {'line': 20, 'character': 0},
     'end': {'line': 20, 'character': 1}},
    'rangeLength': 1,
    'text': ''}]}}

didSave_notification_2 = {'jsonrpc': '2.0',
 'method': 'textDocument/didSave',
 'params': {'textDocument': {'uri': 'file:///c%3A/Users/di68kap/PycharmProjects/DHParser/examples/EBNF/EBNF.ebnf',
   'version': 3}}}

shutdown_request = {'jsonrpc': '2.0', 'id': 2, 'method': 'shutdown', 'params': None}

exit_notification = {'jsonrpc': '2.0', 'method': 'exit', 'params': None}


class TestServerDynamic:
    def setup(self):
        self.EBNF_lsp = EBNFServer.EBNFLanguageServerProtocol()
        self.lsp_table = self.EBNF_lsp.lsp_fulltable.copy()
        self.lsp_table.setdefault('default', EBNFParser.compile_src)
        self.pipeA = MockStream('pipeA')
        self.pipeB = MockStream('pipeB')
        self.readerA = StreamReaderProxy(self.pipeA)
        self.writerA = StreamWriterProxy(self.pipeA)
        self.readerB = StreamReaderProxy(self.pipeB)
        self.writerB = StreamWriterProxy(self.pipeB)

    def test_server_processes(self):
        # This test takes a few seconds!
        async def test_interaction(reader, writer) -> bool:
            async def send(json_obj: str):
                writer.write(add_header(json.dumps(json_obj).encode()))
                await writer.drain()

            async def receive() -> str:
                package = await read_full_content(reader)
                header, raw_data, backlog = split_header(package)
                return json.loads(raw_data.decode())

            publishDiagnosticsCounter = 0

            await send(initialize_request)
            data = await receive()
            assert "result" in data and data['id'] == initialize_request['id']
            await send(initialized_notification)
            await send(didOpen_notification)
            await asyncio.sleep(EBNFServer.RECOMPILE_DELAY + 2)
            await send(didChange_notifictaion_1)
            await asyncio.sleep(0.1)
            await send(completion_request)
            await asyncio.sleep(EBNFServer.RECOMPILE_DELAY + 0.5)
            await send(didSave_notification_1)
            await asyncio.sleep(0.1)
            await send(didChange_notification_2)
            await asyncio.sleep(EBNFServer.RECOMPILE_DELAY + 0.5)
            await send(didSave_notification_2)
            await asyncio.sleep(0.1)
            data = await receive()
            while 'method' in data:
                assert data['method'] == 'textDocument/publishDiagnostics'
                publishDiagnosticsCounter += 1
                data = await receive()
            assert publishDiagnosticsCounter == 1
            assert 'id' in data and data['id'] == completion_request['id']
            while self.pipeB.data_available():
                data = await receive()
                if 'method' in data:
                    assert data['method'] == 'textDocument/publishDiagnostics'
                    publishDiagnosticsCounter += 1
                await asyncio.sleep(0.1)
            assert publishDiagnosticsCounter == 3
            await send(shutdown_request)
            data = await receive()
            assert 'id' in data and data['id'] == shutdown_request['id']
            await send(exit_notification)
            await asyncio.sleep(0.5)

        p = None
        try:
            p = spawn_stream_server(self.readerA, self.writerB,
                                    {'rpc_functions': self.lsp_table,
                                     'cpu_bound': set(self.EBNF_lsp.cpu_bound.lsp_table.keys()),
                                     'blocking': set(self.EBNF_lsp.blocking.lsp_table.keys()),
                                     'connection_callback': self.EBNF_lsp.connect,
                                     'server_name': 'EBNFServer',
                                     'strict_lsp': True},
                                    threading.Thread)
            asyncio_run(test_interaction(self.readerB, self.writerA))
        finally:
            if p is not None:
                value_error = stop_stream_server(self.readerB, self.writerA)
                # assert value_error, "server hasn't been shutdown orderly"
                p.join()



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
