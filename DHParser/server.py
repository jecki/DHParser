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
import json
from multiprocessing import Process, Value, Queue
from typing import Callable, Optional, Union, Dict, List, Sequence, cast

from DHParser.toolkit import get_config_value, re

RPC_Table = Dict[str, Callable]
RPC_Type = Union[RPC_Table, List[Callable], Callable]

SERVER_ERROR = "COMPILER-SERVER-ERROR"

SERVER_OFFLINE = 0
SERVER_STARTING = 1
SERVER_ONLINE = 2
SERVER_TERMINATE = 3


RX_MAYBE_JSON = re.compile('\s*(?:\{|\[|"|\d|true|false|null)')


class Server:
    def __init__(self, rpc_functions: RPC_Type):
        if isinstance(rpc_functions, Dict):
            self.rpc_table = cast(RPC_Table, rpc_functions)  # type: RPC_Table
        elif isinstance(rpc_functions, List):
            self.rpc_table = {}
            for func in cast(List, rpc_functions):
                self.rpc_table[func.__name__] = func
        else:
            assert isinstance(rpc_functions, Callable)
            func = cast(Callable, rpc_functions)
            self.rpc_table = { func.__name__: func }

        self.max_source_size = get_config_value('max_rpc_size')
        self.stage = Value('b', SERVER_OFFLINE)
        self.server = None
        self.server_messages = Queue()  # type: Queue
        self.server_process = None  # type: Optional[Process]

    async def handle_compilation_request(self,
                                         reader: asyncio.StreamReader,
                                         writer: asyncio.StreamWriter):
        data = await reader.read(self.max_source_size + 1)
        rpc_error = None
        json_id = 'null'

        if len(data) > self.max_source_size:
            rpc_error = -32600, "Invaild Request: Source code too large! Only %i MB allowed" \
                                % (self.max_source_size // (1024**2))

        if rpc_error is None:
            try:
                obj = json.loads(data)
            except json.decoder.JSONDecodeError as e:
                rpc_error = -32700, "JSONDecodeError: " + str(e)

        if rpc_error is None:
            if isinstance(obj, Dict):
                json_id = obj.get('id', 'null') if isinstance(obj, Dict) else 'null'
            else:
                rpc_error = -32700, 'Parse error: Request does not appear to be an RPC-call!?'

        if rpc_error is None:
            if obj.get('jsonrpc', 'unknown') != '2.0':
                rpc_error = -32600, 'Invalid Request: jsonrpc version 2.0 needed, version "' \
                            ' "%s" found.' % obj.get('jsonrpc', b'unknown')
            elif not 'method' in obj:
                rpc_error = -32600, 'Invalid Request: No method specified.'
            elif obj['method'] not in self.rpc_table:
                rpc_error = -32601, 'Method not found: ' + str(obj['method'])
            else:
                method = self.rpc_table[obj['method']]
                params = obj['params'] if 'params' in obj else ()
                try:
                    if isinstance(params, Sequence):
                        result = method(*params)
                    elif isinstance(params, Dict):
                        result = method(**params)
                except Exception as e:
                    rpc_error = -32602, "Invalid Params: " + str(e)

        if rpc_error is None:
            json_result = {"jsonrpc": "2.0", "result": result, "id": json_id}
            json.dump(writer, json_result)
        else:
            writer.write(('{"jsonrpc": "2.0", "error": {"code": %i, "message": "%s"}, "id": %s '
                          % (rpc_error[0], rpc_error[1], json_id)).encode())
        await writer.drain()
        writer.close()
        # TODO: add these lines in case a terminate signal is received, i.e. exit server coroutine
        #  gracefully.
        # self.server.cancel()

    async def serve(self, address: str = '127.0.0.1', port: int = 8888):
        self.server = await asyncio.start_server(self.handle_compilation_request, address, port)
        async with self.server:
            self.stage.value = SERVER_ONLINE
            self.server_messages.put(SERVER_ONLINE)
            await self.server.serve_forever()
        # self.server.wait_until_closed()

    def run_server(self, address: str = '127.0.0.1', port: int = 8888):
        self.stage.value = SERVER_STARTING
        asyncio.run(self.serve(address, port))

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
        self.server_process.terminate()

    def wait_for_termination_request(self):
        assert self.server_process
        # self.wait_until_server_online()
        while self.server_messages.get() != SERVER_TERMINATE:
            pass
        self.terminate_server_process()
        self.server_process = None
