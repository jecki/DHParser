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
import platform
import subprocess
import sys
import time

sys.path.extend(['../', './'])

from DHParser.server import Server, LanguageServerProtocol, create_language_server, asyncio_run, \
    STOP_SERVER_REQUEST, IDENTIFY_REQUEST, SERVER_OFFLINE
from DHParser.toolkit import concurrent_ident

# from DHParser.configuration import CONFIG_PRESET
# THREAD_LOCALS.LOGGING = 'LOGS'
# if not os.path.exists('LOGS'):
#     os.mkdir('LOGS')
# CONFIG_PRESET['log_server'] = True

scriptdir = os.path.dirname(os.path.realpath(__file__))


TEST_PORT = 8889

# def compiler_dummy(src: str, log_dir: str='') -> Tuple[str, str]:
#     return src

def stop_server():
    async def send_stop_server():
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(STOP_SERVER_REQUEST)
            _ = await reader.read(1024)
            writer.close()
        except ConnectionRefusedError:
            pass
        except ConnectionResetError:
            pass

    asyncio_run(send_stop_server())


class TestServer:
    # def test_server(self):
    #     cs = Server(compiler_dummy)
    #     cs.run_server()

    def setup(self):
        stop_server()
        self.windows = sys.platform.lower().find('win') >= 0

    def compiler_dummy(self, src: str) -> str:
        return src

    def long_running(self, duration: str) -> str:
        time.sleep(float(duration))
        return(duration)

    def test_server_process(self):
        """Basic Test of server module."""
        async def compile_remote(src):
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(src.encode())
            data = await reader.read(500)
            writer.close()
            assert data.decode() == "Test", data.decode()
        cs = Server(self.compiler_dummy, cpu_bound=set())
        try:
            cs.spawn_server('127.0.0.1', TEST_PORT)
            asyncio_run(compile_remote('Test'))
        finally:
            cs.terminate_server()

    def test_indentify(self):
        """Test server's 'identify/'-command."""
        async def send_request(request):
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(request.encode() if isinstance(request, str) else request)
            data = await reader.read(500)
            writer.close()
            return data.decode()

        cs = Server(self.compiler_dummy)
        try:
            cs.spawn_server('127.0.0.1', TEST_PORT)
            result = asyncio_run(send_request(IDENTIFY_REQUEST))
            assert result.startswith('DHParser'), result
        finally:
            cs.terminate_server()

    def test_terminate(self):
        """Test different ways of sending a termination message to server:
        http-request, plain-text and json-rpc."""
        async def terminate_server(termination_request, expected_response):
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(termination_request)
            data = await reader.read(500)
            writer.close()
            # print(data)
            assert data.find(expected_response) >= 0, str(data)

        cs = Server(self.compiler_dummy, cpu_bound=set())
        try:
            cs.spawn_server('127.0.0.1', TEST_PORT)
            asyncio_run(terminate_server(STOP_SERVER_REQUEST,
                                         b'DHParser server at 127.0.0.1:%i stopped!' % TEST_PORT))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE

            cs.spawn_server('127.0.0.1', TEST_PORT)
            asyncio_run(terminate_server(b'GET ' + STOP_SERVER_REQUEST + b' HTTP',
                                         b'DHParser server at 127.0.0.1:%i stopped!' % TEST_PORT))
            cs.wait_for_termination()
            assert cs.stage.value == SERVER_OFFLINE

            cs.spawn_server('127.0.0.1', TEST_PORT)
            jsonrpc = json.dumps({"jsonrpc": "2.0", "method": STOP_SERVER_REQUEST.decode(),
                                  'id': 1})
            asyncio_run(terminate_server(jsonrpc.encode(),
                                         b'DHParser server at 127.0.0.1:%i stopped!' % TEST_PORT))
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
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
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
                cs.spawn_server('127.0.0.1', TEST_PORT)
                asyncio_run(run_tasks())
                assert sequence == [SLOW, FAST, FAST, SLOW], str(sequence)
            finally:
                cs.terminate_server()

            cs = Server(self.long_running,
                        cpu_bound=frozenset(),
                        blocking=frozenset(['long_running']))
            try:
                sequence = []
                cs.spawn_server('127.0.0.1', TEST_PORT)
                asyncio_run(run_tasks())
                assert sequence == [SLOW, FAST, FAST, SLOW]
            finally:
                cs.terminate_server()

        cs = Server(self.long_running,
                    cpu_bound=frozenset(),
                    blocking=frozenset())
        try:
            sequence = []
            cs.spawn_server('127.0.0.1', TEST_PORT)
            asyncio_run(run_tasks())
            # if run asyncronously, order os results is arbitrary
            assert sequence.count(SLOW) == 2 and sequence.count(FAST) == 2
        finally:
            cs.terminate_server()


RUN_SERVER_SCRIPT = """
import os
import sys

path = '.'
while not 'DHParser' in os.listdir(path) and len(path) < 20:
    path = os.path.join('..', path)
sys.path.append(path)

def dummy(s: str) -> str:
    return s

def run_server(host, port):
    from DHParser.server import Server
    # print('Starting server on %s:%i' % (host, port))
    server = Server(dummy)
    server.run_server(host, port)

if __name__ == '__main__':
    run_server('127.0.0.1', {TEST_PORT})
""".format(TEST_PORT=TEST_PORT)


class TestSpawning:
    """Tests spawning a server by starting a script via subprocess.Popen."""

    def setup(self):
        self.tmpdir = 'tmp_' + concurrent_ident()
        os.mkdir(self.tmpdir)
        stop_server()

    def teardown(self):
        stop_server()
        for fname in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, fname))
        os.rmdir(self.tmpdir)

    def test_spawn(self):
        scriptname = os.path.join(self.tmpdir, 'spawn_server.py')
        with open(scriptname, 'w') as f:
            f.write(RUN_SERVER_SCRIPT)
        nulldevice = " >/dev/null" if platform.system() != "Windows" else " > NUL"
        interpreter = 'python3' if os.system('python3 -V' + nulldevice) == 0 else 'python'
        subprocess.Popen([interpreter, scriptname])

        async def identify():
            countdown = 20
            delay = 0.05
            connected = False
            reader, writer = None, None
            while countdown > 0:
                try:
                    reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
                    # print(countdown)
                    countdown = 0
                    connected = True
                except ConnectionRefusedError:
                    time.sleep(delay)
                    delay += 0.0
                    countdown -= 1
            if connected:
                writer.write(IDENTIFY_REQUEST.encode())
                data = await reader.read(500)
                writer.close()
                return data.decode()
            return ''

        result = asyncio_run(identify())
        # print(result)


def send_request(request: str) -> str:
    response = ''
    async def send(request):
        try:
            nonlocal response
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(request.encode())
            response = (await reader.read(8192)).decode()
            writer.close()
        except ConnectionRefusedError:
            pass

    asyncio_run(send(request))
    return response


def json_rpc(method: str, params: dict) -> dict:
    return json.dumps({'jsonrpc': '2.0', 'id':'0', 'method':method, 'params': params})



class TestLanguageServer:
    """Tests for the generic LanguageServer-class."""

    def setup(self):
        stop_server()
        self.windows = sys.platform.lower().find('win') >= 0
        self.server = create_language_server(LanguageServerProtocol())
        self.server.spawn_server('127.0.0.1', TEST_PORT)

    def teardown(self):
        self.server.terminate_server()
        stop_server()

    def test_initialize(self):
        response = send_request(json_rpc('initialize',
                                         {'processId': 0,
                                          'rootUri': 'file://~/tmp',
                                          'capabilities': {}}))
        res = json.loads(response)
        assert 'result' in res and 'capabilities' in res['result']




if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
