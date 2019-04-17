#!/usr/bin/python3

"""test_server.py - tests of the server module of DHParser


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
import json
import os
from multiprocessing import Process
import sys
from typing import Tuple

sys.path.extend(['../', './'])

from DHParser.server import Server, STOP_SERVER_REQUEST, SERVER_OFFLINE


scriptdir = os.path.dirname(os.path.realpath(__file__))


# def compiler_dummy(src: str, log_dir: str='') -> Tuple[str, str]:
#     return src


class TestServer:
    # def test_server(self):
    #     cs = Server(compiler_dummy)
    #     cs.run_server()

    def compiler_dummy(self, src: str, log_dir: str = '') -> str:
        return src

    def test_server_proces(self):
        """Basic Test of server module."""
        async def compile(src):
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            writer.write(src.encode())
            data = await reader.read(500)
            writer.close()
            assert data.decode() == "Test"
        cs = Server(self.compiler_dummy, cpu_bound=set())
        try:
            cs.spawn_server('127.0.0.1', 8888)
            asyncio.run(compile('Test'))
        finally:
            cs.terminate_server_process()
            cs.wait_for_termination()

    def test_terminate(self):
        async def terminate_server(termination_request, expected_response):
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            writer.write(termination_request)
            data = await reader.read(500)
            writer.close()
            # print(data)
            assert data.find(expected_response) >= 0, str(data)

        cs = Server(self.compiler_dummy, cpu_bound=set())
        try:
            cs.spawn_server('127.0.0.1', 8888)
            asyncio.run(terminate_server(STOP_SERVER_REQUEST,
                                         b'DHParser server at 127.0.0.1:8888 stopped!'))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE

            cs.spawn_server('127.0.0.1', 8888)
            asyncio.run(terminate_server(b'GET ' + STOP_SERVER_REQUEST + b' HTTP',
                                         b'DHParser server at 127.0.0.1:8888 stopped!'))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE

            cs.spawn_server('127.0.0.1', 8888)
            jsonrpc = json.dumps({"jsonrpc": "2.0", "method": STOP_SERVER_REQUEST.decode()})
            asyncio.run(terminate_server(jsonrpc.encode(),
                                         b'DHParser server at 127.0.0.1:8888 stopped!'))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE
        finally:
            cs.terminate_server_process()
            cs.wait_for_termination()


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
