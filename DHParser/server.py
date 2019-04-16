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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
from multiprocessing import Process, Value, Queue
import sys
import time
from typing import Callable, Optional, Union, Dict, List, Tuple, Sequence, Set, cast

from DHParser.toolkit import get_config_value, is_filename, load_if_file, re

__all__ = ('RPC_Table',
           'RPC_Type',
           'JSON_Type',
           'SERVER_ERROR',
           'SERVER_OFFLINE',
           'SERVER_STARTING',
           'SERVER_ONLINE',
           'SERVER_TERMINATE',
           'Server')


RPC_Table = Dict[str, Callable]
RPC_Type = Union[RPC_Table, List[Callable], Callable]
JSON_Type = Union[Dict, Sequence, str, int, None]

RX_IS_JSON = re.compile(b'\s*(?:{|\[|"|\d|true|false|null)')
RX_GREP_URL = re.compile(b'GET ([^ ]+) HTTP')

SERVER_ERROR = "COMPILER-SERVER-ERROR"

SERVER_OFFLINE = 0
SERVER_STARTING = 1
SERVER_ONLINE = 2
SERVER_TERMINATE = 3

RESPONSE_HEADER = b'''HTTP/1.1 200 OK
Date: {date}
Server: DHParser
Accept-Ranges: none
Content-Length: {length}
Connection: close
Content-Type: text/html; charset=utf-8
X-Pad: avoid browser bug
'''

UNKNOWN_FUNC_HTML = """<!DOCTYPE html>
<html lang="en" xml:lang="en">
<head>
  <meta charset="UTF-8" />
</head>
<body>
<h1>DHParser Error: Function {func} unknown or not registered!</h1>
</body>
</html>
"""

STOP_SERVER_REQUEST = b"__STOP_SERVER__"


__test_get = b'''GET /method/object HTTP/1.1
Host: 127.0.0.1:8888
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: de,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate
DNT: 1
Connection: keep-alive
Upgrade-Insecure-Requests: 1


'''


def gmtstamp() -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

# CompilationItem = NamedTuple('CompilationItem',
#                              [('uri', str),
#                               ('hash', int),
#                               ('errors', str),
#                               ('preview', str)])

ALL_RPCs = frozenset('*')  # Magic value denoting all remove procedures


class Server:
    def __init__(self, rpc_functions: RPC_Type,
                 cpu_bound: Set[str] = ALL_RPCs,
                 blocking: Set[str] = frozenset()):
        if isinstance(rpc_functions, Dict):
            self.rpc_table = cast(RPC_Table, rpc_functions)  # type: RPC_Table
        elif isinstance(rpc_functions, List):
            self.rpc_table = {}
            for func in cast(List, rpc_functions):
                self.rpc_table[func.__name__] = func
        else:
            assert isinstance(rpc_functions, Callable)
            func = cast(Callable, rpc_functions)
            self.rpc_table = {func.__name__: func}

        # see: https://docs.python.org/3/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools
        self.cpu_bound = frozenset(self.rpc_table.keys()) if cpu_bound == ALL_RPCs else cpu_bound
        self.blocking = frozenset(self.rpc_table.keys()) if blocking == ALL_RPCs else blocking
        self.blocking = self.blocking - self.cpu_bound  # cpu_bound property takes precedence

        assert not (self.cpu_bound - self.rpc_table.keys())
        assert not (self.blocking - self.rpc_table.keys())

        self.max_source_size = get_config_value('max_rpc_size')  #type: int
        self.stage = Value('b', SERVER_OFFLINE)  # type: Value
        self.server = None  # type: Optional[asyncio.AbstractServer]
        self.server_messages = Queue()  # type: Queue
        self.server_process = None  # type: Optional[Process]

        # if the server is run in a separate process, the following variables
        # should only be accessed from the server process
        self.server = None        # type: Optional[asyncio.AbstractServer]
        self.stop_response = ''   # type: str
        self.pp_executor = None   # type: Optional[ProcessPoolExecutor]
        self.tp_executor = None   # type: Optional[ThreadPoolExecutor]

    async def handle_request(self,
                             reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter):
        rpc_error = None   # type: Optional[Tuple[int, str]]
        json_id = 'null'   # type: Tuple[int, str]
        obj = {}           # type: Dict
        result = None      # type: JSON_Type
        raw = None         # type: JSON_Type
        killswitch = False # type: bool

        data = await reader.read(self.max_source_size + 1)
        oversized = len(data) > self.max_source_size

        if data.startswith(b'GET'):
            # HTTP request
            m = RX_GREP_URL(data)
            if m:
                func_name, argument = m.group(1).decode().strip('/').split('/', 1) + [None]
                if func_name.encode() == STOP_SERVER_REQUEST:
                    writer.write(self.stop_response.encode())
                    killswitch = True
                else:
                    func = self.rpc_table.get(func_name,
                                              lambda _: UNKNOWN_FUNC_HTML.format(func=func_name))
                    result = func(argument) if argument is not None else func()
                    if isinstance(result, str):
                        gmt = gmtstamp.encode()
                        response = RESPONSE_HEADER.format(date=gmt, length=str(len(res)).encode) \
                                   + result.encode()
                        writer.write(response)
                    else:
                        writer.write(json.dumps(result).encode())

        elif not RX_IS_JSON.match(data):
            # plain data
            if oversized:
                writer.write("Source code too large! Only %i MB allowed" \
                             % (self.max_source_size // (1024 ** 2)))
            elif data == STOP_SERVER_REQUEST:
                writer.write(self.stop_response.encode())
                killswitch = True
            else:
                if len(self.rpc_table) == 1:
                    func = self.rpc_table[tuple(self.rpc_table.keys())[0]]
                else:
                    err = lambda arg: 'function "compile_src" not registered!'
                    func = self.rpc_table.get('compile_src', self.rpc_table.get('compile', err))
                result = func(data.decode())
                if isinstance(result, str):
                    writer.write(result.encode())
                else:
                    writer.write(json.dumps(result).encode())

        else:
            # JSON RPC
            if oversized:
                rpc_error = -32600, "Invaild Request: Source code too large! Only %i MB allowed" \
                            % (self.max_source_size // (1024 ** 2))

            if rpc_error is None:
                try:
                    raw = json.loads(data)
                except json.decoder.JSONDecodeError as e:
                    rpc_error = -32700, "JSONDecodeError: " + str(e) + str(data)

            if rpc_error is None:
                if isinstance(raw, Dict):
                    obj = cast(Dict, raw)
                    json_id = obj.get('id', 'null')
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
                    killswitch = True
                elif obj['method'] not in self.rpc_table:
                    rpc_error = -32601, 'Method not found: ' + str(obj['method'])
                else:
                    method_name = obj['method']
                    method = self.rpc_table[method_name]
                    params = obj['params'] if 'params' in obj else ()
                    try:
                        # run method either a) directly if it is short running or
                        # b) in a thread pool if it contains blocking io or
                        # c) in a process pool if it is cpu bound
                        # see: https://docs.python.org/3/library/asyncio-eventloop.html
                        #      #executing-code-in-thread-or-process-pools
                        has_kw_params = isinstance(params, Dict)
                        assert has_kw_params or isinstance(params, Sequence)
                        loop = asyncio.get_running_loop()
                        executor = self.pp_executor if method_name in self.cpu_bound else \
                                   self.tp_executor if method_name in self.blocking else None
                        if executor is None:
                            result = method(**params) if has_kw_params else method(*params)
                        elif has_kw_params:
                            result = await loop.run_in_executor(executor, method, **params)
                        else:
                            result = await loop.run_in_executor(executor, method, *params)
                    except TypeError as e:
                        rpc_error = -32602, "Invalid Params: " + str(e)
                    except NameError as e:
                        rpc_error = -32601, "Method not found: " + str(e)
                    except Exception as e:
                        rpc_error = -32000, "Server Error: " + str(e)

            if rpc_error is None:
                json_result = {"jsonrpc": "2.0", "result": result, "id": json_id}
                json.dump(writer, json_result)
            else:
                writer.write(('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s}'
                              % (rpc_error[0], rpc_error[1], json_id)).encode())
        await writer.drain()
        writer.close()
        if killswitch:
            self.server.cancel()

    async def serve(self, host: str = '127.0.0.1', port: int = 8888):
        with ProcessPoolExecutor() as p, ThreadPoolExecutor() as t:
            self.stop_response = "DHParser server at {}:{} stopped!".format(host, port)
            self.server = cast(asyncio.base_events.Server,
                               await asyncio.start_server(self.handle_request, host, port))
            async with self.server:
                self.stage.value = SERVER_ONLINE
                self.server_messages.put(SERVER_ONLINE)
                await self.server.serve_forever()
            # self.server.wait_until_closed()

    def run_server(self, address: str = '127.0.0.1', port: int = 8888):
        assert self.stage.value == SERVER_OFFLINE
        self.stage.value = SERVER_STARTING
        if sys.version_info >= (3, 7):
            asyncio.run(self.serve(address, port))
        else:
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self.serve(address, port))
            finally:
                # self.server.cancel()
                loop.close()

    def wait_until_server_online(self):
        if self.stage.value != SERVER_ONLINE:
            if self.server_messages.get() != SERVER_ONLINE:
                raise AssertionError('could not start server!?')
            assert self.stage.value == SERVER_ONLINE

    def run_as_process(self):
        self.server_process = Process(target=self.run_server)
        self.server_process.start()
        self.wait_until_server_online()

    def terminate_server_process(self):
        if self.server_process:
            self.stage.value = SERVER_TERMINATE
            self.server_process.terminate()
            self.server_process = None
        self.stage.value = SERVER_OFFLINE

    def wait_for_termination_request(self):
        if self.server_process:
            if self.stage.value in (SERVER_STARTING, SERVER_ONLINE):
                while self.server_messages.get() != SERVER_TERMINATE:
                    pass
            if self.stage.value == SERVER_TERMINATE:
                self.terminate_server_process()
