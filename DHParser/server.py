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

from __future__ import annotations

import asyncio
from concurrent.futures import Future, Executor, ThreadPoolExecutor, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
try:
    from concurrent.futures.thread import BrokenThreadPool
except ImportError:
    # BrokenThreadPool requires Python version >= 3.8
    class BrokenThreadPool(Exception):
        pass
from datetime import datetime
from functools import partial
import inspect
import io
import json
from multiprocessing import Process, Value, Array
import os
import subprocess
import sys
import threading
from threading import Thread
import time
import traceback
from typing import Callable, Coroutine, Awaitable, Optional, Union, Dict, List, Tuple, Sequence, \
    Set, Any, cast, Type, TypeVar

from DHParser.configuration import access_thread_locals, get_config_value
from DHParser.nodetree import DHParser_JSONEncoder
from DHParser.log import create_log, append_log, is_logging, log_dir
from DHParser.toolkit import re, re_find, JSON_Type, JSON_Dict, JSONstr, JSONnull, \
    json_encode_string, json_rpc, json_dumps, identify_python, normalize_docstring, md5, \
    is_html_name, TypeAlias
from DHParser.versionnumber import __version__


__all__ = ('RPC_Table',
           'RPC_Type',
           'RPC_Error_Type',
           'ConnectionCallback',
           'RX_CONTENT_LENGTH',
           'RE_DATA_START',
           'JSONRPC_HEADER_BYTES',
           'SERVER_ERROR',
           'SERVER_OFFLINE',
           'SERVER_STARTING',
           'SERVER_ONLINE',
           'SERVER_TERMINATING',
           'USE_DEFAULT_HOST',
           'USE_DEFAULT_PORT',
           'STOP_SERVER_REQUEST_BYTES',
           'IDENTIFY_REQUEST',
           'IDENTIFY_REQUEST_BYTES',
           'LOGGING_REQUEST',
           'INFO_REQUEST',
           'SERVE_REQUEST',
           'SERVER_REPLY_TIMEOUT',
           'ALL_RPCs',
           'rpc_entry_info',
           'rpc_table_info',
           'pp_json',
           'pp_json_str',
           'asyncio_run',
           'asyncio_connect',
           'split_header',
           'ExecutionEnvironment',
           'Connection',
           'connection_cb_dummy',
           'Server',
           'probe_tcp_server',
           'spawn_tcp_server',
           'stop_tcp_server',
           'has_server_stopped')


RPC_Table: TypeAlias = Dict[str, Callable]
RPC_Type: TypeAlias = Union[RPC_Table, List[Callable], Callable]
RPC_Error_Type: TypeAlias = Optional[Tuple[int, str]]
BytesType: TypeAlias = Union[bytes, bytearray]
ConnectionCallback: TypeAlias = Callable[['Connection'], None]

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
Content-Type: {mime}; charset=utf-8
X-Pad: avoid browser bug

'''

JSONRPC_HEADER_BYTES = b'''Content-Length: %i\r\n\r\n'''
JSONRPC_HEADER = '''Content-Length: %i\r\n\r\n'''

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en" xml:lang="en">
<head>
  <meta charset="utf-8" />
</head>
<body>
<h1>{heading}</h1>
{content}
</body>
</html>
'''

UNKNOWN_FUNC_HTML = HTML_TEMPLATE.format(
    heading="DHParser Error: Function &ldquo;{func}&rdquo; unknown or not registered!",
    content='')

USE_DEFAULT_HOST = ''
USE_DEFAULT_PORT = -1

STOP_SERVER_REQUEST = "__STOP_SERVER__"
STOP_SERVER_REQUEST_BYTES = b"__STOP_SERVER__"
IDENTIFY_REQUEST = "identify()"
IDENTIFY_REQUEST_BYTES = b"identify()"
INFO_REQUEST = "info()"
SERVE_REQUEST = "serve()"
LOGGING_REQUEST = "logging('')"

SERVER_REPLY_TIMEOUT = 3  # seconds


def substitute_default_host_and_port(host, port):
    """Substiutes the default value(s) from the configuration file if host
     or port ist ``USE_DEFAULT_HOST`` or ``USE_DEFAULT_PORT``. """
    if host == USE_DEFAULT_HOST:
        host = get_config_value('server_default_host')
    if port == USE_DEFAULT_PORT:
        port = int(get_config_value('server_default_port'))
    return host, port


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
        if s[:1] in ('"', "'"):
            return s.strip('" \'')
        else:
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return s


def pp_json(obj: JSON_Type, *, cls=json.JSONEncoder) -> str:
    """Returns json-object as pretty-printed string. Other than the standard-library's
    `json.dumps()`-function `pp_json` allows to include already serialized
    parts (in the form of JSONStr-objects) in the json-object. Example::

    :param obj: A json-object (or a tree of json-objects) to be serialized
    :param cls: The class of a custom json-encoder derived from `json.JSONEncoder`
    :return: The pretty-printed string-serialized form of the json-object.
    """
    custom_encoder = cls()

    def serialize(obj, indent: str) -> List[str]:
        if isinstance(obj, str):
            if obj.find('\n') >= 0:
                lines = obj.split('\n')
                pretty_str = json_encode_string(lines[0]) + '\n' \
                    + '\n'.join(indent + json_encode_string(line) for line in lines[1:])
                return [pretty_str]
            else:
                return [json_encode_string(obj)]
        elif isinstance(obj, dict):
            if obj:
                if len(obj) == 1:
                    k, v = next(iter(obj.items()))
                    if not isinstance(v, (dict, list, tuple)):
                        r = ['{"' + k + '": ']
                        r.extend(serialize(v, indent + '  '))
                        r.append('}')
                        return r
                r = ['{\n' + indent + '  ']
                for k, v in obj.items():
                    r.append('"' + k + '": ')
                    r.extend(serialize(v, indent + '  '))
                    r.append(',\n' + indent + '  ')
                r[-1] = '}'
                return r
            return ['{}']
        elif isinstance(obj, (list, tuple)):
            if obj:
                r = ['[']
                for item in obj:
                    r.extend(serialize(item, indent + '  '))
                    r.append(',')
                r[-1] = ']'
                return r
            return ['[]']
        elif obj is True:
            return ['true']
        elif obj is False:
            return ['false']
        elif obj is None:
            return ['null']
        elif isinstance(obj, (int, float)):
            # NOTE: test for int must follow test for bool, because True and False
            #       are treated as instances of int as well by Python
            return [repr(obj)]
        elif isinstance(obj, JSONstr):
            return [obj.serialized_json]
        elif isinstance(obj, JSONnull) or obj is JSONnull:
            return ['null']
        return serialize(custom_encoder.default(obj), indent)

    return ''.join(serialize(obj, ''))


def pp_json_str(jsons: str) -> str:
    """Pretty-prints and already serialized (but possibly ugly-printed)
    json object in a well-readable form. Syntactic sugar for:
    `pp_json(json.loads(jsons))`."""
    return pp_json(json.loads(jsons))


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
                    myloop.run_until_complete(myloop.shutdown_asyncgens())
                except AttributeError:
                    pass
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
    save_error = ConnectionError  # type: Union[Type[ConnectionError], ConnectionRefusedError, OSError]
    OSError_countdown = 10
    while not connected and delay < retry_timeout:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            delay = retry_timeout
            connected = True
        except ConnectionRefusedError as error:
            save_error = error
            if delay > 0.0:
                await asyncio.sleep(delay)
                delay *= 1.5
            else:
                delay = retry_timeout  # exit while loop
        except OSError as error:
            # workaround for strange erratic OSError (MacOS only?)
            OSError_countdown -= 1
            if OSError_countdown < 0:
                save_error = error
                delay = retry_timeout
            else:
                await asyncio.sleep(0)

    if connected and reader is not None and writer is not None:
        return reader, writer
    else:
        raise save_error


def GMT_timestamp() -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())


ALL_RPCs = set('*')  # Magic value denoting all remote procedures


def _func_info(name: str, func: Callable, html: bool) -> List[str]:
    """Internal function to extract signature and docstring from
    a function."""
    info = []
    if not name:  name = func.__name__
    info.append(name + str(inspect.signature(func)))
    if html:  info[-1] = '<b>' + info[-1] + '</b>'
    docstr = normalize_docstring(getattr(func, '__doc__', '') or '')
    if html:  docstr = '<br/>\n'.join(docstr.split('\n'))
    if docstr:
        info.extend(['', docstr, '', ''])
    else:
        info.append('')
    return info


def _merge_info(info: List[str], html: bool) -> str:
    """Interrnal function to merge function infos into
    a string, omitting trailing empty lines."""
    while info and not info[-1]:  info.pop()
    if html:
        return '\n'.join(['<samp>', '<br/>\n'.join(info), '</samp>'])
    return '\n'.join(info)


def rpc_entry_info(name: str, rpc_table: RPC_Table, html: bool=False) -> str:
    """Returns the name, signature and doc-string of a function in the
    rpc-table as string or HTML-snippet."""
    info = _func_info(name, rpc_table[name], html)
    return _merge_info(info, html)


def rpc_table_info(rpc_table: RPC_Table, html: bool=False) -> str:
    """Returns the names, function signatures and doc-string of all
    functions in the `rpc_table` as a (more or less) well-formatted
    string or as HTML-snippet."""
    info = []
    for name, func in rpc_table.items():
        info.extend(_func_info(name, func, html))
    while info and not info[-1]:  info.pop()
    return _merge_info(info, html)


def default_fallback(*args, **kwargs) -> str:
    return 'No default RPC-function defined!'


def http_response(html: Union[str, bytes], mime_type: str = 'text/html') -> bytes:
    """Embeds an HTML-string in a http header and returns the http-package
    as byte-string.
    """
    gmt = GMT_timestamp()
    if isinstance(html, str):
        encoded_html = html.encode()
    elif isinstance(html, bytes):
        encoded_html = html
    else:
        encoded_html = ("Illegal type %s for response %s. Only str allowed!" \
                        % (str(type(html)), str(html))).encode()
        mime_type = 'text/html'
    response = HTTP_RESPONSE_HEADER.format(date=gmt, length=len(encoded_html), mime=mime_type)
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


def strip_header_delimiter(data: bytes) -> Tuple[str, ...]:
    i = max(data.find(b'\n'), data.find(b'\r'))
    if i >= 0:
        return data[:i].rstrip().decode(), '\n', data[i:].lstrip().decode()
    else:
        return data.decode(),


def pp_transmission(data: bytes) -> Tuple[str, ...]:
    t = strip_header_delimiter(data)
    try:
        pp_str = pp_json_str(t[-1])
    except json.decoder.JSONDecodeError:
        pp_str = t[-1]
    return t[:-1] + (pp_str,)


def gen_task_id() -> int:
    """Generate a unique task id. This is always a negative number to
    distinguish the task id's from the json-rpc ids.
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

    :ivar process_executor:  A process-pool-executor for cpu-bound tasks
    :ivar thread_executor:   A thread-pool-executor for blocking tasks
    :ivar submit_pool:  A secondary process-pool-executor to submit tasks
        synchronously and thread-safe.
    :ivar submit_ppol_lock:  A threading.Lock to ensure that submissions to
        the submit_pool will be thread_safe
    :ivar loop:  The asynchronous event loop for running coroutines
    :ivar log_file:  The name of the log-file to which error messages are
        written if an executor raises a Broken-Error.
    :ivar _closed:  A Flag that is set to True after the `shutdown-method
        has been called. After that any call to the `execute()`-method
        yields an error.
    """
    def __init__(self, event_loop: asyncio.AbstractEventLoop):
        self._process_executor = None                  # type: Optional[ProcessPoolExecutor]
        self._thread_executor = None                   # type: Optional[ThreadPoolExecutor]
        self._submit_pool = None                       # type: Optional[ProcessPoolExecutor]
        self.submit_pool_lock = threading.Lock()       # type: threading.Lock
        self.loop = event_loop                         # type: asyncio.AbstractEventLoop
        self.log_file = ''                             # type: str
        self._closed = False                           # type: bool

    def __del__(self):
        self.shutdown(False)

    @property
    def process_executor(self):
        if self._process_executor is None:
            with self.submit_pool_lock:
                if self._process_executor is None:
                    self._process_executor = ProcessPoolExecutor()
        return self._process_executor

    @property
    def thread_executor(self):
        if self._thread_executor is None:
            with self.submit_pool_lock:
                if self._thread_executor is None:
                    self._thread_executor = ThreadPoolExecutor()
        return self._thread_executor

    @property
    def submit_pool(self):
        if self._submit_pool is None:
            with self.submit_pool_lock:
                if self._submit_pool is None:
                    self._submit_pool = ProcessPoolExecutor()
        return self._submit_pool

    async def execute(self, executor: Optional[Executor],
                      method: Callable,
                      params: Union[dict, tuple, list])\
            -> Tuple[Union[JSON_Type, BytesType], Optional[RPC_Error_Type]]:
        """Executes a method with the given parameters in a given executor
        (``ThreadPoolExcecutor`` or ``ProcessPoolExecutor``). ``execute()`` waits
        for the completion and returns the JSON result and an RPC error tuple (see
        the type definition above). The result may be None and the error may be
        zero, i.e. no error. If `executor` is `None` the method will be called
        directly instead of deferring it to an executor.
        """
        if self._closed:
            return None, (-32000,
                          "Server Error: Execution environment has already been shut down! "
                          "Cannot process method {} with parameters {} any more."
                          .format(method, params))
        result = None      # type: Optional[Union[JSON_Type, BytesType]]
        rpc_error = None   # type: Optional[RPC_Error_Type]
        if params is None:
            params = tuple()
        if isinstance(params, dict):
            executable = partial(method, **params)
        elif isinstance(params, (tuple, list)):
            executable = partial(method, *params)
        else:
            rpc_error = -32040, "Invalid parameter type %s for %s. Must be Dict or Sequence" \
                        % (str(type(params)), str(params))
            return result, rpc_error
        try:
            if executor is None:
                result = (await executable()) if asyncio.iscoroutinefunction(method) \
                    else executable()
            else:
                result = await self.loop.run_in_executor(executor, executable)
        except TypeError as e:
            stacktrace = traceback.format_exc()
            rpc_error = -32602, f"Invalid Params: {e}\n{stacktrace}"
            append_log(self.log_file, rpc_error[1])
        except NameError as e:
            stacktrace = traceback.format_exc()
            rpc_error = -32601, f"Method not found: {e}\n{stacktrace}"
            append_log(self.log_file, rpc_error[1])
        except BrokenProcessPool as e:
            if self.log_file:
                append_log(self.log_file, 'WARNING: Broken ProcessPoolExecutor detected. '
                           'Starting a new ProcessPoolExecutor', echo=True)
            try:
                # restart process pool and try again once
                self.process_executor.shutdown(wait=True)
                self._process_executor = ProcessPoolExecutor()
                result = await self.loop.run_in_executor(executor, executable)
            except BrokenProcessPool as e:
                rpc_error = -32050, str(e)
        except BrokenThreadPool as e:
            if self.log_file:
                append_log(self.log_file, 'WARNING: Broken ThreadPoolExecutor detected. '
                           'Starting a new ThreadPoolExecutor', echo=True)
            try:
                # restart thread pool and try again once
                self.thread_executor.shutdown(wait=True)
                self._thread_executor = ThreadPoolExecutor()
                result = await self.loop.run_in_executor(executor, executable)
            except BrokenThreadPool as e:
                rpc_error = -32060, str(e)
        except Exception as e:
            stacktrace = traceback.format_exc()
            rpc_error = -32000, "Server Error %s: %s\n%s" % (str(type(e)), str(e), stacktrace)
            append_log(self.log_file, rpc_error[1])
        return result, rpc_error

    def submit_as_process(self, func, *args) -> Future:
        """Submits long running function to the secondary process-pool.
        Other than `execute()` this works synchronously and thread-safe.
        """
        if self.submit_pool is None:
            self._submit_pool = ProcessPoolExecutor()
        with self.submit_pool_lock:
            future = self.submit_pool.submit(func, *args)
        return future

    def shutdown(self, wait: bool = True):
        """Shuts the thread and process executor of the execution environment. The
        wait parameter is passed to the shutdown-method of the thread and
        process-executor.
        """
        self._closed = True
        if self._thread_executor is not None:
            self._thread_executor.shutdown(wait=wait)
            self._thread_executor = None
        if self._process_executor is not None:
            self._process_executor.shutdown(wait=wait)
            self._process_executor = None
        if self._submit_pool is not None:
            self._submit_pool.shutdown(wait=wait)
            self._submit_pool = None


class StreamReaderProxy:
    """StreamReaderProxy simulates an asyncio.StreamReader that sends
    and receives data through an io.IOBase-Stream.

    see: https://stackoverflow.com/questions/52089869/how-to-create-asyncio-stream-reader-writer-for-stdin-stdout
    """

    def __init__(self, io_reader: io.IOBase):
        try:
            self.buffered_io = io_reader.buffer
        except AttributeError:
            self.buffered_io = io_reader
        self.loop = None    # type: Optional[asyncio.AbstractEventLoop]
        self.exec = None    # type: Optional[Executor]
        self.max_data_size = get_config_value('max_rpc_size')
        self._eof = False   # type: bool

    def feed_eof(self):
        self._eof = True
        self.buffered_io.close()

    def at_eof(self) -> bool:
        try:
            return self.buffered_io.closed
        except AttributeError:
            return self._eof
    #
    # async def readline(self) -> bytes:
    #     try:
    #         return await self.loop.run_in_executor(None, self.buffered_io.readline)
    #     except AttributeError:
    #         self.loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
    #             else asyncio.get_event_loop()
    #         return await self.loop.run_in_executor(None, self.buffered_io.readline)

    async def _read(self, n=-1) -> bytes:
        if self._eof:
            return b''
        if 1 <= n < self.max_data_size:
            return await self.loop.run_in_executor(self.exec, self.buffered_io.read, n)
            # return self.buffered_io.read(n)
        else:
            data = await self.loop.run_in_executor(self.exec, self.buffered_io.readline)
            # if len(data) > 0:
            #     data += await self.loop.run_in_executor(self.exec, self.buffered_io.readline)
            #     # data += self.buffered_io.readline()
            if len(data) <= 0:
                self.feed_eof()
            return data

    async def read(self, n=-1) -> bytes:
        try:
            return await self._read(n)
        except AttributeError:
            self.loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            return await self._read(n)


StreamReaderType = Union[asyncio.StreamReader, StreamReaderProxy]


async def read_full_block(reader: StreamReaderType) -> Tuple[int, bytes, bytes]:
    """Reads a block from a reader, where block may start with a header
    containing a "Content-Length"-field. if this is the case, read_block
    tries to read exactly the number of bytes specified.

    :param reader: The reader from which the data shall be read.
    :return: A 3-tuple (header_size, data, backlog). header_size is the
        length in bytes of the header or 0 if there is no header, data
        ist the data block including the header and backlog is any data
        that exceeds the specified content-length and that has been
        delivered by the reader even though it has not been requested.
    """
    data = await reader.read()
    backlog = b''
    i = data.find(b'Content-Length:', 0, 512)
    m = RX_CONTENT_LENGTH.match(data, i, i + 100) if i >= 0 else None
    while not m and incomplete_header(data) and not reader.at_eof():
        data += await reader.read()
        i = data.find(b'Content-Length:', 0, 512)
        m = RX_CONTENT_LENGTH.match(data, i, i + 100) if i >= 0 else None
    if m:
        content_length = int(m.group(1))
        m2 = re_find(data, RE_DATA_START)
        while not m2 and not reader.at_eof():
            data += await reader.read()
            m2 = re_find(data, RE_DATA_START)
        if m2:
            header_size = m2.end()
            missing = header_size + content_length - len(data)
            if missing > 0:
                data += await reader.read(missing)
                backlog = data[header_size + content_length:]
        else:
            header_size = 0
    else:
        header_size = 0
    return header_size, data, backlog


class StreamWriterProxy:
    """StreamWriterProxy simulates an asyncio.StreamWriter that sends
    and receives data through an io.IOBase-Stream.

    see: https://stackoverflow.com/questions/52089869/how-to-create-asyncio-stream-reader-writer-for-stdin-stdout
    """

    def __init__(self, io_writer: io.IOBase):
        try:
            self.buffered_io = io_writer.buffer
        except AttributeError:
            self.buffered_io = io_writer
        self.buffer = []
        self.loop = None    # type: Optional[asyncio.AbstractEventLoop]
        self.exec = None    # type: Optional[Executor]

    def write(self, data: bytes):
        assert isinstance(data, bytes)
        self.buffer.append(data)

    def can_write_eof(self) -> bool:
        # return False
        return True

    def write_eof(self):
        data, self.buffer = self.buffer, []
        try:
            self.buffered_io.writelines(data)
            self.buffered_io.flush()
        except ValueError:
            pass
        self.buffered_io.close()

    def close(self):
        # if not self.buffered_io.closed:
        self.write_eof()

    async def wait_closed(self):
        assert self.buffered_io.closed, "buffer is not even closing!"

    def _drain(self, data: List[str]):
        self.buffered_io.writelines(data)
        self.buffered_io.flush()

    async def drain(self):
        data, self.buffer = self.buffer, []
        if data:
            try:
                await self.loop.run_in_executor(self.exec, self._drain, data)
            except AttributeError:
                self.loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                    else asyncio.get_event_loop()
                await self.loop.run_in_executor(self.exec, self._drain, data)


StreamWriterType = Union[asyncio.StreamWriter, StreamWriterProxy]


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
    def __init__(self, reader: StreamReaderType,
                 writer: StreamWriterType,
                 exec_env: ExecutionEnvironment):
        self.alive = True                # type: bool
        self.reader = reader             # type: StreamReaderType
        self.writer = writer             # type: StreamWriterType
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
        task = asyncio.create_task(coroutine) if sys.version_info >= (3, 7) \
            else asyncio.ensure_future(coroutine)
        self.active_tasks[json_id] = task
        return task

    def task_done(self, json_id: int):
        assert json_id in self.active_tasks
        self.finished_tasks.add(json_id)
        # do not do: del self.active_tasks[json_id] !!!

    async def cleanup(self):
        open_tasks = {task for idT, task in self.active_tasks.items()
                      if idT not in self.finished_tasks}
        if open_tasks:
            _, pending = await asyncio.wait(open_tasks, timeout=3.0)  # type: Set[asyncio.Future], Set[asyncio.Future]
            for task in pending:
                task.cancel()
            # wait for task's cancellation to actually finish
            await asyncio.gather(*pending, return_exceptions=True)
        self.active_tasks = dict()
        self.finished_tasks = set()

    # server initiated LSP-calls-support

    def put_response(self, json_obj: JSON_Type):
        """Adds a client-response to the waiting queue. The responses
        to a particular task can be queried with the `client_response()`-
        coroutine."""
        # # Already logged as received message
        # if self.log_file:
        #     self.log('RESULT: ', json_dumps(json_obj), '\n')
        assert self.response_queue is not None
        self.response_queue.put_nowait(json_obj)

    async def _server_call(self, method: str, params: JSON_Type, ID: Optional[int]):
        """Issues a json-rpc call from the server to the client."""
        json_str = json_rpc(method, params, ID)
        self.log('SERVER NOTIFICATION: ' if ID is None else 'SERVER REQUEST: ',
                 pp_json_str(json_str), '\n\n')
        request = json_str.encode()
        # self.writer.write(JSONRPC_HEADER_BYTES % len(request))
        # sefl.writer.write(request)
        request = JSONRPC_HEADER_BYTES % len(request) + request
        self.writer.write(request)
        await self.writer.drain()

    async def server_notification(self, method: str, params: JSON_Type = []):
        await self._server_call(method, params, None)

    async def server_request(self, method: str, params: JSON_Type, ID: int):
        await self._server_call(method, params, ID)

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
        was called on an uninitialized language server.
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
        elif strict and method not in (STOP_SERVER_REQUEST, IDENTIFY_REQUEST):
            if self.lsp_shutdown:
                return -32600, 'language server already shut down'
            elif self.lsp_initialized != LSP_INITIALIZED:
                return -32002, 'language server not initialized'
        return None

    # logging support

    def log(self, *args):
        if self.log_file:
            append_log(self.log_file, *args, echo=self.echo_log)


def pick_value(rpc: bytes, key: bytes) -> Optional[Value]:
    i = rpc.find(key)
    if i < 0:  return None
    i = rpc.find(b':', i)
    if i < 0: return None
    k = rpc.find(b',', i)
    if k < 0:
        k = rpc.find(b'}', i)
        if k < 0: return None
    a = rpc.find(b'"', i, k)
    if a < 0:
        a = i + 1
        b = k
    else:
        a += 1
        b = rpc.find(b'"', a)
        if b < 0: return None
    return rpc[a:b]


class LogFilter:
    """A filter for logging json-rpc-messages."""
    def __init__(self,
                 allow_methods: Set[str] = frozenset(),
                 forbid_methods: Set[str] = frozenset()):
        self.configure(allow_methods, forbid_methods)

    def configure(self,
                  allow_methods: Set[str] = frozenset(),
                  forbid_methods: Set[str] = frozenset()):
        self.allow: Set[bytes] = {bytes(s.strip('"'), encoding='utf-8') for s in allow_methods}
        self.forbid: Set[bytes] = {bytes(s.strip('"'), encoding='utf-8') for s in forbid_methods}
        self.forbid_ids: Set[int] = set()

    def pick_id(self, rpc: bytes) -> Optional[int]:
        try:
            rpc_id = int(pick_value(rpc, b'"id"'))
        except (ValueError, TypeError):
            rpc_id = None
        return rpc_id

    def block_id(self, rpc: bytes):
        rpc_id = self.pick_id(rpc)
        if rpc_id:
            self.forbid_ids.add(rpc_id)

    def id_was_blocked(self, rpc: bytes) -> bool:
        rpc_id = self.pick_id(rpc)
        if rpc_id in self.forbid_ids:
            self.forbid_ids.remove(rpc_id)
            return True
        return False

    def can_pass(self, rpc_data: BytesType) -> bool:
        rpc = bytes(rpc_data)
        if rpc.find(b'"jsonrpc"') >= 0:
            method = pick_value(rpc, b'"method"')
            if method:
                if self.allow:
                    if method in self.allow:
                        return True
                    else:
                        self.block_id(rpc)
                        return False
                else:
                    if method in self.forbid:
                        self.block_id(rpc)
                        return False
                    else:
                        return True
            else:
                return not self.id_was_blocked(rpc)
        return True

def connection_cb_dummy(connection: Connection) -> None:
    pass


class Server:
    """Class Server contains all the boilerplate code for a
    Language-Server-Protocol-Server. Class Server should be
    considered final, i.e. do not derive from this class to add
    LSP-functionality, rather implement the lsp_functionality in
    a dedicated class (or set of functions) and pass the
    LSP-functionality via the rpc_functions-parameter to the
    constructor of this class.

    :ivar server_name: A name for the server. Defaults to
        `CLASSNAME_OBJECTID`
    :ivar strict_lsp: Enforce Language-Server-Protocol on json-rpc-calls.
        If `False` json-rpc calls will be processed even without prior
        initialization, just like plain data or http calls.
    :ivar cpu_bound: Set of function names of functions that are cpu-bound
        and will be run in separate processes.
    :ivar blocking: Set of functions that contain blocking calls
        (e.g. IO-calls) and will therefore be run in separate threads.
    :ivar rpc_table: Table mapping LSP-method names to Python functions
    :ivar known_methods: Set of all known LSP-methods. This includes the
        methods in the rpc-table and the four initialization methods,
        `initialize()`, `initialized()`, `shutdown()`, `exit`
    :ivar connection_callback: A callback function that is called with the
        connection object as argument when a connection to a client is
        established
    :ivar max_data_size: Maximal size of a data chunk that can be read by
        the server at a time.
    :ivar stage:  The operation stage, the server is in. Can be on of the four
        values: `SERVER_OFFLINE`, `SERVER_STARTING`, `SERVER_ONLINE`,
        `SERVER_TERMINATING`
    :ivar host: The host, the server runs on, e.g. "127.0.0.1"
    :ivar port: The port of the server, e.g. 8890
    :ivar server: The asyncio.Server if the server is online, or `None`.
    :ivar serving_task: The task in which the asyncio.Server is run.
    :ivar stop_response:  The response string that is written to the stream
        as answer to a stop request.
    :ivar service_calls:  A set of names of functions that can be called
        as "service calls" from a second connection, even if another
        connection is still open.
    :ivar echo_log: Read from the global configuration. If True, any log
        message will also be echoed on the console.
    :ivar log_file: The file-name of the server-log.
    :ivar log_filter: A filter to allow or block logging of specific
        json-rpc calls.
    :ivar use_jsonrpc_header: Read from the global configuration. If True,
        jsonrpc-calls or responses will always be preceeded by a simple header
        of the form: `Content-Length: {NUM}\\n\\n`, where `{NUM}`
        stands for the byte-size of the rpc-package.
    :ivar exec: An instance of the execution environment that delegates tasks
        to separate processes, threads, asynchronous tasks or simple function
        calls.
    :ivar connection: An instance of the connection class representing the
        data of the current connection or None, if there is no connection at
        the moment. There can be only one connection to the server at a time!
    :ivar kill_switch: If True, the server will be shut down.
    :ivar loop: The asyncio event loop within which the asyncio stream server
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
        self.cpu_bound = set(self.rpc_table.keys()) if cpu_bound == ALL_RPCs else cpu_bound
        self.blocking = set(self.rpc_table.keys()) if blocking == ALL_RPCs else blocking
        self.blocking -= self.cpu_bound  # cpu_bound property takes precedence

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
        self.server = None          # type: Optional[asyncio.AbstractServer]
        self.serving_task = None    # type: Optional[asyncio.Task]
        self.stop_response = ''     # type: str
        self.service_calls = set()  # type: Set[str]

        self.register_service_rpc(IDENTIFY_REQUEST, self.rpc_identify_server)
        self.register_service_rpc(LOGGING_REQUEST, self.rpc_logging)
        self.register_service_rpc(INFO_REQUEST, self.rpc_info)
        self.register_service_rpc(SERVE_REQUEST, self.rpc_serve_page)

        self.exec = None            # type: Optional[ExecutionEnvironment]
        self.connection = None      # type: Optional[Connection]
        self.kill_switch = False    # type: bool
        self.loop = None            # type: Optional[asyncio.AbstractEventLoop]

        self.known_methods = set(self.rpc_table.keys()) | \
            {'initialize', 'initialized', 'shutdown', 'exit'}  # see self.verify_initialization()

        self._echo_log = get_config_value('echo_server_log')  # type: bool
        self.use_jsonrpc_header = get_config_value('jsonrpc_header')  # type: bool
        self._log_file = ''       # type: str
        self.log_filter = LogFilter()
        if get_config_value('log_server'):
            self.start_logging()

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
        if self.connection:
            if isinstance(self.connection.writer, StreamWriterProxy):
                # echoing log messages to the console does not work with stream connections,
                # because the echo stream is the same as the writer of the connection.
                value = False
            self.connection.echo_log = value
        self._echo_log = value


    def register_service_rpc(self, name, method):
        """Registers a service request, i.e. a call that will be accepted from
        a second connection. Otherwise, requests coming from a new connection
        if a connection has already been established, will be rejected, because
        language servers only accept one client at a time."""
        name = name[:name.find('(')]
        if name in self.rpc_table:
            self.log('Service {} is shadowed by an rpc-call with the same name.'.format(name))
        else:
            self.rpc_table[name] = method
            self.service_calls.add(name)

    def start_logging(self, filename: str = "") -> str:
        """Starts logging to a file. If `filename` is void or a directory
        an auto-generated file name will be used. The file will be written
        to the standard log-dir, unless a path is specified in filename."""
        date_time = time.localtime()[:5]
        def log_name():
            """Returns an auto-generated log-name."""
            # return self.server_name + '_' + hex(id(self))[2:] + '.log'
            return self.server_name + '_%04i%02i%02i_%02i%02i' % date_time + '.log'
        if not filename or os.path.isdir(filename) or filename.endswith(os.path.sep):
            filename = os.path.join(filename, log_name())
        else:
            if not filename:
                filename = log_name()
            if not os.path.dirname(filename) and not log_dir():
                filename = os.path.join('.', filename)
        self.log_file = create_log(filename)
        if self.log_file:
            self.log("Log started on %i-%i-%i at %i:%i o'clock\n\n" % date_time)
            self.log('Python Version: %s\nDHParser Version: %s\n\n'
                     % (sys.version.replace('\n', ' '), __version__))
            return 'Started logging to file: "%s"' % self.log_file
        return 'Unable to write log-file: "%s"' % filename

    def stop_logging(self):
        """Stops logging."""
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

    def rpc_identify_server(self, service_call: bool = False, html: bool = False, *args, **kwargs):
        """Returns an identification string for the server."""
        identify = "DHParser %s %s under %s" \
                   % (__version__, self.server_name, identify_python())
        return (identify + ' already connected') if service_call else identify

    def rpc_logging(self, *args, **kwargs) -> str:
        """Starts logging with either a) the default filename, if args is
         empty or the empty string; or b) the given log file name if `args[0]`
         is a non-empty string; or c) stops logging if `args[0]` is `None`.
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

    def rpc_info(self, service_call: bool = False, html: bool = False,
                 *args, **kwargs) -> str:
        """Returns information on the implemented LSP- and service-functions."""
        info = rpc_table_info(self.rpc_table, html)
        if html:
            return HTML_TEMPLATE.format(heading=f'{self.server_name} API:', content=info)
        return info

    def rpc_serve_page(self, file_path: str,
                       service_call: bool = False, html: bool = False,
                       *args, **kwargs) -> Union[str, bytes]:
        """Loads and returns the HTML page or other files stored in file `file_path`"""
        def error(err_desc: str, details: str = '') -> str:
            return HTML_TEMPLATE.format(heading=err_desc, content=details)

        i = file_path.find(':')
        if i >= 0:
            chksum = file_path[:i]
            file_path = file_path[i + 1:]
        else:
            chksum = ''
        dirname, basename = os.path.split(file_path)
        allow_file = os.path.join(dirname, 'DHParser.allow')
        if not os.path.isfile(allow_file):
            return error(f'Access to "{file_path}" forbidden!',
                         '"DHParser.allow not found.')
        if not os.path.isfile(file_path):
            return error(f'Page "{file_path}" not found on.', '')
        with open(allow_file, 'r', encoding='utf-8') as f:
            lines = [l.split('=') for l in f.read().split('\n') if l.strip()]
        allow = { l[0].strip(): l[1].strip() for l in lines if len(l) == 2}
        if not chksum or allow[basename] != chksum:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:  page = f.read()
                if is_html_name(basename):
                    chksum = md5(page)
                    allow[basename] = chksum
                    with open(allow_file, 'w', encoding='utf-8') as f:
                        f.writelines(''.join([name, '=', chk, '\n'])
                                     for name, chk in allow.items())
                    page = re.sub('<body.*?>', f'<body chksum="{chksum}">', page)
            except UnicodeDecodeError:
                with open(file_path, 'rb') as f:  page = f.read()
            return page
        return ''  # empty string means that page has not changed

    async def run(self, method_name: str, method: Callable, params: Union[Dict, List, Tuple]) \
            -> Tuple[Optional[Union[JSON_Type, BytesType]], Optional[RPC_Error_Type]]:
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

    async def respond(self, writer: StreamWriterType, response: Union[str, BytesType]):
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
        if self.use_jsonrpc_header and response[:1] == b'{':
            response = JSONRPC_HEADER_BYTES % len(response) + response
        if self.log_file:  # avoid data decoding if logging is off
            timestamp = str(datetime.now())[11:-3]
            if self.log_filter.can_pass(response):
                self.log(f'RESPONSE {timestamp}: ', *pp_transmission(response), '\n\n')
        try:
            writer.write(response)
            await writer.drain()
        except ConnectionError as err:
            self.log('ERROR when writing data: ', str(err), '\n')
            if self.connection:
                self.connection.alive = False

    def amend_service_call(self, func_name: str, func: Callable, argument: Union[Tuple, Dict],
                           err_func: Callable, html: bool = False) \
            -> Tuple[Callable, Union[Tuple, Dict]]:
        if argument is None:
            argument = ()
        if getattr(func, '__self__', None) == self:
            if isinstance(argument, Dict):
                params = argument.copy()
                params.update({'service_call': True, 'html': html})
                return func, params
            else:
                return func, argument + (True, html)
        else:
            return err_func, {} if isinstance(argument, Dict) else ()

    async def handle_plaindata_request(self, task_id: int,
                                       reader: StreamReaderType,
                                       writer: StreamWriterType,
                                       data: BytesType,
                                       service_call: bool = False):
        """Processes a request in plain-data-format, i.e. neither http nor json-rpc"""
        try:
            header, data, _ = split_header(data)
        except ValueError:
            header = b''

        async def respond(response: Union[str, bytes, bytearray]):
            if header:
                HEADER = JSONRPC_HEADER if isinstance(response, str) else JSONRPC_HEADER_BYTES
                await self.respond(writer, HEADER % len(response) + response)
            else:
                await self.respond(writer, response)

        if len(data) > self.max_data_size:
            await respond("Data too large! Only %i MB allowed"
                          % (self.max_data_size // (1024 ** 2)))
        elif data.startswith(STOP_SERVER_REQUEST_BYTES):
            await respond(self.stop_response)
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
            rpc_error = None
            if service_call:
                if func_name in self.service_calls:
                    func, argument = self.amend_service_call(func_name, func, argument, err_func)
                else:
                    rpc_error = ('', f'Functions "{func_name}" has been requested from a "'
                                     f'second connection although it is not a service call!')
            if rpc_error is None:
                result, rpc_error = await self.run(func_name, func, argument)
            if rpc_error is None:
                if isinstance(result, (str, bytes, bytearray)):
                    await respond(result)
                elif result is not None:
                    try:
                        await respond(json_dumps(result, cls=DHParser_JSONEncoder))
                    except TypeError as err:
                        await respond(str(err))
            else:
                await respond(rpc_error[1])
        assert self.connection
        self.connection.task_done(task_id)

    async def handle_http_request(self, task_id: int,
                                  reader: StreamReaderType,
                                  writer: StreamWriterType,
                                  data: BytesType,
                                  service_call: bool = False):
        if len(data) > self.max_data_size:
            await self.respond(writer, http_response("Data too large! Only %i MB allowed"
                                                     % (self.max_data_size // (1024 ** 2))))
        else:
            m = re.match(RE_GREP_URL, data)
            if m:
                # TODO: use urllib to parse parameters
                func_name, argument = (m.group(1).decode().strip('/').split('/', 1) + [None])[:2]
                # really bad hack to determine mime-type of response
                mime = 'text/html'
                if argument:
                    if argument[-4:].lower() == '.css':  mime = 'text/css'
                    elif argument[-3:].lower() == '.js':  mime = 'text/javascript'
                argument = (argument,) if argument else ()
                if func_name.encode() == STOP_SERVER_REQUEST_BYTES:
                    await self.respond(
                        writer, http_response(HTML_TEMPLATE.format(heading=self.stop_response,
                                                                   content='')))
                    self.kill_switch = True
                    reader.feed_eof()
                else:
                    err_func = lambda *args, **kwargs: UNKNOWN_FUNC_HTML.format(func=func_name)
                    func = self.rpc_table.get(func_name, err_func)
                    if service_call:
                        print('ServiceCall: ' + func_name + str(argument))
                        func, argument = self.amend_service_call(
                            func_name, func, argument, err_func, html=True)
                    elif func_name in self.service_calls:
                        print('Pseudo ServiceCall: ' + func_name + str(argument))
                        argument += (False, True)  # service_call = False, html = True
                    result, rpc_error = await self.run(func.__name__, func, argument)
                    if rpc_error is None:
                        if result is None:
                            result = ''
                        if isinstance(result, (str, bytes, bytearray)):
                            await self.respond(writer, http_response(result, mime))
                        else:
                            try:
                                await self.respond(writer, http_response(
                                    pp_json(result, cls=DHParser_JSONEncoder), 'text/plain'))
                            except TypeError as err:
                                await self.respond(writer, http_response(str(err), 'text/plain'))
                    else:
                        await self.respond(writer, http_response(rpc_error[1], 'text/plain'))
        assert self.connection
        self.connection.task_done(task_id)

    async def handle_jsonrpc_request(self, json_id: int,
                                     reader: StreamReaderType,
                                     writer: StreamWriterType,
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
            method = self.rpc_table[method_name]
            params = json_obj['params'] if 'params' in json_obj else {}
            if service_call:
                err_func = lambda *args, **kwargs: {
                    "error": {"code": -32601,
                              "message": "%s is not a service function" % method_name}}
                method, params = self.amend_service_call(method_name, method, params, err_func)
            params['ID'] = json_id
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
                    if isinstance(result, (bytes, bytearray)):
                        # assume that result is a json-format byte-string!
                        response = b'{"jsonrpc": "2.0", "result": %s, "id": %i}' % (result, json_id)
                    else:
                        json_result = {"jsonrpc": "2.0", "result": result, "id": json_id}
                        response = json_dumps(json_result, cls=DHParser_JSONEncoder)
                    await self.respond(writer, response)
                except TypeError as err:
                    rpc_error = -32070, str(err)

        if rpc_error is not None:
            if json_id >= 0:
                json_str = '{"jsonrpc": "2.0", "error": {"code": %i, "message": %s}, "id": %s}'%\
                       (rpc_error[0], json_encode_string(rpc_error[1]), str(json_id))
            else:
                json_str = '{"jsonrpc": "2.0", "error": {"code": %i, "message": %s}}' % \
                       (rpc_error[0], json_encode_string(rpc_error[1]))
            await self.respond(writer, json_str)

        if result is not None or rpc_error is not None:
            await writer.drain()
        assert self.connection
        self.connection.task_done(json_id)

    async def handle(self, reader: StreamReaderType, writer: StreamWriterType):
        assert self.loop is not None
        # assert self.exec is not None  # causes erratic errors with tests/notest_server_tcp.py

        if isinstance(reader, StreamReaderProxy):
            cast(StreamReaderProxy, reader).loop = self.loop
            cast(StreamReaderProxy, reader).exec = self.exec.thread_executor

        if isinstance(writer, StreamWriterProxy):
            cast(StreamWriterProxy, writer).loop = self.loop
            cast(StreamWriterProxy, writer).exec = self.exec.thread_executor

        if self.connection is None:
            self.connection = Connection(reader, writer, self.exec)
            self.connection.log_file = self.log_file
            self.echo_log = self.echo_log  # will set echo to False is case of a stream connection
            # self.connection.echo_log = self.echo_log  # already set by echo_log property
            id_connection = str(id(self.connection))
            self.connection_callback(self.connection)
            self.log('SERVER MESSAGE: New connection: ', id_connection, '\n')
        else:
            id_connection = ''

        def connection_alive() -> bool:
            """-> `False` if connection is dead or shall be shut down."""
            return not self.kill_switch and self.connection is not None \
                   and self.connection.alive and not reader.at_eof()  # and not reader.closed

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
            #    the data is considered plain data or json-rpc data without a header. The
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
                        # await asyncio.sleep(0)
                        data += await reader.read(content_length or self.max_data_size)
                    except ConnectionError as err:  # (ConnectionAbortedError, ConnectionResetError)
                        self.log('ERROR while awaiting data: ', str(err), '\n')
                        if id_connection:
                            self.connection.alive = False
                        break
                if content_length <= 0 or k <= 0:
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
                        else:
                            k = len(data)
                            content_length = 0
                    elif not incomplete_header(data):
                        # no header or no content-length given
                        # set `context_length` to the size of the data to break the loop
                        content_length = len(data)
                elif content_length + k < len(data):
                    # cut the data of at header size plus content-length
                    buffer = data[content_length + k:]
                    data = data[:content_length + k]
                # continue the loop until at least content_length + k bytes of data
                # have been received

            if self.log_file:   # avoid decoding if logging is off
                timestamp = str(datetime.now())[11:-3]
                if self.log_filter.can_pass(data):
                    self.log(f'RECEIVE {timestamp}: ', *pp_transmission(data), '\n\n')

            if self.connection is None or not self.connection.alive:
                break

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
            if data[:3] == b'GET':
                # HTTP request
                task_id = gen_task_id()
                task = self.connection.create_task(task_id, self.handle_http_request(
                    task_id, reader, writer, data, service_call=not id_connection))
            elif data.find(b'"jsonrpc"') < 0:  # re.match(RE_IS_JSONRPC, data):
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
                        raw_id = json_obj.get('id', gen_task_id())
                        try:
                            json_id = int(raw_id)
                        except TypeError:
                            json_id = 0
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

        if self.connection and (self.kill_switch or not self.connection.alive):
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
                if self.serving_task:
                    self.serving_task.cancel()
            elif self.server:
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

    def run_tcp_server(self, host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT, loop=None):
        """
        Starts a DHParser-server that listens on a tcp port. This function will
        not return until the DHParser-Server ist stopped by sending a
        STOP_SERVER_REQUEST.
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
        except asyncio.CancelledError as e:
            if self.stage.value != SERVER_TERMINATING:
                raise e
        finally:
            # self.server_messages.put(SERVER_OFFLINE)
            self.stage.value = SERVER_OFFLINE

    async def serve_via_streams(self, reader, writer):
        assert self.loop is None
        assert self.exec is None

        self.loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
            else asyncio.get_event_loop()
        self.log('\nLOOP: ' + str(self.loop) + '\n\n')

        self.exec = ExecutionEnvironment(self.loop)
        self.exec.log_file = self.log_file

        try:
            await self.handle(reader, writer)
        finally:
            if self.exec:
                self.exec.shutdown()
            self.exec = None
            self.loop = None

    def run_stream_server(self, reader: StreamReaderType, writer: StreamWriterType):
        """
        Start a DHParser-server that listens on a reader-stream and answers
        on a writer-stream.
        """
        assert self.stage.value == SERVER_OFFLINE
        self.stop_response = "DHParser server communicating over {}, {} stopped!"\
            .format(str(reader), str(writer))
        self.stage.value = SERVER_ONLINE
        try:
            asyncio_run(self.serve_via_streams(reader, writer))
        except KeyboardInterrupt:
            # Don't print an error message, because sys.stdout might
            # be used for communication with the client.
            pass
        except asyncio.CancelledError as e:
            if self.stage.value != SERVER_TERMINATING:
                raise e
        finally:
            self.stage.value = SERVER_OFFLINE


async def probe_tcp_server(host, port, timeout=SERVER_REPLY_TIMEOUT) -> str:
    """Connects to server and sends an identify-request. Returns the response
    or an empty string if connection failed or command timed out."""
    try:
        reader, writer = await asyncio.open_connection(host, port)
        try:
            # request = b'{"jsonrpc": "2.0", "method": "identify", "params": [], "id": null}'
            writer.write(IDENTIFY_REQUEST_BYTES)
            ident = await asyncio.wait_for(reader.read(get_config_value('max_rpc_size')), timeout)
            return ident.decode()
        except asyncio.TimeoutError:
            return ''
    except ConnectionRefusedError:
        return ''


def echo_requests(s: str, log_dir: str='') -> str:
    return s


def _run_tcp_server(host, port, rpc_functions: RPC_Type,
                    cpu_bound: Set[str] = ALL_RPCs,
                    blocking: Set[str] = set(),
                    connection_callback: ConnectionCallback = connection_cb_dummy,
                    server_name: str = '',
                    strict_lsp: bool = True):
    """Starts a tcp-server and waits until server is closed."""
    server = Server(rpc_functions, cpu_bound, blocking,
                    connection_callback, server_name, strict_lsp)
    server.run_tcp_server(host, port)


ConcurrentType = TypeVar('ConcurrentType', Thread, Process)


def spawn_tcp_server(host: str = USE_DEFAULT_HOST,
                     port: int = USE_DEFAULT_PORT,
                     parameters: Union[Tuple, Dict, Callable] = echo_requests,
                     Concurrent: ConcurrentType = Process) -> ConcurrentType:
    """
    Starts DHParser-Server that communicates via tcp in a separate process
    or thread. Can be used for writing test code.

    Servers started with this function sometimes seem to run into race conditions.
    Therefore, USE THIS ONLY FOR TESTING!

    :param host: The host for the tcp-communication, e.g. 127.0.0.1
    :param port: the port number for the tcp-communication.
    :param parameters: The parameter-tuple or -dict for initializing the server
        or simply a rpc-handling function that takes a string-request as
        argument and returns a string response.
    :param Concurrent: The concurrent class, either mutliprocessing.Process or
        threading.Tread for running the server.
    :return: the `multiprocessing.Proccess`-object of the already started
        server-processs.
    """
    if isinstance(parameters, tuple) or isinstance(parameters, list):
        p = Concurrent(target=_run_tcp_server, args=(host, port, *parameters))
    elif isinstance(parameters, dict):
        p = Concurrent(target=_run_tcp_server, args=(host, port), kwargs=parameters)
    else:
        assert callable(parameters)
        p = Concurrent(target=_run_tcp_server, args=(host, port, parameters))
    p.start()
    return p


def _run_stream_server(reader: StreamReaderType,
                       writer: StreamWriterType,
                       rpc_functions: RPC_Type,
                       cpu_bound: Set[str] = ALL_RPCs,
                       blocking: Set[str] = set(),
                       connection_callback: ConnectionCallback = connection_cb_dummy,
                       server_name: str = '',
                       strict_lsp: bool = True):
    """Starts a stream-server and waits until server is closed."""
    server = Server(rpc_functions, cpu_bound, blocking,
                    connection_callback, server_name, strict_lsp)
    server.run_stream_server(reader, writer)


def spawn_stream_server(reader: StreamReaderType,
                        writer: StreamWriterType,
                        parameters: Union[Tuple, Dict, Callable] = echo_requests,
                        Concurrent: ConcurrentType = Thread) -> ConcurrentType:
    """
    Starts a DHParser-Server that communitcates via streams in a separate
    process or thread.

    USE THIS ONLY FOR TESTING!

    :param reader: The stream from which the server will read requests.
    :param writer: The stream to which the server will write responses.
    :param parameters: The parameter-tuple or -dict for initializing the server
        or simply a rpc-handling function that takes a string-request as
        argument and returns a string response.
    :param Concurrent: The concurrent class, either mutliprocessing.Process or
        threading.Tread for running the server.
    :return: the `multiprocessing.Proccess`-object of the already started
        server-processs.
    """
    if isinstance(parameters, tuple) or isinstance(parameters, list):
        p = Concurrent(target=_run_stream_server, args=(reader, writer, *parameters))
    elif isinstance(parameters, dict):
        p = Concurrent(target=_run_stream_server, args=(reader, writer), kwargs=parameters)
    else:
        assert callable(parameters)
        p = Concurrent(target=_run_stream_server, args=(reader, writer, parameters))
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

    # global python_interpreter_name_cached
    host, port = substitute_default_host_and_port(host, port)
    interpreter = sys.executable
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
                await asyncio.sleep(delay)
                delay *= 1.5
            else:
                delay = timeout  # exit while loop
        return False
    except ConnectionRefusedError:
        return True


async def send_stop_request(reader: StreamReaderType, writer: StreamWriterType):
    """
    Send a stop request, reads and drops the reply. Raises a ValueError in
    case the writer is already closed.
    """
    writer.write(JSONRPC_HEADER_BYTES % len(STOP_SERVER_REQUEST_BYTES))
    writer.write(STOP_SERVER_REQUEST_BYTES)
    await writer.drain()
    _ = await read_full_block(reader)  # await reader.read(1024)
    writer.write_eof()
    await writer.drain()
    writer.close()
    if sys.version_info >= (3, 7):
        await writer.wait_closed()


async def send_stop_server(host: str, port: int, timeout) -> Optional[Exception]:
    try:
        reader, writer = await asyncio.open_connection(host, port)
        await send_stop_request(reader, writer)
        if timeout > 0.0:
            if not await has_server_stopped(host, port, timeout):
                raise AssertionError('Could not stop server on host %s port %i '
                                     'within timeout %f !' % (host, port, timeout))
    except ConnectionRefusedError as error:
        return error
    except ConnectionResetError as error:
        return error
    return None


def stop_tcp_server(host: str = USE_DEFAULT_HOST, port: int = USE_DEFAULT_PORT,
                    timeout: float = 3.0) -> Optional[Exception]:
    """Sends a STOP_SERVER_REQUEST to a running tcp server. Returns any
    legitimate exceptions that occur if the server has already been closed."""

    host, port = substitute_default_host_and_port(host, port)
    return asyncio_run(send_stop_server(host, port, timeout))


def stop_stream_server(reader: StreamReaderType, writer: StreamWriterType) -> Optional[Exception]:
    """Sends a STOP_SERVER_REQUEST to a running stream server. Returns any
    legitimate exceptions that occur if the server has already been closed."""
    if isinstance(reader, StreamReaderProxy):
        reader.loop = None
    if isinstance(writer, StreamWriterProxy):
        writer.loop = None
    try:
        asyncio_run(send_stop_request(reader, writer))
    except ValueError as error:
        return error
    return None


# def io_server(server: Server):
#     stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
#     server.handle(stdin, stdout)

# https://stackoverflow.com/questions/52089869/how-to-create-asyncio-stream-reader-writer-for-stdin-stdout
#
# import asyncio
# import os
# import sys
#
# async def stdio(limit=asyncio.streams._DEFAULT_LIMIT, loop=None):
#     if loop is None:
#         loop = asyncio.get_event_loop()
#
#     if sys.platform == 'win32':
#         return _win32_stdio(loop)
#
#     reader = asyncio.StreamReader(limit=limit, loop=loop)
#     await loop.connect_read_pipe(
#         lambda: asyncio.StreamReaderProtocol(reader, loop=loop), sys.stdin)
#
#     writer_transport, writer_protocol = await loop.connect_write_pipe(
#         lambda: asyncio.streams.FlowControlMixin(loop=loop),
#         os.fdopen(sys.stdout.fileno(), 'wb'))
#     writer = asyncio.streams.StreamWriter(
#         writer_transport, writer_protocol, None, loop)
#
#     return reader, writer
#
# def _win32_stdio(loop):
#     # no support for asyncio stdio yet on Windows, see https://bugs.python.org/issue26832
#     # use an executor to read from stdio and write to stdout
#     # note: if nothing ever drains the writer explicitly, no flushing ever takes place!
#     class Win32StdinReader:
#         def __init__(self):
#             self.stdin = sys.stdin.buffer
#         async def readline():
#             # a single call to sys.stdin.readline() is thread-safe
#             return await loop.run_in_executor(None, self.stdin.readline)
#
#     class Win32StdoutWriter:
#         def __init__(self):
#             self.buffer = []
#             self.stdout = sys.stdout.buffer
#         def write(self, data):
#             self.buffer.append(data)
#         async def drain(self):
#             data, self.buffer = self.buffer, []
#             # a single call to sys.stdout.writelines() is thread-safe
#             return await loop.run_in_executor(None, sys.stdout.writelines, data)
#
#     return Win32StdinReader(), Win32StdoutWriter()


