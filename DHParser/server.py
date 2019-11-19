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

import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from functools import partial
import json
from multiprocessing import Process, Value, Array
import platform
import os
import subprocess
import sys
import time
from typing import Callable, Coroutine, Optional, Union, Dict, List, Tuple, Sequence, Set, \
    Iterator, Any, cast

from DHParser.configuration import access_thread_locals, get_config_value
from DHParser.syntaxtree import DHParser_JSONEncoder
from DHParser.log import create_log, append_log, is_logging, log_dir
from DHParser.toolkit import re, re_find
from DHParser.versionnumber import __version__


__all__ = ('RPC_Table',
           'RPC_Type',
           'JSON_Type',
           'SERVER_ERROR',
           'SERVER_OFFLINE',
           'SERVER_STARTING',
           'SERVER_ONLINE',
           'SERVER_TERMINATING',
           'USE_DEFAULT_HOST',
           'USE_DEFAULT_PORT',
           'STOP_SERVER_REQUEST',
           'IDENTIFY_REQUEST',
           'LOGGING_REQUEST',
           'ALL_RPCs',
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
RX_CONTENT_LENGTH = re.compile(rb'Content-Length:\s*(\d+)')
RE_DATA_START = rb'\r?\n\r?\n'

SERVER_ERROR = "COMPILER-SERVER-ERROR"

SERVER_OFFLINE = 0
SERVER_STARTING = 1
SERVER_ONLINE = 2
SERVER_TERMINATING = 3

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
LOGGING_REQUEST = 'logging("")'



def substitute_default_host_and_port(host, port):
    """Substiutes the default value(s) from the configuration file if host
     or port ist ``USE_DEFAULT_HOST`` or ``USE_DEFAULT_PORT``. """
    if host == USE_DEFAULT_HOST:
        host = get_config_value('server_default_host')
    if port == USE_DEFAULT_PORT:
        port = get_config_value('server_default_port')
    return host, port


def as_json_rpc(func: Callable,
                params: Union[List[JSON_Type], Dict[str, JSON_Type]]=(),
                ID: Optional[int]=None) -> str:
    """Generates a JSON-RPC-call for `func` with parameters `params`"""
    return json.dumps({"jsonrpc": "2.0", "method": func.__name__, "params": params, "id": ID})


def convert_argstr(s: str) -> Union[None, bool, int, str,  List, Dict]:
    """Convert string to suitable argument type"""
    s = s.strip()
    if s in ('None', 'null'):
        return None
    elif s in ('True', 'true'):
        return True
    elif s in ('False', 'false'):
        return False
    try:
        return int(s)
    except ValueError:
        if s.startswith('"') or s.startswith("'"):
            return s.strip('" \'')
        else:
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return s


def asyncio_run(coroutine: Coroutine, loop=None) -> Any:
    """Backward compatible version of Pyhon3.7's `asyncio.run()`"""
    if sys.version_info >= (3, 7):
        return asyncio.run(coroutine)
    else:
        if loop is None:
            try:
                loop = asyncio.get_event_loop()
                myloop = loop
            except RuntimeError:
                myloop = asyncio.new_event_loop()
                asyncio.set_event_loop(myloop)
        else:
            myloop = loop
        try:
            return myloop.run_until_complete(coroutine)
        finally:
            if loop is None:
                try:
                    myloop.run_until_complete(loop.shutdown_asyncgens())
                finally:
                    asyncio.set_event_loop(None)
                    myloop.close()


async def asyncio_connect(host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT,
                    retry_timeout: float = 3.0) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Opens a connection with timeout retry-timeout."""
    host, port = substitute_default_host_and_port(host, port)
    delay = retry_timeout / 1.5**12 if retry_timeout > 0.0 else retry_timeout - 0.001
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
                delay *= 1.5
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
    """

    Attributes:
        server_name: A name for the server. Defaults to 'CLASSNAME_OBJECTID'
        cpu_bound:  Set of function names of functions that are cpu-bound and
                will be run in separate processes
        blocking:   Set of functions that contain blocking calls (e.g. IO-calls)
                and will therefore be run in separate threads.
        max_data_size:  Maximal size of a data chunk that can be read by the
                server at a time.
        stage:  The operation stage, the server is in. Can be on of the four values:
                SERVER_OFFLINE, SERVER_STARTING, SERVER_ONLINE, SERVER_TERMINATING
        host:   The host, the server runs on, e.g. "127.0.0.1"
        port:   The port of the server, e.g. 8888
        server: The asyncio.Server if the server is online, or `None`.
        serving_task:  The task in which the asyncio.Server is run.
        stop_response:  The response string that is written to the stream as
                answer to a stop request.
        pp_executor:  A process-pool-executor for cpu-bound tasks
        tp_executor:  A thread-pool-executor for blocking tasks
        echo_log:   Read from the global configuration. If True, any log message
                will also be echoed on the console.
        use_jsonrpc_header:  Read from the global configuration. If True, jsonrpc
                calls or responses will always be preceeded by a simple header of
                the form: "Content-Length: {NUM}\n\n", where "{NUM}" stands for
                the byte-size of the rpc-package.
        active_tasks: A dictionary that maps the connection's id (i.e. the id of
                its stream writer) to a mapping of task id's (resp. jsonrpc id's)
                to their tasks to keep track of  any running task.
        finished_tasks: A dictionary that maps the connection's id (i.e. the id
                of its stream writer) to a set of task id's (resp. jsonrpc id's)
        connections:  A set of connection id's (i.e. id's of stream writer
                objects) that are currently active. If an id is removed from
                this set, the connection will be closed as soon as possible.
        kill_switch:  If True the, the server will be shut down.
        loop:  The asyncio event loop within which the asyncio stream server is
                run. This is only needed for Python 3.5 compatibility. If run
                with a python version from 3.6 onwards, higher level asyncio
                functions will be used.

    """
    def __init__(self, rpc_functions: RPC_Type,
                 cpu_bound: Set[str] = ALL_RPCs,
                 blocking: Set[str] = frozenset(),
                 server_name: str = ''):
        self.server_name = server_name or '%s_%s' % (self.__class__.__name__, hex(id(self))[2:])
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

        # see: https://docs.python.org/3/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools
        self.cpu_bound = frozenset(self.rpc_table.keys()) if cpu_bound == ALL_RPCs else cpu_bound
        self.blocking = frozenset(self.rpc_table.keys()) if blocking == ALL_RPCs else blocking
        self.blocking = self.blocking - self.cpu_bound  # cpu_bound property takes precedence

        assert not (self.cpu_bound - self.rpc_table.keys())
        assert not (self.blocking - self.rpc_table.keys())

        identify_name = IDENTIFY_REQUEST[:IDENTIFY_REQUEST.find('(')]
        if identify_name not in self.rpc_table:
            self.rpc_table[identify_name] = self.rpc_identify_server
        logging_name = LOGGING_REQUEST[:LOGGING_REQUEST.find('(')]
        if logging_name not in self.rpc_table:
            self.rpc_table[logging_name] = self.rpc_logging

        self.max_data_size = get_config_value('max_rpc_size')  #type: int
        # self.server_messages = Queue()  # type: Queue

        # shared variables
        self.stage = Value('b', SERVER_OFFLINE)  # type: Value
        self.host = Array('c', b' ' * 2048)      # type: Array
        self.port = Value('H', 0)                # type: Value

        # if the server is run in a separate process, the following variables
        # should only be accessed from the server process
        self.server = None        # type: Optional[asyncio.AbstractServer]
        self.serving_task = None  # type: Optional[asyncio.Task]
        self.stop_response = ''   # type: str
        self.pp_executor = None   # type: Optional[ProcessPoolExecutor]
        self.tp_executor = None   # type: Optional[ThreadPoolExecutor]

        self.echo_log = get_config_value('echo_server_log')  # type: bool
        self.use_jsonrpc_header = get_config_value('jsonrpc_header')  # type: bool

        self.log_file = ''              # type: str
        if get_config_value('log_server'):
            self.start_logging()

        self.active_tasks = dict()      # type: Dict[int, Dict[int, asyncio.Future]]
        self.finished_tasks = dict()    # type: Dict[int, Set[int]]
        self.connections = set()        # type: Set
        self.kill_switch = False        # type: bool
        self.loop = None  # just for python 3.5 compatibility...

    def start_logging(self, filename: str = "") -> str:
        if not filename:
            filename = self.server_name + '.log'
        if not log_dir():
            filename = os.path.join('.', filename)
        self.log_file = create_log(filename)
        if self.log_file:
            self.log('Python Version: %s\nDHParser Version: %s\n\n'
                     % (sys.version.replace('\n', ' '), __version__))
            return 'Started logging to file: "%s"' % self.log_file
        return 'Unable to write log-file: "%s"' % filename

    def stop_logging(self):
        if self.log_file:
            self.log('Logging will be stopped now!')
            ret = 'Stopped logging to file: "%s"' % self.log_file
            self.log_file = ''
        else:
            ret = 'No logging'
        return ret

    def log(self, *args):
        if self.log_file:
            append_log(self.log_file, *args, echo=self.echo_log)

    def rpc_identify_server(self):
        """Returns an identification string for the server."""
        return "DHParser " + __version__ + " " + self.server_name

    def rpc_logging(self, *args) -> str:
        """Starts logging with either a) the default filename, if args is
         empty or the empty string b) the given log file name if `args[0]`
         is a non-empty string c) stops logging if `args[0]` is `None`.
         """
        if len(args) > 0:
            log_name = args[0]
            if len(args) > 1:
                echo = args[1].upper()
                if echo in ("ECHO", "ECHO_ON"):
                    self.echo_log = True
                elif echo in ("NO_ECHO", "NOECHO", "ECHO_OFF"):
                    self.echo_log = False
                else:
                    return 'Second arg must be "ECHO_ON" or "ECHO_OFF", not: ' \
                           + ','.join(args[1:])
            if log_name is not None:
                return self.start_logging(log_name)
            else:
                return self.stop_logging()
        else:
            return self.start_logging()

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
        if params is None:
            params = tuple()
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

    async def respond(self, writer: asyncio.StreamWriter, response: Union[str, bytes]):
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
        self.log('RESPONSE: ', response.decode(), '\n\n')
        # print('returned: ', response)
        try:
            if sys.version_info >= (3, 9):
                await writer.write(response)
            else:
                writer.write(response)
                await writer.drain()
        except ConnectionError as err:
            self.log('ERROR when wrting data: ', str(err), '\n')
            self.connections.remove(id(writer))

    async def handle_plaindata_request(self, task_id: int,
                                       reader: asyncio.StreamReader,
                                       writer: asyncio.StreamWriter,
                                       data: bytes):
        """Processes a request in plain-data-format, i.e. neither http nor json_rpc"""
        if len(data) > self.max_data_size:
            await self.respond(writer, "Data too large! Only %i MB allowed"
                               % (self.max_data_size // (1024 ** 2)))
        elif data.startswith(STOP_SERVER_REQUEST):
            await self.respond(writer, self.stop_response)
            self.kill_switch = True
            reader.feed_eof()
        else:
            m = re.match(RE_FUNCTION_CALL, data)
            if m:
                func_name = m.group(1).decode()
                argstr = m.group(2).decode()
                if argstr:
                    argument = tuple(convert_argstr(s) for s in argstr.split(','))
                else:
                    argument = ()
            else:
                func_name = self.default
                argument = (data.decode(),)
            err_func = lambda *args, **kwargs: \
                'No function named "%s" known to server %s !' % (func_name, self.server_name)
            func = self.rpc_table.get(func_name, err_func)
            result, rpc_error = await self.run(func_name, func, argument)
            if rpc_error is None:
                if isinstance(result, str):
                    await self.respond(writer, result)
                elif result is not None:
                    try:
                        await self.respond(writer, json.dumps(result, cls=DHParser_JSONEncoder))
                    except TypeError as err:
                        await self.respond(writer, str(err))
            else:
                await self.respond(writer, rpc_error[1])
        self.finished_tasks[id(writer)].add(task_id)

    async def handle_http_request(self, task_id: int,
                                  reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter,
                                  data: bytes):
        if len(data) > self.max_data_size:
            await self.respond(writer, http_response("Data too large! Only %i MB allowed"
                                                     % (self.max_data_size // (1024 ** 2))))
        else:
            result, rpc_error = None, None
            m = re.match(RE_GREP_URL, data)
            # m = RX_GREP_URL(data.decode())
            if m:
                func_name, argument = m.group(1).decode().strip('/').split('/', 1) + [None]
                if func_name.encode() == STOP_SERVER_REQUEST:
                    await self.respond(
                        writer, http_response(ONELINER_HTML.format(line=self.stop_response)))
                    self.kill_switch = True
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
                            await self.respond(writer, http_response(result))
                        else:
                            try:
                                await self.respond(writer, http_response(
                                    json.dumps(result, indent=2, cls=DHParser_JSONEncoder)))
                            except TypeError as err:
                                await self.respond(writer, http_response(str(err)))
                    else:
                        await self.respond(writer, http_response(rpc_error[1]))
        self.finished_tasks[id(writer)].add(task_id)

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
                self.connections.remove(id(writer))
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
                    await self.respond(writer, json.dumps(json_result, cls=DHParser_JSONEncoder))
                except TypeError as err:
                    rpc_error = -32070, str(err)

        if rpc_error is not None:
            await self.respond(
                writer, ('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}'
                         % (rpc_error[0], rpc_error[1], json_id)))

        if result is not None or rpc_error is not None:
            await writer.drain()
        self.finished_tasks[id(writer)].add(json_id)

    async def connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        id_writer = id(writer)  # type: int
        self.connections.add(id_writer)
        self.log('SERVER MESSAGE: New connection: ', str(id_writer), '\n')
        self.active_tasks[id_writer] = dict()   # type: Dict[id, asyncio.Task]
        self.finished_tasks[id_writer] = set()  # type: Set[int]
        buffer = b''  # type: bytes
        while not self.kill_switch and id_writer in self.connections:
            # reset the data variable
            data = b''  # type: bytes
            # reset the content length
            content_length = 0  # type: int
            # reset the length of the header, represented by the variable `k`
            k = 0  # type: int

            # The following loop buffers the data from the stream until a complete data
            # set consisting of 1) a header containing a "Content-Length: ..." field,
            # 2) a separator consisting of an empty line and 3) a data-package of exactly
            # the size given in the "Context-Length"- Field has been received.
            #
            # There are four cases to cover:
            #
            # a) the data received does not contain a Content-Length-field. In this case
            #    the data is considered plain data or json-rpc data wihout a header. The
            #    data passed through as is without worrying about its size.
            #
            # b) the data has a header with a Content-Length-field and the size of the
            #    data is exactly the size of the header (including the separator) plus
            #    the value given in the Content-Length field (i.e. `k + content_length`).
            #    In this case the data is passed through.
            #
            # c) the data has a header but the size is less than the header's size plus
            #    the content-length mentioned in the header. In this case further data
            #    is awaited from the stream until the aggregated data has at least the
            #    size of header and content-length.
            #
            # d) the data has a header but the size is more than the header's size plus
            #    the content-length value. In this case the excess data is buffered,
            #    and only the data up to the size of the header plus the content-length
            #    is passed through.
            #
            # Thus, at the end of the loop the `data`-variable always contains one
            # complete package of data (and not more), including a header at
            # the beginning, if there was any.
            #
            # see also: test/test_server.TestLanguageServer.test_varying_data_chunk_sizes

            while (content_length <= 0 or len(data) < content_length + k) \
                    and not self.kill_switch and id_writer in self.connections \
                    and not reader.at_eof():
                if buffer:
                    # if there is any data in the buffer, retrieve this first,
                    # before awaiting further data from the stream
                    data += buffer
                    buffer = b''
                else:
                    try:
                        data += await reader.read(self.max_data_size + 1)
                    except ConnectionError as err:  # (ConnectionAbortedError, ConnectionResetError)
                        self.log('ERROR while awaiting data: ', str(err), '\n')
                        self.connections.remove(id_writer)
                        break
                if content_length <= 0:
                    # If content-length has not been set, look for it in the
                    # received data package. This assumes that if there is
                    # a header at all, it is transmitted in one chunk and not
                    # in pieces, e.g. b'Cont', b'ent-Length: 52'!
                    # TODO: Check with the TDP-manual, whether this assumption can be relied on!
                    i = data.find(b'Content-Length:', 0, 512)
                    m = RX_CONTENT_LENGTH.match(data, i, i + 100) if i >= 0 else None
                    if m:
                        content_length = int(m.group(1))
                        m2 = re_find(data, RE_DATA_START)
                        if m2:
                            k = m2.end()
                            if len(data) > k + content_length:
                                # cut the data of at header size plus content-length
                                buffer = data[k + content_length:]
                                data = data[:k + content_length]
                    else:
                        # no header or no context-length given
                        # set `context_length` to the size of the data to break the loop
                        content_length = len(data)
                elif content_length + k < len(data):
                    # cut the data of at header size plus content-length
                    buffer = data[content_length + k:]
                    data = data[:content_length + k]
                # continue the loop until at least content_length + k bytes of data
                # have been received

            self.log('RECEIVE: ' , data.decode(), '\n')

            # remove finished tasks from active_tasks list,
            # so that the task-objects can be garbage collected
            for task_id in self.finished_tasks[id_writer]:
                del self.active_tasks[id_writer][task_id]
            self.finished_tasks[id_writer] = set()

            if id_writer not in self.connections:
                break
            elif not data and reader.at_eof():
                self.connections.remove(id_writer)
                break

            if data.startswith(b'GET'):
                # HTTP request
                task_id = gen_task_id()
                task = asyncio.ensure_future(self.handle_http_request(
                    task_id, reader, writer, data))
                assert task_id not in self.active_tasks, str(task_id)
                self.active_tasks[id_writer][task_id] = task

            elif not data.find(b'"jsonrpc"') >= 0:  # re.match(RE_IS_JSONRPC, data):
                # plain data
                task_id = gen_task_id()
                task = asyncio.ensure_future(self.handle_plaindata_request(
                    task_id, reader, writer, data))
                assert task_id not in self.active_tasks, str(task_id)
                self.active_tasks[id_writer][task_id] = task

            else:
                # assume json
                # TODO: add batch processing capability! (put calls to execute in asyncio tasks, use asyncio.gather)
                json_id = 0
                raw = None
                json_obj = {}
                rpc_error = None
                # see: https://microsoft.github.io/language-server-protocol/specification#header-part
                # i = max(data.find(b'\n\n'), data.find(b'\r\n\r\n')) + 2
                i = data.find(b'{')
                if i > 0:
                    data = data[i:]
                if len(data) > self.max_data_size:
                    rpc_error = -32600, "Request is too large! Only %i MB allowed" \
                                % (self.max_data_size // (1024 ** 2))

                if rpc_error is None:
                    try:
                        raw = json.loads(data.decode())
                    except json.decoder.JSONDecodeError as e:
                        rpc_error = -32700, "JSONDecodeError: " + (str(e) + str(data)).replace('"', "`")

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
                    self.active_tasks[id_writer][json_id] = task
                else:
                    await self.respond(writer,
                        ('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}'
                         % (rpc_error[0], rpc_error[1], json_id)))

        if self.kill_switch or id_writer not in self.connections:
            # TODO: terminate all active tasks depending on this particular connection
            try:
                writer.write_eof()
                await writer.drain()
                writer.close()
            except (ConnectionError, OSError) as err:
                self.log('ERROR while shutdown: ', str(err), '\n')
            self.log('SERVER MESSAGE: Closing Connection: %i.\n\n' % id_writer)
            open_tasks = {task for id, task in self.active_tasks[id_writer].items()
                          if id not in self.finished_tasks[id_writer]}
            if open_tasks:
                done, pending = await asyncio.wait(open_tasks, timeout=3.0)
                for task in pending:
                    task.cancel()
            del self.active_tasks[id_writer]
            del self.finished_tasks[id_writer]

        if self.kill_switch:
            # TODO: terminate processes and threads! Is this needed?
            # TODO: terminate all connections
            self.connections = set()
            self.stage.value = SERVER_TERMINATING
            if sys.version_info >= (3, 7):
                await writer.wait_closed()
                self.serving_task.cancel()
            else:
                self.server.close()  # break self.server.serve_forever()
            if sys.version_info < (3, 7) and self.loop is not None:
                self.loop.stop()
            self.log('SERVER MESSAGE: Stopping Server: %i.\n\n' % id_writer)
            self.kill_switch = False  # reset flag

    async def connection_py38(self, stream: 'asyncio.Stream'):
        await self.connection(stream, stream)

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
            self.server = cast(asyncio.AbstractServer,
                               await asyncio.start_server(self.connection, host, port))
            async with self.server:
                self.stage.value = SERVER_ONLINE
                # self.server_messages.put(SERVER_ONLINE)
                self.serving_task = asyncio.create_task(self.server.serve_forever())
                await self.serving_task
        finally:
            if self.server is not None and sys.version_info < (3, 8):
                await self.server.wait_closed()
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
                # self.server_messages.put(SERVER_ONLINE)
                self.loop.run_forever()
            finally:
                self.server.close()
                try:
                    self.loop.run_until_complete(self.server.wait_closed())
                finally:
                    if loop is None:
                        try:
                            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                        finally:
                            asyncio.set_event_loop(None)
                            self.loop.close()
                            self.loop = None

    # def _empty_message_queue(self):
    #     while not self.server_messages.empty():
    #         self.server_messages.get()

    def run_server(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT, loop=None):
        """
        Starts a DHParser-Server. This function will not return until the
        DHParser-Server ist stopped by sending a STOP_SERVER_REQUEST.
        """
        assert self.stage.value == SERVER_OFFLINE
        self.stage.value = SERVER_STARTING
        # self._empty_message_queue()
        if self.echo_log:
            print("Server logging is on.")
        try:
            if sys.version_info >= (3, 7):
                asyncio_run(self.serve(host, port))
            else:
                self.serve_py35(host, port, loop)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        except asyncio.CancelledError:
            if self.stage.value != SERVER_TERMINATING:
                raise
        # self.server_messages.put(SERVER_OFFLINE)
        self.stage.value = SERVER_OFFLINE


def run_server(host, port, rpc_functions: RPC_Type,
               cpu_bound: Set[str] = ALL_RPCs,
               blocking: Set[str] = frozenset()):
    """Start a server and wait until server is closed."""
    server = Server(rpc_functions, cpu_bound, blocking)
    server.run_server(host, port)


def dummy_server(s: str) -> str:
    return s


def spawn_server(host: str = USE_DEFAULT_HOST,
                 port: int = USE_DEFAULT_PORT,
                 parameters: Union[Tuple, Callable] = dummy_server) -> Process:
    """
    Start DHParser-Server in a separate process and return.
    Useful for writing test code.
    WARNING: Does not seem to work with multiprocessing.set_start_method('spawn')
             under linux !?
    """
    if isinstance(parameters, tuple) or isinstance(parameters, list):
        p = Process(target=run_server, args=(host, port, *parameters))
    else:
        p = Process(target=run_server, args=(host, port, parameters))
    p.start()
    return p


RUN_SERVER_SCRIPT_TEMPLATE = """
import os
import sys

sys.path.append(os.path.abspath('{IMPORT_PATH}'))
path = '.'
while not 'DHParser' in os.listdir(path) and len(path) < 20:
    path = os.path.join('..', path)
if len(path) < 20:
    sys.path.append(os.path.abspath(path))

{INITIALIZATION}

def run_server(host, port):
    from DHParser.server import asyncio_run, Server, stop_server, has_server_stopped
    {LOGGING}
    stop_server(host, port, 2.0)
    server = Server({PARAMETERS})
    server.run_server(host, port)

if __name__ == '__main__':
    run_server('{HOST}', {PORT})
"""

LOGGING_BLOCK = """from DHParser.log import start_logging
    from DHParser.configuration import set_config_value
    set_config_value('log_dir', os.path.abspath("LOGS"))
    set_config_value('log_server', True)
    set_config_value('echo_server_log', True)"""

python_interpreter_name_cached = ''


def detach_server(host: str = USE_DEFAULT_HOST,
                 port: int = USE_DEFAULT_PORT,
                 initialization: str = '',
                 parameters: str = 'lambda s: s',
                 import_path: str = '.'):
    """
    Start DHParser-Server in a separate process and return. The process remains
    active even after the parent process is closed. Useful for writing test code.
    """
    async def wait_for_connection(host, port):
        reader, writer = await asyncio_connect(host, port)  # wait until server online
        writer.close()
        # if sys.version_info >= (3, 7):
        #     await writer.wait_closed()

    global python_interpreter_name_cached
    host, port = substitute_default_host_and_port(host, port)
    null_device = " >/dev/null" if platform.system() != "Windows" else " > NUL"
    if python_interpreter_name_cached:
        interpreter = python_interpreter_name_cached
    else:
        interpreter = 'python3' if os.system('python3 -V' + null_device) == 0 else 'python'
        # interpreter = '/home/eckhart/.local/bin/python3.8'
        # interpreter = "pypy3"
        python_interpreter_name_cached = interpreter
    logging = ''  # type: str
    if is_logging() and get_config_value('log_server'):
        logging = LOGGING_BLOCK.format(LOGDIR=get_config_value('log_dir').replace('\\', '\\\\'),
                                       ECHO=get_config_value('echo_server_log'))
    run_server_script = RUN_SERVER_SCRIPT_TEMPLATE.format(
        HOST=host, PORT=port, INITIALIZATION=initialization, LOGGING=logging,
        PARAMETERS=parameters, IMPORT_PATH=import_path.replace('\\', '\\\\'))
    # print(run_server_script)
    if sys.version_info >= (3, 6):
        subprocess.Popen([interpreter, '-c', run_server_script], encoding="utf-8")
    else:
        subprocess.Popen([interpreter, '-c', run_server_script])
    asyncio_run(wait_for_connection(host, port))


async def has_server_stopped(host: str = USE_DEFAULT_HOST,
                             port: int = USE_DEFAULT_PORT,
                             timeout: float = 3.0) -> bool:
    """
    Returns True, if no server is running or any server that is running
    has stopped within the given timeout. Returns False, if server has
    not stopped and is still running.
    """
    host, port = substitute_default_host_and_port(host, port)
    delay = timeout / 1.5**12 if timeout > 0.0 else timeout - 0.001
    try:
        while delay < timeout:
            _, writer = await asyncio_connect(host, port, retry_timeout=0.0)
            writer.close()
            if sys.version_info >= (3, 7):
                await writer.wait_closed()
            if delay > 0.0:
                time.sleep(delay)
                delay *= 1.5
            else:
                delay = timeout  # exit while loop
        return False
    except ConnectionRefusedError:
        return True


def stop_server(host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT,
                timeout: float = 3.0) -> Optional[Exception]:
    """Sends a STOP_SERVER_REQUEST to a running server. Returns any exceptions
    that occurred."""
    async def send_stop_server(host: str, port: int) -> Optional[Exception]:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(STOP_SERVER_REQUEST)
            await writer.drain()
            _ = await reader.read(1024)
            writer.write_eof()
            writer.close()
            if sys.version_info >= (3, 7):
                await writer.wait_closed()
            if timeout > 0.0:
                if not await has_server_stopped(host, port, timeout):
                    raise AssertionError('Could not stop server on host %s port %i '
                                         'within timeout %f !' % (host, port, timeout))
        except ConnectionRefusedError as error:
            return error
        except ConnectionResetError as error:
            return error
        return None

    host, port = substitute_default_host_and_port(host, port)
    return asyncio_run(send_stop_server(host, port))


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
