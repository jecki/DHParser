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
"""


import asyncio
from multiprocessing import Process, Value, Queue
from typing import Callable, Optional, Any

from DHParser.preprocess import BEGIN_TOKEN, END_TOKEN, TOKEN_DELIMITER
from DHParser.toolkit import get_config_value


# TODO: implement compilation-server!

SERVER_ERROR = "COMPILER-SERVER-ERROR"
CompileFunc = Callable[[str, str], Any]     # compiler_src(source: str, log_dir: str) -> Any


SERVER_OFFLINE = 0
SERVER_STARTING = 1
SERVER_ONLINE = 2
SERVER_TERMINATE = 3



class CompilerServer:
    def __init__(self, compiler: CompileFunc):
        self.compiler = compiler
        self.max_source_size = get_config_value('max_source_size')
        self.stage = Value('b', SERVER_OFFLINE)
        self.server_messages = Queue()  # type: Queue
        self.server_process = None  # type: Optional[Process]

    async def handle_compilation_request(self,
                                         reader: asyncio.StreamReader,
                                         writer: asyncio.StreamWriter):
        data = await reader.read(self.max_source_size + 1)
        if len(data) > self.max_source_size:
            writer.write(BEGIN_TOKEN + SERVER_ERROR + TOKEN_DELIMITER +
                         "Source code to large! Only %iMB allowed." %
                         (self.max_source_size // (1024**2)) + END_TOKEN)
        else:
            writer.write(data)   # for now, only echo
        await writer.drain()
        writer.close()

    async def serve(self, address: str = '127.0.0.1', port: int = 8888):
        server = await asyncio.start_server(self.handle_compilation_request, address, port)
        async with server:
            self.stage.value = SERVER_ONLINE
            self.server_messages.put(SERVER_ONLINE)
            await server.serve_forever()

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

    def wait_for_termination(self):
        assert self.server_process
        # self.wait_until_server_online()
        while self.server_messages.get() != SERVER_TERMINATE:
            pass
        self.terminate_server_process()
        self.server_process = None
