#!/usr/bin/python3

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
        from DHParser.ebnf import compile_ebnf


class EBNFBlockingTasks:
    def __init__(self, lsp_data: dict):
        from DHParser.server import gen_lsp_table
        self.lsp_data = lsp_data
        self.lsp_table = gen_lsp_table(self, prefix='lsp_')


class EBNFLanguageServerProtocol:
    """
    For the specification and implementation of the language server protocol, see:
        https://code.visualstudio.com/api/language-extensions/language-server-extension-guide
        https://microsoft.github.io/language-server-protocol/
        https://langserver.org/
    """
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
                    "triggerCharacters": ['#', '*']
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

    def lsp_textDocument_didOpen(self, textDocument):
        return None

    def lsp_textDocument_didSave(self, **kwargs):
        return None

    def lsp_textDocument_didClose(self, **kwargs):
        return None

    def lsp_textDocument_didChange(self, textDocument: dict, contentChanges: list):
        uri = textDocument['uri']
        self.pending_changes[uri] = contentChanges[0]['text']
        asyncio.sleep(3)
        text = self.pending_changes.get(uri, None)
        if text:
            exenv = self.connection.exec
            del self.pending_changes[uri]
            result, rpc_error = await exenv.execute(exenv.process_executor,
                                                    self.cpu_bound.compile_EBNF,
                                                    (text,))
        return None

    def lsp_textDocument_completion(self, **kwargs):
        print('completion', kwargs)
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
        from EBNFCompiler import compile_src
    except ModuleNotFoundError:
        from tst_EBNF_grammar import recompile_grammar
        recompile_grammar(os.path.join(scriptpath, 'EBNF.ebnf'), force=False)
        from EBNFCompiler import compile_src
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
        try:
            subprocess.Popen(['python3', __file__, '--startserver', host, str(port)])
        except FileNotFoundError:
            subprocess.Popen(['python', __file__, '--startserver', host, str(port)])
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


def print_usage_and_exit():
    print('Usages:\n'
          + '    python EBNFServer.py --startserver [--host host] [--port port] [--logging [ON|LOG_PATH|OFF]]\n'
          + '    python EBNFServer.py --startdaemon [--host host] [--port port] [--logging [ON|LOG_PATH|OFF]]\n'
          + '    python EBNFServer.py --stopserver\n'
          + '    python EBNFServer.py --status\n'
          + '    python EBNFServer.py --logging [ON|LOG_PATH|OFF]\n'
          + '    python EBNFServer.py FILENAME.dsl [--host host] [--port port]  [--logging [ON|LOG_PATH|OFF]]')
    sys.exit(1)


def assert_if(cond: bool, message: str):
    if not cond:
        if message:
            print(message)
        print_usage_and_exit()


def parse_logging_args(argv):
    try:
        i = argv.index('--logging')
        echo = repr('ECHO_ON') if argv[1].lower() == '--startserver' else repr('ECHO_OFF')
        del argv[i]
        if i < len(argv):
            arg = argv[i].upper()
            if arg in ('OFF', 'STOP', 'NO', 'FALSE'):
                log_path = repr(None)
                echo = repr('ECHO_OFF')
            elif arg in ('ON', 'START', 'YES', 'TRUE'):
                log_path = repr('')
            else:
                log_path = repr(argv[i])
            del argv[i]
        else:
            log_path = repr('')
        args = log_path, echo
        request = LOGGING_REQUEST.replace('""', ", ".join(args))
        print('Logging to file %s with call %s' % (repr(log_path), request))
        return log_path, request
    except ValueError:
        return None, ''


if __name__ == "__main__":
    host, port = '', -1

    # read and remove "--host ..." and "--port ..." parameters from sys.argv
    argv = []
    i = 0
    while i < len(sys.argv):
        if sys.argv[i] in ('--host', '-h'):
            assert_if(i < len(sys.argv) - 1, 'host missing!')
            host = sys.argv[i+1]
            i += 1
        elif sys.argv[i] in ('--port', '-p'):
            assert_if(i < len(sys.argv) - 1, 'port number missing!')
            try:
                port = int(sys.argv[i+1])
            except ValueError:
                assert_if(False, 'invalid port number: ' + sys.argv[i+1])
            i += 1
        else:
            argv.append(sys.argv[i])
        i += 1

    if len(argv) < 2:
        print_usage_and_exit()

    if port < 0 or not host:
        # if host and port have not been specified explicitly on the command
        # line, try to retrieve them from (temporary) config file or use
        # hard coded default values
        host, port = retrieve_host_and_port()

    if sys.argv[1] == "--status":
        try:
            result = asyncio_run(send_request(IDENTIFY_REQUEST, host, port))
            print('Server ' + str(result) + ' running on ' + host + ' ' + str(port))
        except ConnectionRefusedError:
            print('No server running on: ' + host + ' ' + str(port))

    elif argv[1] == "--startserver":
        log_path, _ = parse_logging_args(argv)
        if len(argv) == 2:
            argv.append(host)
        if len(argv) == 3:
            argv.append(str(port))
        sys.exit(run_server(argv[2], int(argv[3]), log_path))

    elif argv[1] == "--startdaemon":
        log_path, log_request = parse_logging_args(argv)
        if len(argv) == 2:
            argv.append(host)
        if len(argv) == 3:
            argv.append(str(port))
        start_server_daemon(host, port)
        if log_request:
            print(asyncio_run(send_request(log_request, host, port)))

    elif argv[1] in ("--stopserver", "--killserver", "--stopdaemon", "--killdaemon"):
        try:
            result = asyncio_run(send_request(STOP_SERVER_REQUEST, host, port))
        except ConnectionRefusedError as e:
            print(e)
            sys.exit(1)
        print(result)

    elif argv[1] == "--logging":
        log_path, request = parse_logging_args(argv)
        print(asyncio_run(send_request(request, host, port)))

    elif argv[1].startswith('-'):
        print_usage_and_exit()

    elif argv[1]:
        if not argv[1].endswith(')'):
            # argv does not seem to be a command (e.g. "identify()") but a file name or path
            argv[1] = os.path.abspath(argv[1])
            # print(argv[1])
        log_path, log_request = parse_logging_args(argv)
        try:
            if log_request:
                print(asyncio_run(send_request(log_request, host, port)))
            result = asyncio_run(send_request(argv[1], host, port))
        except ConnectionRefusedError:
            start_server_daemon(host, port)               # start server first
            if log_request:
                print(asyncio_run(send_request(log_request, host, port)))
            result = asyncio_run(send_request(argv[1], host, port))
        if len(result) >= DATA_RECEIVE_LIMIT:
            print(result, '...')
        else:
            print(result)
    else:
        print_usage_and_exit()
