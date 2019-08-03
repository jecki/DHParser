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
from functools import partial
import json
from multiprocessing import Process, Queue, Value, Array
import platform
import os
import subprocess
import sys
import time
from typing import Callable, Coroutine, Optional, Union, Dict, List, Tuple, Sequence, Set, \
    Iterator, Any, cast

from DHParser.configuration import access_thread_locals, get_config_value
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
           'asyncio_run',
           'asyncio_connect',
           'Server',
           'spawn_server',
           'stop_server',
           'has_server_stopped',
           'gen_lsp_table')


RPC_Table = Dict[str, Callable]
RPC_Type = Union[RPC_Table, List[Callable], Callable]
RPC_Error_Type = Optional[Tuple[int, str]]
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

JSONRPC_HEADER = '''Content-Length: {length}\r\n\r\n'''

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
STOP_SERVER_REQUEST_STR = STOP_SERVER_REQUEST.decode()
IDENTIFY_REQUEST = "identify()"


def substitute_default_host_and_port(host, port):
    """Substiutes the default value(s) from the configuration file if host
     or port ist ``USE_DEFAULT_HOST`` or ``USE_DEFAULT_PORT``. """
    if host == USE_DEFAULT_HOST:
        host = get_config_value('server_default_host')
    if port == USE_DEFAULT_PORT:
        port = get_config_value('server_default_port')
    return host, port


def identify_server():
    """Returns an identification string for the server."""
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
    """Backward compatible version of Pyhon3.7's `asyncio.run()`"""
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


async def asyncio_connect(host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT,
                    retry_timeout: float = 1.0):
    """
    Backwards compatible version of Python3.8's `asyncio.connect()`, with the
    variant that it returns a reader, writer pair instead of just one stream.
    From Python 3.8 onward, the returned reader and writer are one and the
    same stream, however.
    """
    host, port = substitute_default_host_and_port(host, port)
    delay = retry_timeout / 2**7  if retry_timeout > 0.0 else retry_timeout - 0.001
    connected = False
    reader, writer = None, None
    while delay < retry_timeout:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            delay = retry_timeout
            connected = True
        except ConnectionRefusedError as error:
            save_error = error
            if delay > 0.0:
                time.sleep(delay)
                delay *= 2
            else:
                delay = retry_timeout  # exit while loop
    if connected:
        return reader, writer
    else:
        raise save_error


def GMT_timestamp() -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())


ALL_RPCs = frozenset('*')  # Magic value denoting all remote procedures


def default_fallback(*args, **kwargs) -> str:
    return 'No default RPC-function defined!'


def http_response(html: str) -> bytes:
    """
    Embeds an html-string in a http header and returns the http-package
    as byte-string.
    """
    gmt = GMT_timestamp()
    if isinstance(html, str):
        encoded_html = html.encode()
    else:
        encoded_html = "Illegal type %s for response %s. Only str allowed!" \
                       % (str(type(html)), str(html))
    response = HTTP_RESPONSE_HEADER.format(date=gmt, length=len(encoded_html))
    return response.encode() + encoded_html


def gen_task_id() -> int:
    """Generate a unique task id. This is always a negative number to
    distinguish the taks id's from the json-rpc ids."""
    THREAD_LOCALS = access_thread_locals()
    try:
        value = THREAD_LOCALS.DHParser_server_task_id
        THREAD_LOCALS.DHParser_server_task_id = value - 1
    except AttributeError:
        THREAD_LOCALS.DHParser_server_task_id = -2
        value = -1
    assert value < 0
    return value


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
        assert STOP_SERVER_REQUEST_STR not in self.rpc_table
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
        self.host = Array('c', b' ' * 2048)      # type: Array
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

        self.active_tasks = {}        # type: Dict[int, asyncio.Future]
        self.kill_switch = False      # type: bool
        self.exit_connection = False  # type: bool
        self.loop = None  # just for python 3.5 compatibility...

    async def execute(self, executor: Optional[Executor],
                      method: Callable,
                      params: Union[Dict, Sequence])\
            -> Tuple[JSON_Type, RPC_Error_Type]:
        """Executes a method with the given parameters in a given executor
        (ThreadPoolExcecutor or ProcessPoolExecutor). `execute()`waits for the
        completion and returns the JSON result and an RPC error tuple (see the
        type definition above). The result may be None and the error may be
        zero, i.e. no error. If `executor` is `None`the method will be called
        directly instead of deferring it to an executor."""
        result = None      # type: JSON_Type
        rpc_error = None   # type: RPC_Error_Type
        has_kw_params = isinstance(params, Dict)
        if not (has_kw_params or isinstance(params, Sequence)):
            rpc_error = -32040, "Invalid parameter type %s for %s. Must be Dict or Sequence" \
                        % (str(type(params)), str(params))
            return result, rpc_error
        try:
            # print(executor, method, params)
            if executor is None:
                result = method(**params) if has_kw_params else method(*params)
            elif has_kw_params:
                result = await self.loop.run_in_executor(executor, partial(method, **params))
            else:
                result = await self.loop.run_in_executor(executor, partial(method, *params))
        except TypeError as e:
            rpc_error = -32602, "Invalid Params: " + str(e)
        except NameError as e:
            rpc_error = -32601, "Method not found: " + str(e)
        except BrokenProcessPool as e:
            rpc_error = -32050, "Broken Executor: " + str(e)
        except Exception as e:
            rpc_error = -32000, "Server Error " + str(type(e)) + ': ' + str(e)
        return result, rpc_error

    async def run(self, method_name: str, method: Callable, params: Union[Dict, Sequence]) \
            -> Tuple[JSON_Type, RPC_Error_Type]:
        """Picks the right execution method (process, thread or direct execution) and
        runs it in the respective executor. In case of a broken ProcessPoolExecutor it
        restarts the ProcessPoolExecutor and tries to execute the method again."""
        # run method either a) directly if it is short running or
        # b) in a thread pool if it contains blocking io or
        # c) in a process pool if it is cpu bound
        # see: https://docs.python.org/3/library/asyncio-eventloop.html
        #      #executing-code-in-thread-or-process-pools
        result, rpc_error = None, None
        executor = self.pp_executor if method_name in self.cpu_bound else \
            self.tp_executor if method_name in self.blocking else None
        result, rpc_error = await self.execute(executor, method, params)
        if rpc_error is not None and rpc_error[0] == -32050:
            # if process pool is broken, try again:
            self.pp_executor.shutdown(wait=True)
            self.pp_executor = ProcessPoolExecutor()
            result, rpc_error = await self.execute(self.pp_executor, method, params)
        return result, rpc_error

    def respond(self, writer: asyncio.StreamWriter, response: Union[str, bytes]):
        """Sends a response to the given writer. Depending on the configuration,
        the response will be logged. If the response appears to be a json-rpc
        response a JSONRPC_HEADER will be added depending on
        `self.use_jsonrpc_header`.
        """
        if isinstance(response, str):
            response = response.encode()
        elif not isinstance(response, bytes):
            response = ('Illegal response type %s of reponse object %s. '
                        'Only bytes and str allowed!'
                        % (str(type(response)), str(response))).encode()
        if self.use_jsonrpc_header and response.startswith(b'{'):
            response = JSONRPC_HEADER.format(length=len(response)).encode() + response
        append_log(self.log_file, 'RESPONSE: ', response.decode(), '\n\n', echo=self.echo_log)
        # print('returned: ', response)
        writer.write(response)

    async def handle_plaindata_request(self, task_id: int,
                                       reader: asyncio.StreamReader,
                                       writer: asyncio.StreamWriter,
                                       data: bytes):
        """Processes a request in plain-data-format, i.e. neither http nor json_rpc"""
        if len(data) > self.max_source_size:
            self.respond(writer, "Data too large! Only %i MB allowed"
                                 % (self.max_source_size // (1024 ** 2)))
            await writer.drain()
        elif data.startswith(STOP_SERVER_REQUEST):
            self.respond(writer, self.stop_response)
            await writer.drain()
            self.kill_switch = True
            reader.feed_eof()
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
            result, rpc_error = await self.run(func_name, func, argument)
            if rpc_error is None:
                if isinstance(result, str):
                    self.respond(writer, result)
                elif result is not None:
                    try:
                        self.respond(writer, json.dumps(result, cls=DHParser_JSONEncoder))
                    except TypeError as err:
                        self.respond(writer, str(err))
            else:
                self.respond(writer, rpc_error[1])
            if result is not None or rpc_error is not None:
                await writer.drain()
        try:
            del self.active_tasks[task_id]
        except KeyError:
            pass  # task might have been finished even before it has been registered

    async def handle_http_request(self, task_id: int,
                                  reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter,
                                  data: bytes):
        if len(data) > self.max_source_size:
            self.respond(writer, http_response("Data too large! Only %i MB allowed"
                                               % (self.max_source_size // (1024 ** 2))))
            await writer.drain()
        else:
            result, rpc_error = None, None
            m = re.match(RE_GREP_URL, data)
            # m = RX_GREP_URL(data.decode())
            if m:
                func_name, argument = m.group(1).decode().strip('/').split('/', 1) + [None]
                if func_name.encode() == STOP_SERVER_REQUEST:
                    self.respond(writer,
                                 http_response(ONELINER_HTML.format(line=self.stop_response)))
                    self.kill_switch = True
                    await writer.drain()
                    reader.feed_eof()
                else:
                    func = self.rpc_table.get(func_name,
                                              lambda _: UNKNOWN_FUNC_HTML.format(func=func_name))
                    # result = func(argument) if argument is not None else func()
                    result, rpc_error = await self.run(func.__name__, func,
                                                       (argument,) if argument else ())
                    if rpc_error is None:
                        if result is None:
                            result = ''
                        if isinstance(result, str):
                            self.respond(writer, http_response(result))
                        else:
                            try:
                                self.respond(writer, http_response(
                                    json.dumps(result, indent=2, cls=DHParser_JSONEncoder)))
                            except TypeError as err:
                                self.respond(writer, http_response(str(err)))
                    else:
                        self.respond(writer, http_response(rpc_error[1]))
            if result is not None or rpc_error is not None:
                await writer.drain()
        try:
            del self.active_tasks[task_id]
        except KeyError:
            pass  # task might have been finished even before it has been registered

    async def handle_jsonrpc_request(self, json_id: int,
                                     reader: asyncio.StreamReader,
                                     writer: asyncio.StreamWriter,
                                     json_obj: Dict):
        # TODO: handle cancellation calls!
        result, rpc_error = None, None
        if json_obj.get('jsonrpc', '0.0') < '2.0':
            rpc_error = -32600, 'Invalid Request: jsonrpc version 2.0 needed, version "' \
                                ' "%s" found.' % json_obj.get('jsonrpc', b'unknown')
        elif 'method' not in json_obj:
            rpc_error = -32600, 'Invalid Request: No method specified.'
        elif json_obj['method'] == STOP_SERVER_REQUEST_STR:
            result = self.stop_response
            self.kill_switch = True
            reader.feed_eof()
        elif json_obj['method'] not in self.rpc_table:
            rpc_error = -32601, 'Method not found: ' + str(json_obj['method'])
        else:
            method_name = json_obj['method']
            method = self.rpc_table[method_name]
            params = json_obj['params'] if 'params' in json_obj else ()
            result, rpc_error = await self.run(method_name, method, params)
            if method_name == 'exit':
                self.exit_connection = True
                reader.feed_eof()

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
            if json_id is not None and result is not None:
                try:
                    json_result = {"jsonrpc": "2.0", "result": result, "id": json_id}
                    self.respond(writer, json.dumps(json_result, cls=DHParser_JSONEncoder))
                except TypeError as err:
                    rpc_error = -32070, str(err)

        if rpc_error is not None:
            self.respond(writer, ('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}'
                                  % (rpc_error[0], rpc_error[1], json_id)))

        if result is not None or rpc_error is not None:
            await writer.drain()
        try:
            del self.active_tasks[json_id]
        except KeyError:
            pass  # task might have been finished even before it has been registered

    async def connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # print('BEGIN DHParser.server.connection()')
        while not self.exit_connection and not self.kill_switch:
            # print('waiting for data...', self.kill_switch)
            data = await reader.read(self.max_source_size + 1)   # type: bytes
            append_log(self.log_file, 'RECEIVE: ', data.decode(), '\n', echo=self.echo_log)
            # print('received: ', data.decode())
            if not data and reader.at_eof():
                break

            if data.startswith(b'GET'):
                # HTTP request
                task_id = gen_task_id()
                task = asyncio.ensure_future(self.handle_http_request(
                    task_id, reader, writer, data))
                assert task_id not in self.active_tasks, str(task_id)
                self.active_tasks[task_id] = task
            elif not data.find(b'"jsonrpc"') >= 0:  # re.match(RE_IS_JSONRPC, data):
                # plain data
                task_id = gen_task_id()
                task = asyncio.ensure_future(self.handle_plaindata_request(
                    task_id, reader, writer, data))
                assert task_id not in self.active_tasks, str(task_id)
                self.active_tasks[task_id] = task
            else:
                # assume json
                # TODO: add batch processing capability! (put calls to execute in asyncio tasks, use asyncio.gather)
                json_id = 0
                raw = None
                json_obj = {}
                rpc_error = None
                i = data.find(b'"jsonrpc"') - 1
                # see: https://microsoft.github.io/language-server-protocol/specification#header-part
                # i = max(data.find(b'\n\n'), data.find(b'\r\n\r\n')) + 2
                while i > 0 and data[i] in (b'{', b'['):
                    i -= 1
                if i > 0:
                    data = data[i:]
                if len(data) > self.max_source_size:
                    rpc_error = -32600, "Invaild Request: Source code too large! Only %i MB allowed" \
                                % (self.max_source_size // (1024 ** 2))

                if rpc_error is None:
                    try:
                        raw = json.loads(data.decode())
                    except json.decoder.JSONDecodeError as e:
                        rpc_error = -32700, "JSONDecodeError: " + str(e) + str(data)

                if rpc_error is None:
                    if isinstance(raw, Dict):
                        json_obj = cast(Dict, raw)
                        json_id = json_obj.get('id', None)
                    else:
                        rpc_error = -32700, 'Parse error: Request does not appear to be an RPC-call!?'

                if rpc_error is None:
                    task = asyncio.ensure_future(self.handle_jsonrpc_request(
                        json_id, reader, writer, json_obj))
                    assert json_id not in self.active_tasks, str(json_id)
                    self.active_tasks[json_id] = task
                else:
                    self.respond(writer,
                        ('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}'
                         % (rpc_error[0], rpc_error[1], json_id)))
                    await writer.drain()

        if self.exit_connection or self.kill_switch:
            writer.write_eof()
            await writer.drain()
            writer.close()
            self.exit_connection = False  # reset flag

        # print("ACTIVE TASKS: ", self.active_tasks)

        if self.kill_switch:
            # TODO: terminate processes and threads! Is this needed??
            self.stage.value = SERVER_TERMINATE
            self.server.close()
            if sys.version_info < (3, 7) and self.loop is not None:
                self.loop.stop()
            self.kill_switch = False  # reset flag
        # print('END DHParser.server.connection()')

    async def serve(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT):
        host, port = substitute_default_host_and_port(host, port)
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
            self.loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            self.server = cast(asyncio.base_events.Server,
                               await asyncio.start_server(self.connection, host, port))
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
                    asyncio.start_server(self.connection, host, port, loop=self.loop)))
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
                asyncio_run(self.serve(host, port))
            else:
                self.serve_py35(host, port, loop)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        except CancelledError:
            pass
        self.pp_executor = None
        self.tp_executor = None
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
        Useful for writing test code.
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
            writer.write_eof()
            await writer.drain()
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


RUN_SERVER_SCRIPT_TEMPLATE = """
import os
import sys

path = '.'
sys.path.append(os.path.abspath(path))
while not 'DHParser' in os.listdir(path) and len(path) < 20:
    path = os.path.join('..', path)
if len(path) < 20:
    sys.path.append(os.path.abspath(path))

{INITIALIZATION}

def run_server(host, port):
    from DHParser.server import asyncio_run, Server, stop_server, has_server_stopped
    stop_server(host, port)
    asyncio_run(has_server_stopped(host, port))
    server = Server({PARAMETERS})
    server.run_server(host, port)

if __name__ == '__main__':
    run_server('{HOST}', {PORT})
"""


def spawn_server(host: str = USE_DEFAULT_HOST,
                 port: int = USE_DEFAULT_PORT,
                 initialization: str = '',
                 parameters: str = 'lambda s: s'):
    """
    Start DHParser-Server in a separate process and return.
    Useful for writing test code.
    """
    host, port = substitute_default_host_and_port(host, port)
    null_device = " >/dev/null" if platform.system() != "Windows" else " > NUL"
    interpreter = 'python3' if os.system('python3 -V' + null_device) == 0 else 'python'
    run_server_script = RUN_SERVER_SCRIPT_TEMPLATE.format(
        HOST=host, PORT=port, INITIALIZATION=initialization, PARAMETERS=parameters)
    subprocess.Popen([interpreter, '-c', run_server_script])


def stop_server(host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT) \
        -> Optional[Exception]:
    """Sends a STOP_SERVER_REQUEST to a running server. Returns any exceptions
    that occurred."""
    async def send_stop_server(host: str, port: int) -> Optional[Exception]:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(STOP_SERVER_REQUEST)
            _ = await reader.read(1024)
            writer.write_eof()
            await writer.drain()
            writer.close()
            if sys.version_info >= (3, 7):
                await writer.wait_closed()
        except ConnectionRefusedError as error:
            return error
        except ConnectionResetError as error:
            return error
        return None

    host, port = substitute_default_host_and_port(host, port)
    return asyncio_run(send_stop_server(host, port))


async def has_server_stopped(host: str = USE_DEFAULT_HOST,
                             port: int = USE_DEFAULT_PORT,
                             timeout: float = 1.0) -> bool:
    """
    Returns True, if no server is running or any server that is running
    stops within the given timeout.
    """
    host, port = substitute_default_host_and_port(host, port)
    delay = timeout / 2**7  if timeout > 0.0 else timeout - 0.001
    try:
        while delay < timeout:
            _, writer = await asyncio_connect(host, port, retry_timeout=0.0)
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
            if delay > 0.0:
                time.sleep(delay)
                delay *= 2
            else:
                delay = timeout  # exit while loop
        return False
    except ConnectionRefusedError:
        return True

#######################################################################
#
# Language-Server-Protocol support
#
#######################################################################


def gen_lsp_table(lsp_funcs_or_instance: Union[Sequence[Callable], Iterator[Callable], Any],
                  prefix: str = '') -> RPC_Table:
    """Creates an RPC from a list of functions or from the methods
    of a class that implement the language server protocol.
    The dictionary keys are derived from the function name by replacing an
    underscore _ with a slash / and a single capital S with a $-sign.
    if `prefix` is not the empty string only functions or methods that start
    with `prefix` will be added to the table. The prefix will be removed
    before converting the functions' name to a dictionary key.

    >>> class LSP:
    ...     def lsp_initialize(self, **kw):
    ...         pass
    ...     def lsp_shutdown(self, **kw):
    ...         pass
    >>> lsp = LSP()
    >>> gen_lsp_table(lsp, 'lsp_').keys()
    dict_keys(['initialize', 'shutdown'])
    """
    rpc_table = {}
    if not isinstance(lsp_funcs_or_instance, Sequence) \
            and not isinstance(lsp_funcs_or_instance, Iterator):
        # assume lsp_funcs_or_instance is the instance of a class
        lsp_funcs = (getattr(lsp_funcs_or_instance, attr)
                     for attr in dir(lsp_funcs_or_instance) if not attr.startswith('__'))
    else:
        lsp_funcs = lsp_funcs_or_instance
    for func in lsp_funcs:
        name = func.__name__ if hasattr(func, '__name__') else ''
        if name and name.startswith(prefix):
            name = name[len(prefix):]
            name = name.replace('_', '/').replace('S/', '$/')
        rpc_table[name] = func
    return rpc_table



