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

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')  # 'spawn' (windows and linux)
                                               # or 'fork' or 'forkserver' or 'spawn' (linux only)

import asyncio
import functools
import json
import multiprocessing
import os
import platform
import subprocess
import sys
import time
from typing import Callable

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.server import Server, asyncio_run, gen_lsp_table, \
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
            writer.write_eof()
            await writer.drain()
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
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
        self.spawn = multiprocessing.get_start_method() == "spawn"

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
            if sys.version_info >= (3, 7):  await writer.wait_closed()
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
            writer.write_eof()
            await writer.drain()
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
            return data.decode()

        cs = Server(self.compiler_dummy)
        try:
            cs.spawn_server('127.0.0.1', TEST_PORT)
            result = asyncio_run(send_request(IDENTIFY_REQUEST))
            assert isinstance(result, str) and result.startswith('DHParser'), result
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
            if sys.version_info >= (3, 7):  await writer.wait_closed()
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
        if self.spawn:
            SLOW, FAST = '0.1', '0.01'
        else:
            SLOW, FAST = '0.01', '0.001'

        async def call_remote(argument):
            sequence.append(argument)
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(argument.encode())
            sequence.append((await reader.read(500)).decode())
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()

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
                    # delay += 0.0
                    countdown -= 1
            if connected:
                writer.write(IDENTIFY_REQUEST.encode())
                data = await reader.read(500)
                writer.write_eof()
                await writer.drain()
                writer.close()
                if sys.version_info >= (3, 7):  await writer.wait_closed()
                return data.decode()
            return ''

        result = asyncio_run(identify())
        assert result.startswith('DHParser')


def send_request(request: str, expect_response: bool = True) -> str:
    response = ''
    async def send(request):
        try:
            nonlocal response
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(request.encode())
            if expect_response:
                response = (await reader.read(8192)).decode()
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
        except ConnectionRefusedError:
            pass

    asyncio_run(send(request))
    return response

jrpc_id = 0

def json_rpc(method: str, params: dict) -> str:
    global jrpc_id
    jrpc_id += 1
    return json.dumps({'jsonrpc': '2.0', 'id':jrpc_id, 'method':method, 'params': params})


# initialized = multiprocessing.Value('b', 0)
# processId = multiprocessing.Value('Q', 0)
# rootUri = multiprocessing.Array('c', b' ' * 2048)
# clientCapabilities = multiprocessing.Array('c', b' ' * 16384)
# serverCapabilities = multiprocessing.Array('c', b' ' * 16384)
# serverCapabilities.value = json.dumps('{}').encode()
#
#
# def lsp_initialize(**kwargs):
#     global initialized, processId, rootUri, clientCapabilities, serverCapabilities
#     if initialized.value != 0 or processId.value != 0:
#         return {"code": -32002, "message": "Server has already been initialized."}
#     processId.value = kwargs['processId']
#     rootUri.value = kwargs['rootUri'].encode()
#     clientCapabilities.value = json.dumps(kwargs['capabilities']).encode()
#     return {'capabilities': json.loads(serverCapabilities.value.decode())}
#
#
# def lsp_initialized(**kwargs):
#     global initialized
#     print(processId.value)
#     print(rootUri.value)
#     print(clientCapabilities.value)
#     initialized.value = -1
#     return None


def lsp_rpc(f: Callable):
    """A decorator for LanguageServerProtocol-methods. This wrapper
    filters out calls that are made before initializing the server and
    after shutdown and returns an error message instead.
    This decorator should only be used on methods of
    LanguageServerProtocol-objects as it expects the first parameter
    to be a the `self`-reference of this object.
    All LSP-methods should be decorated with this decorator except
    initialize and exit
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            self = args[0]
        except IndexError:
            self = kwargs['self']
        if self.shared.shutdown:
            return {'code': -32600, 'message': 'language server already shut down'}
        elif not self.shared.initialized:
            return {'code': -32002, 'message': 'language server not initialized'}
        else:
            return f(*args, **kwargs)
    return wrapper


class LSP:
    def __init__(self):
        manager = multiprocessing.Manager()
        self.shared = manager.Namespace()
        self.shared.initialized = False
        self.shared.shutdown = False
        self.shared.processId = 0
        self.shared.rootUri = ''
        self.shared.clientCapabilities = ''
        self.shared.serverCapabilities = json.dumps('{}')

    def lsp_initialize(self, **kwargs):
        if self.shared.initialized or self.shared.processId != 0:
            return {"code": -32002, "message": "Server has already been initialized."}
        self.shared.processId = kwargs['processId']
        self.shared.rootUri = kwargs['rootUri']
        self.shared.clientCapabilities = json.dumps(kwargs['capabilities'])
        return {'capabilities': json.loads(self.shared.serverCapabilities)}

    def lsp_initialized(self, **kwargs):
        assert self.shared.processId != 0
        self.shared.initialized = True
        return None

    @lsp_rpc
    def lsp_custom(self, **kwargs):
        return kwargs

    @lsp_rpc
    def lsp_check(self, **kwargs):
        return {'processId': self.shared.processId}

    @lsp_rpc
    def lsp_shutdown(self):
        self.shared.shutdown = True
        return {}

    def lsp_exit(self):
        self.shared.shutdown = True
        return None


class TestLanguageServer:
    """Tests for the generic LanguageServer-class."""

    def setup(self):
        stop_server()
        self.server = None


    def teardown(self):
        if self.server is not None:
            self.server.terminate_server()
            self.server = None
        stop_server()

    def start_server(self):
        stop_server()
        self.lsp = LSP()
        lsp_table = gen_lsp_table(self.lsp, prefix='lsp_')
        self.server = Server(rpc_functions=lsp_table,
                             cpu_bound={'check'},
                             blocking={'custom'})
        self.server.spawn_server('127.0.0.1', TEST_PORT)

    def test_initialize(self):
        self.start_server()
        response = send_request(json_rpc('initialize',
                                         {'processId': 701,
                                          'rootUri': 'file://~/tmp',
                                          'capabilities': {}}))
        i = response.find('"jsonrpc"') - 1
        while i > 0 and response[i] in ('{', '['):
            i -= 1
        res = json.loads(response[i:])
        assert 'result' in res and 'capabilities' in res['result'], str(res)

        response = send_request(json_rpc('custom', {}))
        assert response.find('error') >= 0

        response = send_request(json_rpc('initialized', {}), expect_response=False)
        assert response == '', response

        response = send_request(json_rpc('custom', {'test': 1}))
        assert response.find('test') >= 0

        response = send_request(json_rpc('check', {}))
        assert response.find('701') >= 0

        response = send_request(json_rpc('shutdown', {}))
        assert response.find('error') < 0

        response = send_request(json_rpc('custom', {}))
        assert response.find('error') >= 0

        response = send_request(json_rpc('exit', {}))
        assert response == '', response

    def test_initializion_sequence(self):
        self.start_server()
        async def initialization_seuquence():
            reader, writer = await asyncio.open_connection('127.0.0.1', TEST_PORT)
            writer.write(json_rpc('initialize',
                                  {'processId': 701,
                                   'rootUri': 'file://~/tmp',
                                   'capabilities': {}}).encode())
            response = (await reader.read(8192)).decode()
            i = response.find('"jsonrpc"') - 1
            while i > 0 and response[i] in ('{', '['):
                i -= 1
            res = json.loads(response[i:])
            assert 'result' in res and 'capabilities' in res['result'], str(res)

            writer.write(json_rpc('initialized', {}).encode())

            writer.write(json_rpc('custom', {'test': 1}).encode())
            response = (await reader.read(8192)).decode()
            assert response.find('test') >= 0

        asyncio_run(initialization_seuquence())


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())

