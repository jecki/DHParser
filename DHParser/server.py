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

<https://www.jsonrpc.org/specification>

For JSON see:

<https://json.org/>

The `server`-module contains some rudimentary support for the language server protocol.
For the specification and implementation of the language server protocol, see:

<https://code.visualstudio.com/api/language-extensions/language-server-extension-guide>

<https://microsoft.github.io/language-server-protocol/>

<https://langserver.org/>
"""

import asyncio
from concurrent.futures import Executor, ThreadPoolExecutor, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
try:
    from concurrent.futures.thread import BrokenThreadPool
except ImportError:
    # BrokenThreadPool requires Python version >= 3.8
    class BrokenThreadPool:
        pass
from functools import partial
import json
from multiprocessing import Process, Value, Array
import platform
import os
import subprocess
import sys
import time
from typing import Callable, Coroutine, Awaitable, Optional, Union, Dict, List, Tuple, Sequence, \
    Set, Iterator, Iterable, Any, cast, Type

from DHParser.configuration import access_thread_locals, get_config_value
from DHParser.syntaxtree import DHParser_JSONEncoder
from DHParser.log import create_log, append_log, is_logging, log_dir
from DHParser.toolkit import re, re_find
from DHParser.versionnumber import __version__


__all__ = ('RPC_Table',
           'RPC_Type',
           'RPC_Error_Type',
           'JSON_Type',
           'JSON_Dict',
           'ConnectionCallback',
           'SERVER_ERROR',
           'SERVER_OFFLINE',
           'SERVER_STARTING',
           'SERVER_ONLINE',
           'SERVER_TERMINATING',
           'USE_DEFAULT_HOST',
           'USE_DEFAULT_PORT',
           'STOP_SERVER_REQUEST_BYTES',
           'IDENTIFY_REQUEST',
           'LOGGING_REQUEST',
           'ALL_RPCs',
           'asyncio_run',
           'asyncio_connect',
           'split_header',
           'ExecutionEnvironment',
           'Connection',
           'connection_cb_dummy',
           'Server',
           'spawn_server',
           'stop_server',
           'has_server_stopped',
           'gen_lsp_name',
           'gen_lsp_table')


RPC_Table = Dict[str, Callable]
RPC_Type = Union[RPC_Table, List[Callable], Callable]
RPC_Error_Type = Optional[Tuple[int, str]]
JSON_Type = Union[Dict, Sequence, str, int, None]
JSON_Dict = Dict[str, JSON_Type]
BytesType = Union[bytes, bytearray]
ConnectionCallback = Callable[['Connection'], None]

RE_IS_JSONRPC = rb'(?:.*?\n\n)?\s*(?:{\s*"jsonrpc")|(?:\[\s*{\s*"jsonrpc")'
# b'\s*(?:{|\[|"|\d|true|false|null)'
RE_GREP_URL = rb'GET ([^ \n]+) HTTP'
RE_FUNCTION_CALL = rb'\s*(\w+)\(([^)]*)\)$'
RX_CONTENT_LENGTH = re.compile(rb'Content-Length:\s*(\d+)')
RE_DATA_START = rb'\r?\n\r?\n'

SERVER_ERROR = "COMPILER-SERVER-ERROR"

# DSL-Server run-stage
SERVER_OFFLINE = 0
SERVER_STARTING = 1
SERVER_ONLINE = 2
SERVER_TERMINATING = 3

# Language-Server initializiation and shutdown-stage flag values
LSP_INITIALIZING = "initializing"
LSP_INITIALIZED = "initialized"
LSP_SHUTTING_DOWN = "shutting-down"
LSP_SHUTDOWN = "shut-down"

# Response-header-templates
HTTP_RESPONSE_HEADER = '''HTTP/1.1 200 OK
Date: {date}
Server: DHParser
Accept-Ranges: none
Content-Length: {length}
Connection: close
Content-Type: text/html; charset=utf-8
X-Pad: avoid browser bug

'''

JSONRPC_HEADER = b'''Content-Length: %i\r\n\r\n'''

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

STOP_SERVER_REQUEST = "__STOP_SERVER__"
STOP_SERVER_REQUEST_BYTES = b"__STOP_SERVER__"
IDENTIFY_REQUEST = "identify()"
LOGGING_REQUEST = "logging('')"


def substitute_default_host_and_port(host, port):
    """Substiutes the default value(s) from the configuration file if host
     or port ist ``USE_DEFAULT_HOST`` or ``USE_DEFAULT_PORT``. """
    if host == USE_DEFAULT_HOST:
        host = get_config_value('server_default_host')
    if port == USE_DEFAULT_PORT:
        port = get_config_value('server_default_port')
    return host, port


def as_json_rpc(func: Callable,
                params: Union[List[JSON_Type], Dict[str, JSON_Type]] = [],
                ID: Optional[int] = None) -> str:
    """Generates a JSON-RPC-call for `func` with parameters `params`"""
    return json.dumps({"jsonrpc": "2.0", "method": func.__name__, "params": params, "id": ID})


def convert_argstr(s: str) -> Union[None, bool, int, str, List, Dict]:
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


def asyncio_run(coroutine: Awaitable, loop=None) -> Any:
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


async def asyncio_connect(
        host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT,
        retry_timeout: float = 3.0) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Opens a connection with timeout retry-timeout."""
    host, port = substitute_default_host_and_port(host, port)
    delay = retry_timeout / 1.5**12 if retry_timeout > 0.0 else retry_timeout - 0.001
    connected = False
    reader, writer = None, None
    save_error = ConnectionError  # type: Union[Type[ConnectionError], ConnectionRefusedError]
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
    if connected and reader is not None and writer is not None:
        return reader, writer
    else:
        raise save_error


def GMT_timestamp() -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())


ALL_RPCs = set('*')  # Magic value denoting all remote procedures


def default_fallback(*args, **kwargs) -> str:
    return 'No default RPC-function defined!'


def http_response(html: str) -> bytes:
    """Embeds an html-string in a http header and returns the http-package
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


def incomplete_header(data: BytesType) -> bool:
    """Returns `True` if data appears to represent an incomplete header."""
    return b'Content-Length'.startswith(data) or \
           (data.startswith(b'Content-Length') and not re_find(data, RE_DATA_START))


def split_header(data: BytesType) -> Tuple[BytesType, BytesType, BytesType]:
    """Splits the given data-chunk and returns tuple (header, data, backlog).
    If the data-chunk is incomplete it will be returned unchanged while the
    returned header remains empty."""
    header = b''
    backlog = b''
    i = data.find(b'Content-Length:', 0, 512)
    m = RX_CONTENT_LENGTH.match(data, i, i + 100) if i >= 0 else None
    if m:
        content_length = int(m.group(1))
        m2 = re_find(data, RE_DATA_START)
        if m2:
            header_size = m2.end()
            if len(data) >= header_size + content_length:
                # cut the data of at header size plus content-length
                header = data[:header_size]
                backlog = data[header_size + content_length:]
                data = data[header_size:header_size + content_length]
    elif not incomplete_header(data):
        raise ValueError('data does not contain a valid header')
    return header, data, backlog


def strip_header_delimiter(data: str) -> Tuple[str]:
    i = max(data.find('\n'), data.find('\r'))
    return (data[:i].rstrip(), '\n', data[i:].lstrip()) if i >= 0 else (data,)


def gen_task_id() -> int:
    """Generate a unique task id. This is always a negative number to
    distinguish the taks id's from the json-rpc ids.
    """
    THREAD_LOCALS = access_thread_locals()
    try:
        value = THREAD_LOCALS.DHParser_server_task_id
        THREAD_LOCALS.DHParser_server_task_id = value - 1
    except AttributeError:
        THREAD_LOCALS.DHParser_server_task_id = -2
        value = -1
    assert value < 0
    return value


class ExecutionEnvironment:
    """Class ExecutionEnvironment provides methods for executing server tasks
    in separate processes, threads, as asynchronous task or as simple function.

    Attributes:
        process_executor:  A process-pool-executor for cpu-bound tasks
        thread_executor:   A thread-pool-executor for blocking tasks
        loop:              The asynchronous event loop for running coroutines
        log_file:          The name of the log-file to which error messages
                           are written if an executor raises a Broken-Error.
        _closed            A Flag that is set to True after the `shutdown()`-
                           method has been called. After that any
                           call to the `execute()`-method yields an error.
    """
    def __init__(self, event_loop: asyncio.AbstractEventLoop):
        self.process_executor = ProcessPoolExecutor()  # type: Optional[ProcessPoolExecutor]
        self.thread_executor = ThreadPoolExecutor()    # type: Optional[ThreadPoolExecutor]
        self.loop = event_loop                         # type: asyncio.AbstractEventLoop
        self.log_file = ''                             # type: str
        self._closed = False                           # type: bool

    def __del__(self):
        self.shutdown(False)

    async def execute(self, executor: Optional[Executor],
                      method: Callable,
                      params: Union[Dict, Sequence])\
            -> Tuple[Optional[JSON_Type], Optional[RPC_Error_Type]]:
        """Executes a method with the given parameters in a given executor
        (`ThreadPoolExcecutor` or `ProcessPoolExecutor`). `execute()`waits for
        the completion and returns the JSON result and an RPC error tuple (see
        the type definition above). The result may be None and the error may be
        zero, i.e. no error. If `executor` is `None`the method will be called
        directly instead of deferring it to an executor.
        """
        if self._closed:
            return None, (-32000,
                          "Server Error: Execution environment has already been shut down! "\
                          "Cannot process method {} with parameters {} any more."\
                          .format(method, params))
        result = None      # type: Optional[JSON_Type]
        rpc_error = None   # type: Optional[RPC_Error_Type]
        if params is None:
            params = tuple()
        if isinstance(params, Dict):
            executable = partial(method, **params)
        elif isinstance(params, Sequence):
            executable = partial(method, *params)
        else:
            rpc_error = -32040, "Invalid parameter type %s for %s. Must be Dict or Sequence" \
                        % (str(type(params)), str(params))
            return result, rpc_error
        try:
            if executor is None:
                result = await executable() if asyncio.iscoroutinefunction(method) else executable()
            else:
                result = await self.loop.run_in_executor(executor, executable)
        except TypeError as e:
            rpc_error = -32602, "Invalid Params: " + str(e)
        except NameError as e:
            rpc_error = -32601, "Method not found: " + str(e)
        except BrokenProcessPool as e:
            if self.log_file:
                append_log(self.log_file, 'WARNING: Broken ProcessPoolExecutor detected. '
                           'Starting a new ProcessPoolExecutor', echo=True)
            try:
                # restart process pool and try again once
                self.process_executor.shutdown(wait=True)
                self.process_executor = ProcessPoolExecutor()
                await self.loop.run_in_executor(executor, executable)
            except BrokenProcessPool as e:
                rpc_error = -32050, str(e)
        except BrokenThreadPool as e:
            if self.log_file:
                append_log(self.log_file, 'WARNING: Broken ThreadPoolExecutor detected. '
                           'Starting a new ThreadPoolExecutor', echo=True)
            try:
                # restart thread pool and try again once
                self.thread_executor.shutdown(wait=True)
                self.thread_executor = ThreadPoolExecutor()
                await self.loop.run_in_executor(executor, executable)
            except BrokenThreadPool as e:
                rpc_error = -32060, str(e)
        except Exception as e:
            rpc_error = -32000, "Server Error " + str(type(e)) + ': ' + str(e)
        return result, rpc_error

    def shutdown(self, wait: bool = True):
        """Shuts the thread and process executor of the execution environment. The
        wait parameter is passed to the shutdown-method of the thread and
        process-executor.
        """
        self._closed = True
        if self.thread_executor is not None:
            self.thread_executor.shutdown(wait=wait)
            self.thread_executor = None
        if self.process_executor is not None:
            self.process_executor.shutdown(wait=wait)
            self.process_executor = None


class Connection:
    """Class Connections encapsulates connection-specific data for the Server
    class (see below). At the moment, however, only one connection is accepted at
    one and the same time, assuming there is a one-on-one relationship between
    the Text-Editor (i.e. the client) and the language server. Still, it serves
    clarity to encapsulate the connection specific state.

    Currently, logging is not encapsulated, assuming that for the purpose of
    debugging the language server it is better not to have more than one
    connection at a time, anyway.

    Attributes:
        alive: Boolean flag, indicating that the connection is still alive.
                When set to false the connection will be closed, but the
                server will not be stopped.
        reader: the stream-reader for this connection
        writer: the stream-writer for this connection
        exec:   the execution environment of the server
        active_tasks: A dictionary that maps task id's (resp. jsonrpc id's)
                to their futures to keep track of  any running task.
        finished_tasks: a set of task id's (resp. jsonrpc id's) for tasks
                that have been finished and should be removed from the
                `active_tasks`-dictionary at the next possible time.
        response_queue:  An asynchronous queue which stores the json-rpc responses
                and errors received from a language server client as result of
                commands initiated by the server.
        pending_responses:  A dictionary of jsonrpc-/task-id's to lists of
                JSON-objects that have been fetched from the the response queue
                but not yet been collected by the calling task.
        lsp_initialized: A string-flag indicating that the connection to a language
                sever via json-rpc has been established.
        lsp_shutdown: A string-flag indicating that the connection to a language server
                via jason-rpc has been is or is being shut down.
        log_file:  Name of the server-log. Mirrors Server.log_file
        echo_log:  If `True` log messages will be echoed to the console. Mirrors
                Server.log_file
    """
    def __init__(self, reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter,
                 exec_env: ExecutionEnvironment):
        self.alive = True                # type: bool
        self.reader = reader             # type: asyncio.StreamReader
        self.writer = writer             # type: asyncio.StreamWriter
        self.exec = exec_env             # type: ExecutionEnvironment
        self.active_tasks = dict()       # type: Dict[int, asyncio.Future]
        self.finished_tasks = set()      # type: Set[int]
        self.response_queue = None       # type: Optional[asyncio.Queue]
        self.pending_responses = dict()  # type: Dict[int, List[JSON_Type]]
        self.lsp_initialized = ""        # type: str
        self.lsp_shutdown = ""           # type: str
        self.log_file = ""               # type: str
        self.echo_log = False            # type: bool

    # async-task support

    def create_task(self, json_id: int, coroutine: Coroutine) -> asyncio.futures.Future:
        assert json_id not in self.active_tasks, \
            "JSON-id {} already used!".format(json_id)
        task = asyncio.ensure_future(coroutine)
        self.active_tasks[json_id] = task
        return task

    def task_done(self, json_id: int):
        assert json_id in self.active_tasks
        self.finished_tasks.add(json_id)
        # do not do: del self.active_tasks[json_id] !!!

    async def cleanup(self):
        open_tasks = {task for id, task in self.active_tasks.items()
                      if id not in self.finished_tasks}
        if open_tasks:
            _, pending = await asyncio.wait(
                open_tasks, timeout=3.0)  # type: Set[asyncio.Future], Set[asyncio.Future]
            for task in pending:
                task.cancel()
            # wait for task's cancellation to actually finish
            await asyncio.gather(*pending, return_exceptions=True)
        self.active_tasks = dict()
        self.finished_tasks = set()

    # server initiated LSP-calls-support

    def put_response(self, json_obj: JSON_Type):
        """Adds a client-response to the waiting queue. The responses
        to a particual task can be queried with the `client_response()`-
        coroutine."""
        if self.log_file:
            self.log('RESULT: ', json.dumps(json_obj))
        assert self.response_queue is not None
        self.response_queue.put_nowait(json_obj)

    async def server_call(self, json_obj: JSON_Type):
        """Issues a json-rpc call from the server to the client."""
        json_str = json.dumps(json_obj)
        if self.log_file:
            self.log('CALL: ', json_str, '\n\n')
        request = json_str.encode()
        request = JSONRPC_HEADER % len(request) + request
        self.writer.write(request)
        await self.writer.drain()

    async def client_response(self, call_id: int) -> JSON_Type:
        """Waits for and returns the response from the lsp-client to the call
        with the id `call_id`."""
        pending = self.pending_responses.get(call_id, [])
        while not pending:
            assert self.response_queue is not None
            response = await self.response_queue.get()
            self.pending_responses.setdefault(call_id, []).insert(0, response)
            pending = self.pending_responses.get(call_id, [])
        response = pending.pop()
        return response

    # LSP-initialization support

    def verify_initialization(self, method: str, strict: bool = True) -> RPC_Error_Type:
        """Implements the LSP-initialization logic and returns an rpc-error if
        either initialization went wrong or an rpc-method other than 'initialize'
        was called on an uninitialized languge server.
        """
        if method == 'initialize':
            if self.lsp_initialized:
                return -32002, 'language server already initializ(ed/ing)'
            elif self.lsp_shutdown == LSP_SHUTTING_DOWN:
                return -32002, 'cannot initialize language server while shutting down'
            else:
                self.lsp_initialized = LSP_INITIALIZING
                self.lsp_shutdown = ''
                self.response_queue = asyncio.Queue(maxsize=100)
        elif method == "initialized":
            if self.lsp_initialized == LSP_INITIALIZING:
                self.lsp_initialized = LSP_INITIALIZED
            else:
                return -32002, 'initialized notification while ' \
                               'language server was not in initializing state!'
        elif method == 'shutdown':
            self.lsp_shutdown = LSP_SHUTTING_DOWN
            self.lsp_initialized = ''
            self.response_queue = None  # drop potentially non empty queue
        elif method == 'exit':
            self.lsp_shutdown = LSP_SHUTDOWN
            self.lsp_initialized = ''
        elif strict and method != STOP_SERVER_REQUEST:
            if self.lsp_shutdown:
                return -32600, 'language server already shut down'
            elif self.lsp_initialized != LSP_INITIALIZED:
                return -32002, 'language server not initialized'
        return None

    # logging support

    def log(self, *args):
        if self.log_file:
            append_log(self.log_file, *args, echo=self.echo_log)


def connection_cb_dummy(connection: Connection) -> None:
    pass


class Server:
    """Class Server contains all the boilerplate code for a
    Language-Server-Protocol-Server.

    :param server_name: A name for the server. Defaults to
        `CLASSNAME_OBJECTID`
    :param strict_lsp: Enforce Language-Server-Protocol von json-rpc-calls.
        If `False` json-rpc calls will be processes even without prior
        initialization, just like plain data or http calls.
    :param cpu_bound: Set of function names of functions that are cpu-bound
        and will be run in separate processes.
    :param blocking: Set of functions that contain blocking calls
        (e.g. IO-calls) and will therefore be run in separate threads.
    :param rpc_table: Table mapping LSP-method names to Python functions
    :param known_methods: Set of all known LSP-methods. This includes the
        methods in the rpc-table and the four initialization methods,
        `initialize()`, `initialized()`, `shudown()`, `exit`
    :param connection_callback: A callback function that is called with the
        connection object as argument when a connection to a client is
        established
    :param max_data_size: Maximal size of a data chunk that can be read by
        the server at a time.
    :param stage:  The operation stage, the server is in. Can be on of the four
        values: `SERVER_OFFLINE`, `SERVER_STARTING`, `SERVER_ONLINE`,
        `SERVER_TERMINATING`
    :param host: The host, the server runs on, e.g. "127.0.0.1"
    :param port: The port of the server, e.g. 8888
    :param server: The asyncio.Server if the server is online, or `None`.
    :param serving_task: The task in which the asyncio.Server is run.
    :param stop_response:  The response string that is written to the stream
        as answer to a stop request.
    :param echo_log: Read from the global configuration. If True, any log
        message will also be echoed on the console.
    :param log_file: The file-name of the server-log.
    :param use_jsonrpc_header: Read from the global configuration. If True,
        jsonrpc-calls or responses will always be preceeded by a simple header
        of the form: "Content-Length: {NUM}\n\n", where "{NUM}" stands for
        the byte-size of the rpc-package.
    :param exec: An instance of the execution environment that delegates tasks
        to separate processes, threads, asynchronous tasks or simple function
        calls.
    :param connection: An instance of the connection class representing the
        data of the current connection or None, if there is no connection at
        the moment. There can be only one connection to the server at a time!
    :param kill_switch: If True the, the server will be shut down.
    :param loop: The asyncio event loop within which the asyncio stream server
        is run.
    """
    def __init__(self, rpc_functions: RPC_Type,
                 cpu_bound: Set[str] = ALL_RPCs,
                 blocking: Set[str] = set(),
                 connection_callback: ConnectionCallback = connection_cb_dummy,
                 server_name: str = '',
                 strict_lsp: bool = True):
        self.server_name = server_name or self.__class__.__name__
        self.strict_lsp = strict_lsp
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
            assert callable(rpc_functions)
            func = cast(Callable, rpc_functions)
            self.rpc_table = {func.__name__: func}
            self.default = func.__name__
        assert STOP_SERVER_REQUEST not in self.rpc_table

        # see: https://docs.python.org/3/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools
        self.cpu_bound = frozenset(self.rpc_table.keys()) if cpu_bound == ALL_RPCs else cpu_bound
        self.blocking = frozenset(self.rpc_table.keys()) if blocking == ALL_RPCs else blocking
        self.blocking = self.blocking - self.cpu_bound  # cpu_bound property takes precedence

        assert not (self.cpu_bound - self.rpc_table.keys())
        assert not (self.blocking - self.rpc_table.keys())

        self.connection_callback = connection_callback

        self.max_data_size = get_config_value('max_rpc_size')  # type: int
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

        self._log_file = ''       # type: str
        if get_config_value('log_server'):
            self.start_logging()
        self._echo_log = get_config_value('echo_server_log')  # type: bool
        self.use_jsonrpc_header = get_config_value('jsonrpc_header')  # type: bool

        self.register_service_rpc(IDENTIFY_REQUEST, self.rpc_identify_server)
        self.register_service_rpc(LOGGING_REQUEST, self.rpc_logging)

        self.exec = None          # type: Optional[ExecutionEnvironment]
        self.connection = None    # type: Optional[Connection]
        self.kill_switch = False  # type: bool
        self.loop = None          # type: Optional[asyncio.AbstractEventLoop]

        self.known_methods = set(self.rpc_table.keys()) | \
            {'initialize', 'initialized', 'shutdown', 'exit'}  # see self.verify_initialization()

    @property
    def log_file(self):
        return self._log_file

    @log_file.setter
    def log_file(self, value: str):
        self._log_file = value
        if self.connection:
            self.connection.log_file = value
        if self.exec:
            self.exec.log_file = value

    @property
    def echo_log(self):
        return self._echo_log

    @echo_log.setter
    def echo_log(self, value: bool):
        self._echo_log = value
        if self.connection:
            self.connection.echo_log = value

    def register_service_rpc(self, name, method):
        """Registers a service request """
        name = name[:name.find('(')]
        if name in self.rpc_table:
            self.log('Service {} is shadowed by an rpc-call with the same name.'.format(name))
        else:
            self.rpc_table[name] = method
            # self.known_methods.add(name)

    def start_logging(self, filename: str = "") -> str:
        if not filename:
            filename = self.server_name + '_' + hex(id(self))[2:] + '.log'
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

    def rpc_identify_server(self, service_call: bool = False):
        """Returns an identification string for the server."""
        if service_call:
            return "DHParser " + __version__ + " " + self.server_name + " already connected"
        else:
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

    async def run(self, method_name: str, method: Callable, params: Union[Dict, Sequence]) \
            -> Tuple[Optional[JSON_Type], Optional[RPC_Error_Type]]:
        """Picks the right execution method (process, thread or direct execution) and
        runs it in the respective executor. In case of a broken ProcessPoolExecutor it
        restarts the ProcessPoolExecutor and tries to execute the method again.
        """
        # run method either a) directly if it is short running or
        # b) in a thread pool if it contains blocking io or
        # c) in a process pool if it is cpu bound
        # see: https://docs.python.org/3/library/asyncio-eventloop.html
        #      #executing-code-in-thread-or-process-pools
        executor = self.exec.process_executor if method_name in self.cpu_bound else \
            self.exec.thread_executor if method_name in self.blocking else None
        result, rpc_error = await self.exec.execute(executor, method, params)
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
            response = ('Illegal response type %s of response object %s. '
                        'Only bytes and str allowed!'
                        % (str(type(response)), str(response))).encode()
        if self.use_jsonrpc_header and response.startswith(b'{'):
            response = JSONRPC_HEADER % len(response) + response
        if self.log_file:  # avoid data decoding if logging is off
            self.log('RESPONSE: ', *strip_header_delimiter(response.decode()), '\n\n')
        try:
            writer.write(response)
            await writer.drain()
        except ConnectionError as err:
            self.log('ERROR when writing data: ', str(err), '\n')
            if self.connection:
                self.connection.alive = False

    def amend_service_call(self, func_name: str, func: Callable, argument: Union[Tuple, Dict],
                           err_func: Callable) -> Tuple[Callable, Union[Tuple, Dict]]:
        if argument is None:
            argument = ()
        if getattr(func, '__self__', None) == self:
            if isinstance(argument, Dict):
                params = argument.copy()
                params.update({'service_call': True})
                return func, params
            else:
                return func, argument + (True,)
        else:
            return err_func, {} if isinstance(argument, Dict) else ()

    async def handle_plaindata_request(self, task_id: int,
                                       reader: asyncio.StreamReader,
                                       writer: asyncio.StreamWriter,
                                       data: BytesType,
                                       service_call: bool = False):
        """Processes a request in plain-data-format, i.e. neither http nor json-rpc"""
        if len(data) > self.max_data_size:
            await self.respond(writer, "Data too large! Only %i MB allowed"
                               % (self.max_data_size // (1024 ** 2)))
        elif data.startswith(STOP_SERVER_REQUEST_BYTES):
            await self.respond(writer, self.stop_response)
            self.kill_switch = True
            reader.feed_eof()
        else:
            m = re.match(RE_FUNCTION_CALL, data)
            if m:
                func_name = m.group(1).decode()
                argstr = m.group(2).decode()
                if argstr:
                    argument = tuple(convert_argstr(s)
                                     for s in argstr.split(','))  # type: Union[Tuple, Dict]
                else:
                    argument = ()
            else:
                func_name = self.default
                argument = (data.decode(),)

            err_func = lambda *args, **kwargs: \
                'No function named "%s" known to server %s !' % (func_name, self.server_name)
            func = self.rpc_table.get(func_name, err_func)  # type: Callable
            if service_call:
                func, argument = self.amend_service_call(func_name, func, argument, err_func)
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
        assert self.connection
        self.connection.task_done(task_id)

    async def handle_http_request(self, task_id: int,
                                  reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter,
                                  data: BytesType,
                                  service_call: bool = False):
        if len(data) > self.max_data_size:
            await self.respond(writer, http_response("Data too large! Only %i MB allowed"
                                                     % (self.max_data_size // (1024 ** 2))))
        else:
            m = re.match(RE_GREP_URL, data)
            if m:
                func_name, argument = m.group(1).decode().strip('/').split('/', 1) + [None]
                if func_name.encode() == STOP_SERVER_REQUEST_BYTES:
                    await self.respond(
                        writer, http_response(ONELINER_HTML.format(line=self.stop_response)))
                    self.kill_switch = True
                    reader.feed_eof()
                else:
                    err_func = lambda _: UNKNOWN_FUNC_HTML.format(func=func_name)
                    func = self.rpc_table.get(func_name, err_func)
                    if service_call:
                        func, argument = self.amend_service_call(
                            func_name, func, argument, err_func)
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
        assert self.connection
        self.connection.task_done(task_id)

    async def handle_jsonrpc_request(self, json_id: int,
                                     reader: asyncio.StreamReader,
                                     writer: asyncio.StreamWriter,
                                     json_obj: Dict,
                                     service_call: bool = False):
        # TODO: handle cancellation calls!
        result = None      # type: Optional[JSON_Type]
        rpc_error = None   # type: Optional[RPC_Error_Type]
        method_name = json_obj.get('method', '')
        if json_obj.get('jsonrpc', '0.0') < '2.0':
            rpc_error = -32600, 'Invalid Request: jsonrpc version 2.0 needed, version "' \
                                ' "%s" found.' % json_obj.get('jsonrpc', b'unknown')
        elif not method_name:
            rpc_error = -32600, 'Invalid Request: No method specified.'
        elif method_name == STOP_SERVER_REQUEST:
            result = self.stop_response
            self.kill_switch = True
            reader.feed_eof()
        elif method_name == 'exit':
            assert self.connection
            self.connection.alive = False
            reader.feed_eof()
        elif method_name not in self.known_methods:  # self.rpc_table:
            rpc_error = -32601, 'Method not found: ' + str(json_obj['method'])
        elif method_name in self.rpc_table:
            # method_name = json_obj['method']
            method = self.rpc_table[method_name]
            params = json_obj['params'] if 'params' in json_obj else {}
            if service_call:
                err_func = lambda *args, **kwargs: {
                    "error": {"code": -32601,
                              "message": "%s is not a service function" % method_name}}
                method, params = self.amend_service_call(method_name, method, params, err_func)
            result, rpc_error = await self.run(method_name, method, params)

        if isinstance(result, Dict) and 'error' in result:
            try:
                rpc_error = result['error']['code'], result['error']['message']
            except KeyError:
                rpc_error = -32603, 'Inconclusive error object: ' + str(result)

        if rpc_error is None:
            try:
                # check for json-rpc errors contained within the result
                try:
                    error = cast(Dict[str, str], result['error'])
                except KeyError:
                    error = cast(Dict[str, str], result)
                rpc_error = int(error['code']), error['message']
            except TypeError:
                pass  # result is not a dictionary, never mind
            except KeyError:
                pass  # no errors in result
            if json_id is not None and result is not None:
                try:
                    json_result = {"jsonrpc": "2.0", "result": result, "id": json_id}
                    await self.respond(writer, json.dumps(json_result, cls=DHParser_JSONEncoder))
                except TypeError as err:
                    rpc_error = -32070, str(err)

        if rpc_error is not None:
            await self.respond(
                writer, ('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}' %
                         (rpc_error[0], rpc_error[1], str(json_id) if json_id >= 0 else 'null')))

        if result is not None or rpc_error is not None:
            await writer.drain()
        assert self.connection
        self.connection.task_done(json_id)

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if self.connection is None:
            self.connection = Connection(reader, writer, self.exec)
            self.connection.log_file = self.log_file
            self.connection.echo_log = self.echo_log
            id_connection = str(id(self.connection))
            self.connection_callback(self.connection)
            self.log('SERVER MESSAGE: New connection: ', id_connection, '\n')
        else:
            id_connection = ''

        def connection_alive() -> bool:
            """-> `False` if connection is dead or shall be shut down."""
            assert self.connection
            return not self.kill_switch and self.connection.alive and not reader.at_eof()

        buffer = bytearray()  # type: bytearray
        while connection_alive():
            # reset the data variable
            data = bytearray()  # type: bytearray
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

            while (content_length <= 0 or len(data) < content_length + k) and connection_alive():
                if buffer:
                    # if there is any data in the buffer, retrieve this first,
                    # before awaiting further data from the stream
                    data += buffer
                    buffer = bytearray()
                else:
                    try:
                        data += await reader.read(self.max_data_size + 1)
                    except ConnectionError as err:  # (ConnectionAbortedError, ConnectionResetError)
                        self.log('ERROR while awaiting data: ', str(err), '\n')
                        if id_connection:
                            self.connection.alive = False
                        break
                if content_length <= 0:
                    # If content-length has not been set, look for it in the received data package.
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
                    elif not incomplete_header(data):
                        # no header or no context-length given
                        # set `context_length` to the size of the data to break the loop
                        content_length = len(data)
                elif content_length + k < len(data):
                    # cut the data of at header size plus content-length
                    buffer = data[content_length + k:]
                    data = data[:content_length + k]
                # continue the loop until at least content_length + k bytes of data
                # have been received

            if self.log_file:   # avoid decoding if logging is off
                self.log('RECEIVE: ', *strip_header_delimiter(data.decode()), '\n\n')

            if id_connection:
                if self.connection.alive:
                    if not data and self.connection.reader.at_eof():
                        self.connection.alive = False
                        break
                    # remove finished tasks from active_tasks list,
                    # so that the task-objects can be garbage collected
                    for task_id in self.connection.finished_tasks:
                        del self.connection.active_tasks[task_id]
                    self.connection.finished_tasks = set()
                else:
                    break

            task = None
            if data.startswith(b'GET'):
                # HTTP request
                task_id = gen_task_id()
                task = self.connection.create_task(task_id, self.handle_http_request(
                    task_id, reader, writer, data, service_call=not id_connection))
            elif not data.find(b'"jsonrpc"') >= 0:  # re.match(RE_IS_JSONRPC, data):
                # plain data
                task_id = gen_task_id()
                task = self.connection.create_task(task_id, self.handle_plaindata_request(
                    task_id, reader, writer, data, service_call=not id_connection))
            else:
                # assume json
                # TODO: add batch processing capability!
                #       (put calls to execute in asyncio tasks, use asyncio.gather)
                json_id = 0       # type: int
                raw = None        # type: Optional[JSON_Type]
                json_obj = {}     # type: JSON_Dict
                rpc_error = None  # type: Optional[RPC_Error_Type]
                # see: https://microsoft.github.io/language-server-protocol/specification#header-part
                # i = max(data.find(b'\n\n'), data.find(b'\r\n\r\n')) + 2
                i = data.find(b'{')
                if i > 0:
                    data = data[i:]
                if len(data) > self.max_data_size:
                    rpc_error = -32600, "JSON-package is too large! Only %i MB allowed" \
                        % (self.max_data_size // (1024 ** 2))

                if rpc_error is None:
                    try:
                        raw = json.loads(data) if sys.version_info >= (3, 6) \
                            else json.loads(data.decode())
                    except json.decoder.JSONDecodeError as e:
                        rpc_error = -32700, "JSONDecodeError: " \
                            + (str(e) + str(data)).replace('"', "`")

                if rpc_error is None:
                    if isinstance(raw, Dict):
                        json_obj = cast(JSON_Dict, raw)
                        raw_id = cast(Union[str, int], json_obj.get('id', gen_task_id()))
                        json_id = int(raw_id)
                    else:
                        rpc_error = -32700, 'Parse error: JSON-package does not appear '\
                                            'to ba an RPC-call or -response!?'

                if rpc_error is None:
                    method = json_obj.get('method', '')
                    response = json_obj.get('result', None) or json_obj.get('error', None)
                    if method:
                        assert isinstance(method, str)
                        if id_connection or method != 'initialize':
                            rpc_error = self.connection.verify_initialization(
                                method, self.strict_lsp and bool(id_connection))
                            if rpc_error is None:
                                task = self.connection.create_task(
                                    json_id, self.handle_jsonrpc_request(
                                        json_id, reader, writer, json_obj, not bool(id_connection)))
                                if method == 'exit':
                                    await task
                                    task = None
                        else:
                            rpc_error = -32002, 'server is already connected to another client'
                    elif response is not None:
                        if id_connection:
                            self.connection.put_response(json_obj)
                    else:
                        rpc_error = -32700, 'Parse error: Not a valid JSON-RPC! '\
                                            '"method" or "response"-field missing.'

                if rpc_error is not None:
                    response = '{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"},'\
                        ' "id": %s}' % (rpc_error[0], rpc_error[1], json_id)
                    await self.respond(writer, response)

            if not id_connection:
                if task:
                    await task
                    task = None
                # for secondary connections only one request is allowed before terminating
                try:
                    writer.write_eof()
                    await writer.drain()
                    writer.close()
                    # if sys.version_info >= (3, 7):  await writer.wait_closed()
                except (ConnectionError, OSError) as err:
                    self.log('ERROR during shutdown of service connection: ', str(err), '\n')
                self.log('SERVER MESSAGE: Closing service-connection.')
                return

        if self.kill_switch or not self.connection.alive:
            await self.connection.cleanup()
            try:
                writer.write_eof()
                await writer.drain()
                writer.close()
            except (ConnectionError, OSError) as err:
                self.log('ERROR while exiting: ', str(err), '\n')
            self.log('SERVER MESSAGE: Closing connection: {}.\n\n'.format(id_connection))
            self.connection = None

        if self.kill_switch:
            # TODO: terminate processes and threads! Is this needed?
            # TODO: terminate all connections
            self.stage.value = SERVER_TERMINATING
            if sys.version_info >= (3, 7):
                await writer.wait_closed()
                assert self.serving_task
                self.serving_task.cancel()
            else:
                self.server.close()  # break self.server.serve_forever()
            if sys.version_info < (3, 7) and self.loop is not None:
                self.loop.stop()
            self.log('SERVER MESSAGE: Stopping server: {}.\n\n'.format(id_connection))
            self.kill_switch = False  # reset flag

    async def serve(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT):
        host, port = substitute_default_host_and_port(host, port)
        assert port >= 0
        self.stop_response = "DHParser server at {}:{} stopped!".format(host, port)
        self.host.value = host.encode()
        self.port.value = port
        self.loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
            else asyncio.get_event_loop()
        try:
            self.exec = ExecutionEnvironment(self.loop)
            self.exec.log_file = self.log_file
            self.server = cast(asyncio.AbstractServer,
                               await asyncio.start_server(self.handle, host, port))
            async with self.server:
                self.stage.value = SERVER_ONLINE
                # self.server_messages.put(SERVER_ONLINE)
                self.serving_task = asyncio.create_task(self.server.serve_forever())
                await self.serving_task
        finally:
            if self.server is not None and sys.version_info < (3, 8):
                await self.server.wait_closed()
            if self.exec:
                self.exec.shutdown()
                self.exec = None

    def serve_py35(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT, loop=None):
        host, port = substitute_default_host_and_port(host, port)
        assert port >= 0
        self.stop_response = "DHParser server at {}:{} stopped!".format(host, port)
        self.host.value = host.encode()
        self.port.value = port
        if loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        else:
            self.loop = loop
        assert self.loop is not None
        try:
            self.exec = ExecutionEnvironment(self.loop)
            self.exec.log_file = self.log_file
            self.server = cast(
                asyncio.base_events.Server,
                self.loop.run_until_complete(
                    asyncio.start_server(self.handle, host, port, loop=self.loop)))
            try:
                self.stage.value = SERVER_ONLINE
                # self.server_messages.put(SERVER_ONLINE)
                self.loop.run_forever()
            finally:
                self.server.close()
                try:
                    self.loop.run_until_complete(self.server.wait_closed())
                finally:
                    try:
                        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
                    finally:
                        asyncio.set_event_loop(None)
                        self.loop.close()
                        self.loop = None
        finally:
            if self.exec:
                self.exec.shutdown()
                self.exec = None

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
               blocking: Set[str] = set(),
               cn_callback: ConnectionCallback = connection_cb_dummy,
               name: str = '',
               strict_lsp: bool = True):
    """Start a server and wait until server is closed."""
    server = Server(rpc_functions, cpu_bound, blocking, cn_callback, name, strict_lsp)
    server.run_server(host, port)


def dummy_server(s: str) -> str:
    return s


def spawn_server(host: str = USE_DEFAULT_HOST,
                 port: int = USE_DEFAULT_PORT,
                 parameters: Union[Tuple, Callable] = dummy_server) -> Process:
    """
    Start DHParser-Server in a separate process and return. Can be used
    for writing test code. WARNING: Does not seem to work with
    `multiprocessing.set_start_method('spawn')` under linux !?
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
        _, writer = await asyncio_connect(host, port)  # wait until server online
        writer.close()
        # if sys.version_info >= (3, 7):
        #     await writer.wait_closed()

    global python_interpreter_name_cached
    host, port = substitute_default_host_and_port(host, port)
    null_device = " >/dev/null" if platform.system() != "Windows" else " > NUL"
    interpreter = sys.executable
    # 'python3' if os.system('python3 -V' + null_device) == 0 else 'python'
    # interpreter = '/home/eckhart/.local/bin/python3.8'
    # interpreter = "pypy3"
    logging = ''  # type: str
    if is_logging() and get_config_value('log_server'):
        logging = LOGGING_BLOCK.format(LOGDIR=get_config_value('log_dir').replace('\\', '\\\\'),
                                       ECHO=get_config_value('echo_server_log'))
    run_server_script = RUN_SERVER_SCRIPT_TEMPLATE.format(
        HOST=host, PORT=port, INITIALIZATION=initialization, LOGGING=logging,
        PARAMETERS=parameters, IMPORT_PATH=import_path.replace('\\', '\\\\'))
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
            writer.write(STOP_SERVER_REQUEST_BYTES)
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


def lsp_candidates(cls: Any, prefix: str = 'lsp_') -> Iterator[str]:
    """Returns an iterator over all method names from a class that either
    have a certain prefix or, if no prefix was given, all non-special and
    non-private-methods of the class."""
    assert not prefix.startswith('_')
    if prefix:
        # return [fn for fn in dir(cls) if fn.startswith(prefix) and callable(getattr(cls, fn))]
        for fn in dir(cls):
            if fn.startswith(prefix) and callable(getattr(cls, fn)):
                yield fn
    else:
        # return [fn for fn in dir(cls) if not fn.startswith('_') and callable(getattr(cls, fn))]
        for fn in dir(cls):
            if not fn.startswith('_') and callable(getattr(cls, fn)):
                yield fn


def gen_lsp_name(func_name: str, prefix: str = 'lsp_') -> str:
    """Generates the name of an lsp-method from a function name,
    e.g. "lsp_S_cacelRequest" -> "$/cancelRequest" """
    assert func_name.startswith(prefix)
    return func_name[len(prefix):].replace('_', '/').replace('S/', '$/')


# def get_lsp_methods(cls: Any, prefix: str= 'lsp_') -> List[str]:
#     """Returns the language-server-protocol-method-names from class `cls`.
#     Methods are selected based on the prefix and their name converted in
#     accordance with the LSP-specification."""
#     return [gen_lsp_name(fn, prefix) for fn in lsp_candidates(cls, prefix)]


def gen_lsp_table(lsp_funcs_or_instance: Union[Iterable[Callable], Any],
                  prefix: str = 'lsp_') -> RPC_Table:
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
    if isinstance(lsp_funcs_or_instance, Iterable):
        assert all(callable(func) for func in lsp_funcs_or_instance)
        rpc_table = {gen_lsp_name(func.__name__, prefix): func for func in lsp_funcs_or_instance}
    # assume lsp_funcs_or_instance is the instance of a class
    cls = lsp_funcs_or_instance
    rpc_table = {gen_lsp_name(fn, prefix): getattr(cls, fn) for fn in lsp_candidates(cls, prefix)}
    return rpc_table
