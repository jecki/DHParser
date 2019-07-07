# server.py - an asynchronous tcp-server to compile sources with DHParser
#
# Copyright 2019  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.


"""
Module `server` contains an asynchronous tcp-server that receives compilation
requests, runs custom compilation functions in a multiprocessing.Pool.

This allows to start a DHParser-compilation environment just once and save the
startup time of DHParser for each subsequent compilation. In particular, with
a just-in-time-compiler like PyPy (https://pypy.org) setting up a
compilation-server is highly recommended, because jit-compilers typically
sacrifice startup-speed for running-speed.

It is up to the compilation function to either return the result of the
compilation in serialized form, or just save the compilation results on the
file system an merely return an success or failure message. Module `server`
does not define any of these message. This is completely up to the clients
of module `server`, i.e. the compilation-modules, to decide.

The communication, i.e. requests and responses, follows the json-rpc protocol:

    https://www.jsonrpc.org/specification

For JSON see:

    https://json.org/
"""

# TODO: Test with python 3.5

import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor, ProcessPoolExecutor, CancelledError
from concurrent.futures.process import BrokenProcessPool
from functools import wraps, partial
import json
from multiprocessing import Process, Manager, Queue, Value, Array
import sys
import time
from typing import Callable, Coroutine, Optional, Union, Dict, List, Tuple, Sequence, Set, Any, \
    cast

from DHParser.configuration import get_config_value, THREAD_LOCALS
from DHParser.syntaxtree import DHParser_JSONEncoder
from DHParser.log import create_log, append_log
from DHParser.toolkit import re
from DHParser.versionnumber import __version__


__all__ = ('RPC_Table',
           'RPC_Type',
           'JSON_Type',
           'SERVER_ERROR',
           'SERVER_OFFLINE',
           'SERVER_STARTING',
           'SERVER_ONLINE',
           'SERVER_TERMINATE',
           'USE_DEFAULT_HOST',
           'USE_DEFAULT_PORT',
           'STOP_SERVER_REQUEST',
           'IDENTIFY_REQUEST',
           'ALL_RPCs',
           'identify_server',
           'Server',
           'lsp_rpc',
           'LanguageServerProtocol',
           'create_language_server')


RPC_Table = Dict[str, Callable]
RPC_Type = Union[RPC_Table, List[Callable], Callable]
JSON_Type = Union[Dict, Sequence, str, int, None]

RE_IS_JSONRPC = rb'(?:.*?\n\n)?\s*(?:{\s*"jsonrpc")|(?:\[\s*{\s*"jsonrpc")'  # b'\s*(?:{|\[|"|\d|true|false|null)'
RE_GREP_URL = rb'GET ([^ \n]+) HTTP'
RE_FUNCTION_CALL = rb'\s*(\w+)\(([^)]*)\)$'

SERVER_ERROR = "COMPILER-SERVER-ERROR"

SERVER_OFFLINE = 0
SERVER_STARTING = 1
SERVER_ONLINE = 2
SERVER_TERMINATE = 3

HTTP_RESPONSE_HEADER = '''HTTP/1.1 200 OK
Date: {date}
Server: DHParser
Accept-Ranges: none
Content-Length: {length}
Connection: close
Content-Type: text/html; charset=utf-8
X-Pad: avoid browser bug

'''

JSONRPC_HEADER = '''Content-Length: {length}

'''

ONELINER_HTML = '''<!DOCTYPE html>
<html lang="en" xml:lang="en">
<head>
  <meta charset="UTF-8" />
</head>
<body>
<h1>{line}</h1>
</body>
</html>

'''

UNKNOWN_FUNC_HTML = ONELINER_HTML.format(
    line="DHParser Error: Function {func} unknown or not registered!")

USE_DEFAULT_HOST = ''
USE_DEFAULT_PORT = -1

STOP_SERVER_REQUEST = b"__STOP_SERVER__"
IDENTIFY_REQUEST = "identify()"


def identify_server():
    return "DHParser " + __version__


def as_json_rpc(func: Callable,
                params: Union[List[JSON_Type], Dict[str, JSON_Type]]=(),
                ID: Optional[int]=None) -> str:
    """Generates a JSON-RPC-call for `func` with parameters `params`"""
    return json.dumps({"jsonrpc": "2.0", "method": func.__name__, "params": params, "id": ID})


def maybe_int(s: str) -> Union[int, str]:
    """Convert string to int if possible, otherwise return string."""
    try:
        return int(s)
    except ValueError:
        return s


def asyncio_run(coroutine: Coroutine, loop=None) -> Any:
    """Backward compatible version of Pyhon 3.7's `asyncio.run()`"""
    if sys.version_info >= (3, 7):
        return asyncio.run(coroutine)
    else:
        if loop is None:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
        else:
            myloop = loop
        try:
            result = loop.run_until_complete(coroutine)
        except ConnectionResetError:
            result = None
        return result


def GMT_timestamp() -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())


ALL_RPCs = frozenset('*')  # Magic value denoting all remote procedures


def default_fallback(*args, **kwargs) -> str:
    return 'No default RPC-function defined!'


class Server:
    def __init__(self, rpc_functions: RPC_Type,
                 cpu_bound: Set[str] = ALL_RPCs,
                 blocking: Set[str] = frozenset()):
        if isinstance(rpc_functions, Dict):
            self.rpc_table = cast(RPC_Table, rpc_functions)  # type: RPC_Table
            if 'default' not in self.rpc_table:
                self.rpc_table['default'] = default_fallback
            self.default = 'default'
        elif isinstance(rpc_functions, List):
            self.rpc_table = {}
            func_list = cast(List, rpc_functions)
            assert len(func_list) >= 1
            for func in func_list:
                self.rpc_table[func.__name__] = func
            self.default = func_list[0].__name__
        else:
            assert isinstance(rpc_functions, Callable)
            func = cast(Callable, rpc_functions)
            self.rpc_table = {func.__name__: func}
            self.default = func.__name__
        assert STOP_SERVER_REQUEST.decode() not in self.rpc_table
        if IDENTIFY_REQUEST.strip('()') not in self.rpc_table:
            self.rpc_table[IDENTIFY_REQUEST.strip('()')] = identify_server

        # see: https://docs.python.org/3/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools
        self.cpu_bound = frozenset(self.rpc_table.keys()) if cpu_bound == ALL_RPCs else cpu_bound
        self.blocking = frozenset(self.rpc_table.keys()) if blocking == ALL_RPCs else blocking
        self.blocking = self.blocking - self.cpu_bound  # cpu_bound property takes precedence

        assert not (self.cpu_bound - self.rpc_table.keys())
        assert not (self.blocking - self.rpc_table.keys())

        self.max_source_size = get_config_value('max_rpc_size')  #type: int
        self.server_messages = Queue()  # type: Queue
        self.server_process = None  # type: Optional[Process]

        # shared variables
        self.stage = Value('b', SERVER_OFFLINE)  # type: Value
        self.host = Array('c', b' ' * 1024)      # type: Array
        self.port = Value('H', 0)                # type: Value

        # if the server is run in a separate process, the following variables
        # should only be accessed from the server process
        self.server = None        # type: Optional[asyncio.AbstractServer]
        self.stop_response = ''   # type: str
        self.pp_executor = None   # type: Optional[ProcessPoolExecutor]
        self.tp_executor = None   # type: Optional[ThreadPoolExecutor]

        if get_config_value('log_server'):
            self.log_file = create_log('%s_%s.log' % (self.__class__.__name__, hex(id(self))[2:])) # type: str
        else:
            self.log_file = ''
        self.echo_log = get_config_value('echo_server_log')
        self.use_jsonrpc_header = get_config_value('jsonrpc_header')

        self.loop = None  # just for python 3.5 compatibility...

    async def handle_request(self,
                             reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter):
        rpc_error = None    # type: Optional[Tuple[int, str]]
        json_id = None      # type: Optional[int]
        obj = {}            # type: Dict
        result = None       # type: JSON_Type
        raw = None          # type: JSON_Type
        kill_switch = False # type: bool

        data = await reader.read(self.max_source_size + 1)
        oversized = len(data) > self.max_source_size

        def http_response(html: str) -> bytes:
            gmt = GMT_timestamp()
            if isinstance(html, str):
                encoded_html = html.encode()
            else:
                encoded_html = "Illegal type %s for response %s. Only str allowed!" \
                               % (str(type(html)), str(html))
            response = HTTP_RESPONSE_HEADER.format(date=gmt, length=len(encoded_html))
            return response.encode() + encoded_html

        async def execute(executor: Executor, method: Callable, params: Union[Dict, Sequence]):
            nonlocal result, rpc_error
            has_kw_params = isinstance(params, Dict)
            if not (has_kw_params or isinstance(params, Sequence)):
                rpc_error = -32040, "Invalid parameter type %s for %s. Must be Dict or Sequence" \
                            % (str(type(params)), str(params))
                return
            loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            try:
                # print(executor, method, params)
                if executor is None:
                    result = method(**params) if has_kw_params else method(*params)
                elif has_kw_params:
                    result = await loop.run_in_executor(executor, partial(method, **params))
                else:
                    result = await loop.run_in_executor(executor, partial(method, *params))
            except TypeError as e:
                rpc_error = -32602, "Invalid Params: " + str(e)
            except NameError as e:
                rpc_error = -32601, "Method not found: " + str(e)
            except BrokenProcessPool as e:
                rpc_error = -32050, "Broken Executor: " + str(e)
            except Exception as e:
                rpc_error = -32000, "Server Error " + str(type(e)) + ': ' + str(e)

        async def run(method_name: str, method: Callable, params: Union[Dict, Sequence]):
            # run method either a) directly if it is short running or
            # b) in a thread pool if it contains blocking io or
            # c) in a process pool if it is cpu bound
            # see: https://docs.python.org/3/library/asyncio-eventloop.html
            #      #executing-code-in-thread-or-process-pools
            executor = self.pp_executor if method_name in self.cpu_bound else \
                self.tp_executor if method_name in self.blocking else None
            await execute(executor, method, params)
            if rpc_error is not None and rpc_error[0] == -32050:
                # if process pool is broken, try again:
                self.pp_executor.shutdown(wait=True)
                self.pp_executor = ProcessPoolExecutor()
                await execute(self.pp_executor, method, params)

        def respond(response: Union[str, bytes]):
            nonlocal writer, json_id
            if isinstance(response, str):
                response = response.encode()
            elif not isinstance(response, bytes):
                response = ('Illegal response type %s of reponse object %s. '
                            'Only bytes and str allowed!'
                            % (str(type(response)), str(response))).encode()
            if self.use_jsonrpc_header:
                response = JSONRPC_HEADER.format(length=len(response)).encode() + response
            append_log(self.log_file, 'RESPONSE: ', response.decode(), '\n\n', echo=self.echo_log)
            writer.write(response)

        append_log(self.log_file, 'RECEIVE: ', data.decode(), '\n', echo=self.echo_log)

        if data.startswith(b'GET'):
            # HTTP request
            m = re.match(RE_GREP_URL, data)
            # m = RX_GREP_URL(data.decode())
            if m:
                func_name, argument = m.group(1).decode().strip('/').split('/', 1) + [None]
                if func_name.encode() == STOP_SERVER_REQUEST:
                    respond(http_response(ONELINER_HTML.format(line=self.stop_response)))
                    kill_switch = True
                else:
                    func = self.rpc_table.get(func_name,
                                              lambda _: UNKNOWN_FUNC_HTML.format(func=func_name))
                    # result = func(argument) if argument is not None else func()
                    await run(func.__name__, func, (argument,) if argument else ())
                    if rpc_error is None:
                        if isinstance(result, str):
                            respond(http_response(result))
                        else:
                            try:
                                respond(http_response(
                                    json.dumps(result, indent=2, cls=DHParser_JSONEncoder)))
                            except TypeError as err:
                                respond(http_response(str(err)))
                    else:
                        respond(http_response(rpc_error[1]))

        elif not data.find(b'"jsonrpc"') >= 0:  # re.match(RE_IS_JSONRPC, data):
            # plain data
            if oversized:
                respond("Source code too large! Only %i MB allowed"
                             % (self.max_source_size // (1024 ** 2)))
            elif data.startswith(STOP_SERVER_REQUEST):
                respond(self.stop_response)
                kill_switch = True
            else:
                m = re.match(RE_FUNCTION_CALL, data)
                if m:
                    func_name = m.group(1).decode()
                    argstr = m.group(2).decode()
                    if argstr:
                        argument = tuple(maybe_int(s.strip('" \'')) for s in argstr.split(','))
                    else:
                        argument = ()
                else:
                    func_name = self.default
                    argument = (data.decode(),)
                err_func = lambda arg: 'Function %s no found!' % func_name
                func = self.rpc_table.get(func_name, err_func)
                await run(func_name, func, argument)
                if rpc_error is None:
                    if isinstance(result, str):
                        respond(result)
                    elif result is not None:
                        try:
                            respond(json.dumps(result, cls=DHParser_JSONEncoder))
                        except TypeError as err:
                            respond(str(err))
                else:
                    respond(rpc_error[1])

        else:
            # TODO: add batch processing capability! (put calls to execute in asyncio tasks, use asyncio.gather)
            i = data.find(b'"jsonrpc"') - 1
            # see: https://microsoft.github.io/language-server-protocol/specification#header-part
            # i = max(data.find(b'\n\n'), data.find(b'\r\n\r\n')) + 2
            while i > 0 and data[i] in (b'{', b'['):
                i -= 1
            data = data[i:]
            if oversized:
                rpc_error = -32600, "Invaild Request: Source code too large! Only %i MB allowed" \
                            % (self.max_source_size // (1024 ** 2))

            if rpc_error is None:
                try:
                    raw = json.loads(data.decode())
                except json.decoder.JSONDecodeError as e:
                    rpc_error = -32700, "JSONDecodeError: " + str(e) + str(data)

            if rpc_error is None:
                if isinstance(raw, Dict):
                    obj = cast(Dict, raw)
                    json_id = obj.get('id', None)
                else:
                    rpc_error = -32700, 'Parse error: Request does not appear to be an RPC-call!?'

            if rpc_error is None:
                if obj.get('jsonrpc', '0.0') < '2.0':
                    rpc_error = -32600, 'Invalid Request: jsonrpc version 2.0 needed, version "' \
                                        ' "%s" found.' % obj.get('jsonrpc', b'unknown')
                elif 'method' not in obj:
                    rpc_error = -32600, 'Invalid Request: No method specified.'
                elif obj['method'] == STOP_SERVER_REQUEST.decode():
                    result = self.stop_response
                    kill_switch = True
                elif obj['method'] not in self.rpc_table:
                    rpc_error = -32601, 'Method not found: ' + str(obj['method'])
                else:
                    method_name = obj['method']
                    method = self.rpc_table[method_name]
                    params = obj['params'] if 'params' in obj else ()
                    await run(method_name, method, params)

            try:
                try:
                    error = cast(Dict[str, str], result['error'])
                except KeyError:
                    error = cast(Dict[str, str], result)
                rpc_error = int(error['code']), error['message']
            except TypeError:
                pass  # result is not a dictionary, never mind
            except KeyError:
                pass  # no errors in result

            if rpc_error is None:
                if json_id is not None:
                    try:
                        json_result = {"jsonrpc": "2.0", "result": result, "id": json_id}
                        respond(json.dumps(json_result, cls=DHParser_JSONEncoder))
                    except TypeError as err:
                        rpc_error = -32070, str(err)

            if rpc_error is not None:
                respond(('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}'
                              % (rpc_error[0], rpc_error[1], json_id)))
        await writer.drain()
        if kill_switch:
            # TODO: terminate processes and threads! Is this needed??
            self.stage.value = SERVER_TERMINATE
            self.server.close()
            if self.loop is not None:
                self.loop.stop()

    async def serve(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT):
        if host == USE_DEFAULT_HOST:
            host = get_config_value('server_default_host')
        if port == USE_DEFAULT_PORT:
            port = get_config_value('server_default_port')
        assert port >= 0
        # with ProcessPoolExecutor() as p, ThreadPoolExecutor() as t:
        try:
            if self.pp_executor is None:
                self.pp_executor = ProcessPoolExecutor()
            if self.tp_executor is None:
                self.tp_executor = ThreadPoolExecutor()
            self.stop_response = "DHParser server at {}:{} stopped!".format(host, port)
            self.host.value = host.encode()
            self.port.value = port
            self.server = cast(asyncio.base_events.Server,
                               await asyncio.start_server(self.handle_request, host, port))
            async with self.server:
                self.stage.value = SERVER_ONLINE
                self.server_messages.put(SERVER_ONLINE)
                await self.server.serve_forever()
        finally:
            if self.tp_executor is not None:
                self.tp_executor.shutdown(wait=True)
                self.tp_executor = None
            if self.pp_executor is not None:
                self.pp_executor.shutdown(wait=True)
                self.pp_executor = None

    def serve_py35(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT, loop=None):
        if host == USE_DEFAULT_HOST:
            host = get_config_value('server_default_host')
        if port == USE_DEFAULT_PORT:
            port = get_config_value('server_default_port')
        assert port >= 0
        with ProcessPoolExecutor() as p, ThreadPoolExecutor() as t:
            self.pp_executor = p
            self.tp_executor = t
            self.stop_response = "DHParser server at {}:{} stopped!".format(host, port)
            self.host.value = host.encode()
            self.port.value = port
            if loop is None:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            else:
                self.loop = loop
            self.server = cast(
                asyncio.base_events.Server,
                self.loop.run_until_complete(
                    asyncio.start_server(self.handle_request, host, port, loop=self.loop)))
            try:
                self.stage.value = SERVER_ONLINE
                self.server_messages.put(SERVER_ONLINE)
                self.loop.run_forever()
            finally:
                if loop is None:
                    asyncio.set_event_loop(None)
                    self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                    self.loop.close()
                self.server.close()
                asyncio_run(self.server.wait_closed())

    def _empty_message_queue(self):
        while not self.server_messages.empty():
            self.server_messages.get()

    def run_server(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT, loop=None):
        """
        Starts a DHParser-Server. This function will not return until the
        DHParser-Server ist stopped by sending a STOP_SERVER_REQUEST.
        """
        assert self.stage.value == SERVER_OFFLINE
        self.stage.value = SERVER_STARTING
        self._empty_message_queue()
        if self.echo_log:
            print("Server logging is on.")
        try:
            if sys.version_info >= (3, 7):
                asyncio.run(self.serve(host, port))
            else:
                self.serve_py35(host, port, loop)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        except CancelledError:
            pass
        self.pp_executor = None
        self.tt_exectuor = None
        asyncio_run(self.server.wait_closed())
        self.server_messages.put(SERVER_OFFLINE)
        self.stage.value = SERVER_OFFLINE

    def wait_until_server_online(self):
        if self.stage.value != SERVER_ONLINE:
            message = self.server_messages.get()
            if message != SERVER_ONLINE:
                raise AssertionError('could not start server!?')
            assert self.stage.value == SERVER_ONLINE

    def spawn_server(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT):
        """
        Start DHParser-Server in a separate process and return.
        """
        if self.server_process:
            assert not self.server_process.is_alive()
            if sys.version_info >= (3, 7):
                self.server_process.close()
            self.server_process = None
        self._empty_message_queue()
        self.server_process = Process(
            target=self.run_server, args=(host, port), name="DHParser-Server")
        self.server_process.start()
        self.wait_until_server_online()

    async def termination_request(self):
        try:
            host, port = self.host.value.decode(), self.port.value
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(STOP_SERVER_REQUEST)
            await reader.read(500)
            while self.stage.value != SERVER_OFFLINE \
                    and self.server_messages.get() != SERVER_OFFLINE:
                pass
            writer.close()
        except ConnectionRefusedError:
            pass

    def terminate_server(self):
        """
        Terminates the server process.
        """
        try:
            if self.stage.value in (SERVER_STARTING, SERVER_ONLINE):
                asyncio_run(self.termination_request())
            if self.server_process and self.server_process.is_alive():
                if self.stage.value in (SERVER_STARTING, SERVER_ONLINE):
                    self.stage.value = SERVER_TERMINATE
                    self.server_process.terminate()
                self.server_process.join()
                if sys.version_info >= (3, 7):
                    self.server_process.close()
                self.server_process = None
                self.stage.value = SERVER_OFFLINE
        except AssertionError as debugger_err:
            print('If this message appears out of debugging mode, it is an error!')

    def wait_for_termination(self):
        """
        Waits for the termination of the server-process. Termination of the
        server-process can be triggered by sending a STOP_SERVER_REQUEST to the
        server.
        """
        if self.stage.value in (SERVER_STARTING, SERVER_ONLINE, SERVER_TERMINATE):
            while self.server_messages.get() != SERVER_OFFLINE:
                pass
        self.terminate_server()


#######################################################################
#
# Language-Server base class
#
#######################################################################


def lsp_rpc(f: Callable):
    """A decorator for LanguageServerProtocol-methods. This wrapper
    filters out calls that are made before initializing the server and
    after shutdown and returns an error message instead.
    This decorator should only be used on methods of
    LanguageServerProtocol-objects as it expects the first parameter
    to be a the `self`-reference of this object.
    All LSP-methods should be decorated with this decorator except
    initialize and exit
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            self = args[0]
        except IndexError:
            self = kwargs['self']
        assert isinstance(self, LanguageServerProtocol)
        if self.server_shutdown:
            return {'code': -32600, 'message': 'server already shut down'}
        elif not self.server_initialized and f.__name__ != 'rpc_initialize':
            return {'code': -32002, 'message': 'initialize-request must be send first'}
        else:
            return f(*args, **kwargs)
    return wrapper


class LanguageServerProtocol:
    """Template for the implementation of the language server protocol.
    See: https://microsoft.github.io/language-server-protocol/

    Usage:
        class MyLSP(LanguageServerProtocoll):
            # Implement your LSP-methods, here

        language_server = create_language_server(MyLSP())
    """

    cpu_bound = ALL_RPCs    # type: Set[str]
    blocking = frozenset()  # type: Set[str]

    def __init__(self, capabilities: Dict[str, bool] = {}, additional_rpcs: Dict[str, Callable] = {}):
        self.rpc_table = dict()  # type: RPC_Table
        for attr in dir(self):
            if attr.startswith('rpc_'):
                name = attr[4:].replace('_', '/').replace('S/', '$/')
                func = getattr(self, attr)
                self.rpc_table[name] = func
        self.rpc_table.update(additional_rpcs)
        self.server_initialized = False  # type: bool
        self.server_shutdown = False  # type: bool
        self.client_initialized = False  # type: bool

        self.processId = 0  # type: int
        self.rootUri = ''  # type: str
        self.serverCapabilities = capabilities  # type: Dict[str, bool]
        self.clientCapabilities = {}  # type: Dict[str, bool]

        self.server_object = None  # type: Server

    def initialize(self, **kw):
        self.processId = kw['processId']
        self.rootUri = kw['rootUri']
        self.clientCapabilities = kw['capabilities']
        return {'capabilities': self.serverCapabilities}

    def rpc_default(self, arg):
        return '"%s" is no valid JSON-RPC! See: https://www.jsonrpc.org/specification' % arg

    def rpc_initialize(self, **kwargs):
        if self.server_initialized:
            return {"code": -32002, "message": "Server has already been initialized."}
        else:
            result = self.initialize(**kwargs)
            if 'error' not in result:
                self.server_initialized = True
            return result

    def rpc_initialized(self):
        if self.client_initialized:
            pass  # clients must not reply to notifations!
            # print('double notification!')
            # return {"jsonrpc": "2.0",
            #         "error": {"code": -322002,
            #         "message": "Initialize Notification already received!"},
            #         "id": 0}
        else:
            self.client_initialized = True
        return None

    @lsp_rpc
    def rpc_shutdown(self, *args, **kwargs):
        return None

    def rpc_exit(self, *args, **kwargs):
        self.server_object.terminate_server()
        return None


def create_language_server(lsp: LanguageServerProtocol) -> Server:
    """Creates a Language Server for the given Language Server Protocol-object."""
    server = Server(lsp.rpc_table, lsp.cpu_bound, lsp.blocking)
    lsp.server_object = server
    return server

