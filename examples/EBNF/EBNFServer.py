#!/usr/bin/env python3

"""EBNFServer.py - starts a server (if not already running) for the
                    compilation of EBNF

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2019 Bavarian Academy of Sciences and Humanities

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
import os
import sys

assert sys.version_info >= (3, 5, 7), "DHParser requires at least Python-Version 3.5.7"

scriptpath = os.path.dirname(__file__)

STOP_SERVER_REQUEST = b"__STOP_SERVER__"   # hardcoded in order to avoid import from DHParser.server
IDENTIFY_REQUEST = "identify()"
LOGGING_REQUEST = 'logging("")'

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8888

DATA_RECEIVE_LIMIT = 262144

config_filename_cache = ''


def get_config_filename() -> str:
    """
    Returns the file name of a temporary config file that stores
    the host and port of the currently running server.
    """
    global config_filename_cache
    if config_filename_cache:
        return config_filename_cache

    def probe(dir_list) -> str:
        for tmpdir in []:
            if os.path.exists(tmpdir) and os.path.isdir(tmpdir):
                return tmpdir
        return ''

    if sys.platform.find('win') >= 0:
        tmpdir = probe([r'C:\TEMP', r'C:\TMP', r'\TEMP', r'\TMP'])
    else:
        tmpdir = probe(['~/tmp', '/tmp', '/var/tmp', 'usr/tmp'])
    config_filename_cache = os.path.join(tmpdir, os.path.basename(__file__)) + '.cfg'
    return config_filename_cache


def retrieve_host_and_port():
    """
    Retrieve host and port from temporary config file or return default values
    for host and port, in case the temporary config file does not exist.
    """
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    cfg_filename = get_config_filename()
    try:
        with open(cfg_filename) as f:
            print('Reading host and port from file: ' + cfg_filename)
            host, ports = f.read().strip(' \n').split(' ')
            port = int(ports)
    except FileNotFoundError:
        pass
    except ValueError:
        print('removing invalid config file: ' + cfg_filename)
        os.remove(cfg_filename)
    return host, port


def asyncio_run(coroutine):
    """Backward compatible version of Pyhon3.7's `asyncio.run()`"""
    if sys.version_info >= (3, 7):
        return asyncio.run(coroutine)
    else:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()


def json_rpc(func, params={}, ID=None) -> str:
    """Generates a JSON-RPC-call for `func` with parameters `params`"""
    return str({"jsonrpc": "2.0", "method": func.__name__, "params": params, "id": ID})


class EBNFCPUBoundTasks:
    def __init__(self, lsp_data: dict):
        from DHParser.compile import ResultTuple
        from DHParser.server import gen_lsp_table

        self.lsp_data = lsp_data
        self.lsp_table = gen_lsp_table(self, prefix='lsp_')

    def compile_EBNF(self, text: str):
        from DHParser.compile import compile_source
        from DHParser.ebnf import get_ebnf_preprocessor, get_ebnf_grammar, get_ebnf_transformer, \
            get_ebnf_compiler
        compiler = get_ebnf_compiler("EBNFServerAnalyse", text)
        result, messages, _ = compile_source(
            text, get_ebnf_preprocessor(), get_ebnf_grammar(), get_ebnf_transformer(), compiler)
        # TODO: return errors as well as (distilled) information about symbols for code propositions
        return None


class EBNFBlockingTasks:
    def __init__(self, lsp_data: dict):
        from DHParser.server import gen_lsp_table
        self.lsp_data = lsp_data
        self.lsp_table = gen_lsp_table(self, prefix='lsp_')


RECOMPILE_DELAY = 0.5


class EBNFLanguageServerProtocol:
    """
    For the specification and implementation of the language server protocol, see:
        https://code.visualstudio.com/api/language-extensions/language-server-extension-guide
        https://microsoft.github.io/language-server-protocol/
        https://langserver.org/
    """
    # completion_fields = ['label', 'insertText', 'insertTextFormat', 'documentation']
    # completions = [['anonymous', '@ anonymous = /${1:_\\w+}/', 2,
    #                 'List of symbols or a regular expression to identify those definitions '
    #                 'that shall not yield named tags in the syntax tree.'],
    #                ['comment', '@ comment = /${1:#.*(?:\\n|$)}/', 2,
    #                 'Regular expression for comments.'],
    #                ['drop', '@ drop = ${1:whitespace, token, regexp}', 2,
    #                 'List of definitions for which the parsed content shall be dropped rather '
    #                 'than included in the syntax tree. The special values "whitespace", "token" '
    #                 'and "regexp" stand for their respective classes instead of particular '
    #                 'definitions.'],
    #                ['ignorecase', '@ ignorecase = ${1|yes,no|}', 2,
    #                 'Ignore the case wihin regular expressions.'],
    #                ['literalws', '@ literalws = ${1|right,left,both,none|}', 2,
    #                 'Determines one which side (if any) of a string-literal the whitespace '
    #                 'shall be eaten'],
    #                ['whitespace', '@ whitespace = /${1:\\s*}/', 2, 'Regular expression for '
    #                 'insignificant whitespace (denoted by a tilde ~)'],
    #                ['_resume', '@ ${1:SYMBOL}_resume = /${2: }/', 2, 'A list of regular '
    #                 'expressions identifying a place where the parent parser shall catch up the '
    #                 'parsing process, if within the given parser an element marked as mandatory '
    #                 'with the §-sign did not match. (DHParser-extension to EBNF.)'],
    #                ['_skip', '@ ${1:SYMBOL}_skip = /${2: }/', 2,
    #                 'A list of regular expressions to identify a place to which a series-parser '
    #                 'shall skip, if a mandatory "§"-item did not match. The parser skips to the '
    #                 'place after the match except for lookahead-expressions. '
    #                 '(DHParser-extension to EBNF.)'],
    #                ['_error', '@ ${1:SYMBOL}_error = /${2: }/, "${3:error message}"', 2,
    #                 'An error message preceded by a regular expression or string-literal that '
    #                 'will be emitted instead of the stock message, if a mandatory element '
    #                 'violation occured within the given parser. (DHParser-extension to EBNF)'],
    #                ['_filter', '@ ${1:SYMBOL}_filter = ${2:funcname}', 2,
    #                 'Name of a Python-match-function that is applied when retrieving a stored '
    #                 'symbol. (DHParser-extension to EBNF)']]


    def __init__(self):
        from DHParser.server import gen_lsp_table
        self.lsp_data = {
            'processId': 0,
            'rootUri': '',
            'clientCapabilities': {},
            'serverInfo': { "name": "EBNF-Server", "version": "0.2" },
            'serverCapabilities': {
                "textDocumentSync": 1,  # 0 = None, 1 = full, 2 = incremental
                "completionProvider": {
                    "resolveProvider": False,
                    "triggerCharacters": ['@']
                }
            }
        }
        self.connection = None
        self.cpu_bound = EBNFCPUBoundTasks(self.lsp_data)
        self.blocking = EBNFBlockingTasks(self.lsp_data)
        self.lsp_table = gen_lsp_table(self, prefix='lsp_')
        self.lsp_fulltable = self.lsp_table.copy()
        assert self.lsp_fulltable.keys().isdisjoint(self.cpu_bound.lsp_table.keys())
        self.lsp_fulltable.update(self.cpu_bound.lsp_table)
        assert self.lsp_fulltable.keys().isdisjoint(self.blocking.lsp_table.keys())
        self.lsp_fulltable.update(self.blocking.lsp_table)

        self.pending_changes = dict()  # uri -> text
        self.current_text = dict()     # uri -> TextBuffer

        # self.completionItems = [{k: v for k, v in chain(zip(self.completion_fields, item),
        #                                                 [['kind', 2]])}
        #                         for item in self.completions]

    def connect(self, connection):
        self.connection = connection

    def lsp_initialize(self, **kwargs):
        self.lsp_data['processId'] = kwargs['processId']
        self.lsp_data['rootUri'] = kwargs['rootUri']
        self.lsp_data['clientCapabilities'] = kwargs['capabilities']
        return {'capabilities': self.lsp_data['serverCapabilities'],
                'serverInfo': self.lsp_data['serverInfo']}

    def lsp_custom(self, **kwargs):
        return kwargs

    def lsp_shutdown(self):
        self.lsp_data['processId'] = 0
        self.lsp_data['rootUri'] = ''
        self.lsp_data['clientCapabilities'] = {}
        return {}

    async def compile_text(self, uri: str) -> None:
        text_buffer = self.pending_changes.get(uri, None)
        if text_buffer:
            exenv = self.connection.exec
            del self.pending_changes[uri]
            result, rpc_error = await exenv.execute(exenv.process_executor,
                                                    self.cpu_bound.compile_EBNF,
                                                    (text_buffer.snapshot(),))
            # werte Ergebnis aus
            # sende eine PublishDiagnostics-Notification via self.connect
        return None

    async def lsp_textDocument_didOpen(self, textDocument):
        from DHParser.stringview import TextBuffer
        uri = textDocument['uri']
        text = textDocument['text']
        text_buffer = TextBuffer(text, int(textDocument.get('version', 0)))
        self.current_text[uri] = text_buffer
        self.pending_changes[uri] = text_buffer
        await self.compile_text(uri)
        return None

    def lsp_textDocument_didSave(self, **kwargs):
        return None

    def lsp_textDocument_didClose(self, **kwargs):
        return None

    async def lsp_textDocument_didChange(self, textDocument: dict, contentChanges: list):
        uri = textDocument['uri']
        version = int(textDocument['version'])
        if uri not in self.current_text:
            return {}, (-32602, "Invalid uri: " + uri)
        if contentChanges:
            from DHParser.stringview import TextBuffer
            if 'range' in contentChanges[0]:
                text_buffer = self.current_text[uri]
                text_buffer.text_edits(contentChanges, version)
                self.pending_changes[uri] = text_buffer
            else:
                text_buffer = TextBuffer(contentChanges[0]['text'], version)
                self.current_text[uri] = text_buffer
            await asyncio.sleep(RECOMPILE_DELAY)
            await self.compile_text(uri)
        return None

    def lsp_textDocument_completion(self, textDocument: dict, position: dict, context: dict):
        from DHParser.toolkit import text_pos
        text = self.current_text[textDocument['uri']]
        if context['triggerKind'] == 2:  # Trigger Character
            return {}   # leave proposing snippets to VSCode
        line = position['line']
        col = position['character']
        pos = text_pos(text, line, col)
        char = text[pos]
        return None

    def lsp_S_cancelRequest(self, **kwargs):
        return None


def run_server(host, port, log_path=None):
    global scriptpath
    grammar_src = os.path.abspath(__file__).replace('Server.py', '.ebnf')
    dhparserdir = os.path.abspath(os.path.join(scriptpath, '../../'))
    if scriptpath not in sys.path:
        sys.path.append(scriptpath)
    if dhparserdir not in sys.path:
        sys.path.append(dhparserdir)
    try:
        from EBNFParser import compile_src
    except ModuleNotFoundError:
        from tst_EBNF_grammar import recompile_grammar
        recompile_grammar(grammar_src, force=False)
        from EBNFParser import compile_src
    from DHParser.server import Server, gen_lsp_table
    config_filename = get_config_filename()
    try:
        with open(config_filename, 'w') as f:
            f.write(host + ' ' + str(port))
    except PermissionError:
        print('PermissionError: Could not write temporary config file: ' + config_filename)

    print('Starting server on %s:%i' % (host, port))
    EBNF_lsp = EBNFLanguageServerProtocol()
    lsp_table = EBNF_lsp.lsp_fulltable.copy()
    lsp_table.setdefault('default', compile_src)
    EBNF_server = Server(rpc_functions=lsp_table,
                         cpu_bound=set(EBNF_lsp.cpu_bound.lsp_table.keys()),
                         blocking=set(EBNF_lsp.blocking.lsp_table.keys()),
                         connection_callback=EBNF_lsp.connect,
                         server_name='EBNFServer',
                         strict_lsp=True)
    if log_path is not None:
        EBNF_server.echo_log = True
        print(EBNF_server.start_logging(log_path.strip('" \'')))
    try:
        EBNF_server.run_server(host, port)  # returns only after server has stopped
    except OSError as e:
        print(e)
        print('Could not start server. Shutting down!')
        sys.exit(1)
    finally:
        cfg_filename = get_config_filename()
        print('Server on %s:%i stopped' % (host, port))
        try:
            os.remove(cfg_filename)
            print('removing temporary config file: ' + cfg_filename)
        except FileNotFoundError:
            pass


async def send_request(request, host, port):
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(request.encode() if isinstance(request, str) else request)
    data = await reader.read(DATA_RECEIVE_LIMIT)
    writer.close()
    if sys.version_info >= (3, 7):
        await writer.wait_closed()
    return data.decode()


def start_server_daemon(host, port):
    import subprocess, time
    try:
        subprocess.Popen([__file__, '--startserver', host, str(port)])
    except OSError:
        subprocess.Popen([sys.executable, __file__, '--startserver', host, str(port)])
    countdown = 20
    delay = 0.05
    result = None
    while countdown > 0:
        try:
            result = asyncio_run(send_request(IDENTIFY_REQUEST, host, port))
            countdown = 0
        except ConnectionRefusedError:
            time.sleep(delay)
            delay += 0.0
            countdown -= 1
    if result is None:
        print('Could not start server or establish connection in time :-(')
        sys.exit(1)
    print(result)


def parse_logging_args(args):
    if args.logging:
        echo = repr('ECHO_ON') if args.start else repr('ECHO_OFF')
        if args.logging in ('OFF', 'STOP', 'NO', 'FALSE'):
            log_path = repr(None)
            echo = repr('ECHO_OFF')
        elif args.loggigng in ('ON', 'START', 'YES', 'TRUE'):
            log_path = repr('')
        else:
            log_path = args.logging
        request = LOGGING_REQUEST.replace('""', ", ".join((log_path, echo)))
        print('Logging to file %s with call %s' % (repr(log_path), request))
        return log_path, request
    else:
        return None, ''


if __name__ == "__main__":
    from argparse import ArgumentParser, REMAINDER
    parser = ArgumentParser(description="Setup and Control of a Server for processing EBNF-files.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('file', nargs='?')
    group.add_argument('-t', '--status', action='store_true',
                       help="displays the server's status, e.g. whether it is running")
    group.add_argument('-s', '--startserver', nargs='*', metavar=("HOST", "PORT"),
                       help="starts the server")
    group.add_argument('-d', '--startdaemon', action='store_true',
                       help="starts the server in the background")
    group.add_argument('-k', '--stopserver', action='store_true',
                       help="starts the server")
    parser.add_argument('-o', '--host', nargs=1, default=[''],
                        help='host name or IP-address of the server (default: 127.0.0.1)')
    parser.add_argument('-p', '--port', nargs=1, type=int, default=[-1],
                        help='port number of the server (default:8888)')
    parser.add_argument('-l', '--logging', nargs='?', metavar="ON|LOG_DIR|OFF",
                        help='turns logging on (default) or off or writes log to a '
                             'specific directory (implies on)')

    args = parser.parse_args()

    host = args.host[0]
    port = int(args.port[0])
    if port < 0 or not host:
        # if host and port have not been specified explicitly on the command
        # line, try to retrieve them from (temporary) config file or use
        # hard coded default values
        host, port = retrieve_host_and_port()

    if args.status:
        try:
            result = asyncio_run(send_request(IDENTIFY_REQUEST, host, port))
            print('Server ' + str(result) + ' running on ' + host + ':' + str(port))
        except ConnectionRefusedError:
            print('No server running on: ' + host + ':' + str(port))

    elif args.startserver is not None:
        portstr = None
        if len(args.startserver) == 1:
            host, portstr = args.startserver[0].split(':')
        elif len(args.startserver) == 2:
            host, portstr = args.startserver
        elif len(args.startserver) != 0:
            parser.error('Wrong number of arguments for "--startserver"!')
        if portstr is not None:
            try:
                port = int(portstr)
            except ValueError:
                parser.error('port must be a number!')
        log_path, _ = parse_logging_args(args)
        sys.exit(run_server(host, port, log_path))

    elif args.startdaemon:
        log_path, log_request = parse_logging_args(args)
        start_server_daemon(host, port)
        if log_request:
            print(asyncio_run(send_request(log_request, host, port)))

    elif args.stopserver:
        try:
            result = asyncio_run(send_request(STOP_SERVER_REQUEST, host, port))
        except ConnectionRefusedError as e:
            print(e)
            sys.exit(1)
        print(result)

    elif args.logging:
        log_path, request = parse_logging_args(args)
        print(asyncio_run(send_request(request, host, port)))

    elif args.file:
        file_name = args.file
        if not file_name.endswith(')'):
            # argv does not seem to be a command (e.g. "identify()") but a file name or path
            file_name = os.path.abspath(file_name)
            # print(file_name)
        log_path, log_request = parse_logging_args(args)
        try:
            if log_request:
                print(asyncio_run(send_request(log_request, host, port)))
            result = asyncio_run(send_request(file_name, host, port))
        except ConnectionRefusedError:
            start_server_daemon(host, port)               # start server first
            if log_request:
                print(asyncio_run(send_request(log_request, host, port)))
            result = asyncio_run(send_request(file_name, host, port))
        if len(result) >= DATA_RECEIVE_LIMIT:
            print(result, '...')
        else:
            print(result)

    else:
        print('Usages:\n'
              + '    python EBNFServer.py --startserver [--host host] [--port port] [--logging [ON|LOG_PATH|OFF]]\n'
              + '    python EBNFServer.py --startdaemon [--host host] [--port port] [--logging [ON|LOG_PATH|OFF]]\n'
              + '    python EBNFServer.py --stopserver\n'
              + '    python EBNFServer.py --status\n'
              + '    python EBNFServer.py --logging [ON|LOG_PATH|OFF]\n'
              + '    python EBNFServer.py FILENAME.dsl [--host host] [--port port]  [--logging [ON|LOG_PATH|OFF]]')
        sys.exit(1)
