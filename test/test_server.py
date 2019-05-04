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
import sys
import time

sys.path.extend(['../', './'])

from DHParser.server import Server, STOP_SERVER_REQUEST, IDENTIFY_REQUEST, SERVER_OFFLINE, asyncio_run


scriptdir = os.path.dirname(os.path.realpath(__file__))


# def compiler_dummy(src: str, log_dir: str='') -> Tuple[str, str]:
#     return src


class TestServer:
    # def test_server(self):
    #     cs = Server(compiler_dummy)
    #     cs.run_server()

    def setup(self):
        self.windows = sys.platform.lower().find('win') >= 0

    def compiler_dummy(self, src: str) -> str:
        return src

    def long_running(self, duration: str) -> str:
        time.sleep(float(duration))
        return(duration)

    def test_server_proces(self):
        """Basic Test of server module."""
        async def compile_remote(src):
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            writer.write(src.encode())
            data = await reader.read(500)
            writer.close()
            assert data.decode() == "Test", data.decode()
        cs = Server(self.compiler_dummy, cpu_bound=set())
        try:
            cs.spawn_server('127.0.0.1', 8888)
            asyncio_run(compile_remote('Test'))
        finally:
            cs.terminate_server()

    def test_indentify(self):
        """Test server's 'identify/'-command."""
        async def send_request(request):
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            writer.write(request.encode() if isinstance(request, str) else request)
            data = await reader.read(500)
            writer.close()
            return data.decode()

        cs = Server(self.compiler_dummy)
        try:
            cs.spawn_server('127.0.0.1', 8888)
            result = asyncio_run(send_request(IDENTIFY_REQUEST))
            assert result.startswith('DHParser'), result
        finally:
            cs.terminate_server()

    def test_terminate(self):
        """Test different ways of sending a termination message to server:
        http-request, plain-text and json-rpc."""
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
            asyncio_run(terminate_server(STOP_SERVER_REQUEST,
                                         b'DHParser server at 127.0.0.1:8888 stopped!'))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE

            cs.spawn_server('127.0.0.1', 8888)
            asyncio_run(terminate_server(b'GET ' + STOP_SERVER_REQUEST + b' HTTP',
                                         b'DHParser server at 127.0.0.1:8888 stopped!'))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE

            cs.spawn_server('127.0.0.1', 8888)
            jsonrpc = json.dumps({"jsonrpc": "2.0", "method": STOP_SERVER_REQUEST.decode(),
                                  'id': 1})
            asyncio_run(terminate_server(jsonrpc.encode(),
                                         b'DHParser server at 127.0.0.1:8888 stopped!'))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE
        finally:
            cs.terminate_server()

    def test_long_running_task(self):
        """Test, whether delegation of (long-running) tasks to
        processes or threads works."""
        sequence = []
        if self.windows:
            SLOW, FAST = '0.1', '0.01'
        else:
            SLOW, FAST = '0.01', '0.001'

        async def call_remote(argument):
            sequence.append(argument)
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            writer.write(argument.encode())
            sequence.append((await reader.read(500)).decode())
            writer.close()

        async def run_tasks():
            await asyncio.gather(call_remote(SLOW),
                                 call_remote(FAST))

        if sys.version_info >= (3, 6):
            cs = Server(self.long_running,
                        cpu_bound=frozenset(['long_running']),
                        blocking=frozenset())
            try:
                cs.spawn_server('127.0.0.1', 8888)
                asyncio_run(run_tasks())
                assert sequence == [SLOW, FAST, FAST, SLOW], str(sequence)
            finally:
                cs.terminate_server()

            cs = Server(self.long_running,
                        cpu_bound=frozenset(),
                        blocking=frozenset(['long_running']))
            try:
                sequence = []
                cs.spawn_server('127.0.0.1', 8888)
                asyncio_run(run_tasks())
                assert sequence == [SLOW, FAST, FAST, SLOW]
            finally:
                cs.terminate_server()

        cs = Server(self.long_running,
                    cpu_bound=frozenset(),
                    blocking=frozenset())
        try:
            sequence = []
            cs.spawn_server('127.0.0.1', 8888)
            asyncio_run(run_tasks())
            # if run asyncronously, order os results is arbitrary
            assert sequence.count(SLOW) == 2 and sequence.count(FAST) == 2
        finally:
            cs.terminate_server()


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
