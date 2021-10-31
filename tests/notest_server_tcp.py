#!/usr/bin/env python3

"""notest_server_tcp.py - tests of the server module of DHParser,
    connections via tcp.


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

# Quite slow under MS Windows! Therefore, renamed to notest_server_tcp.py
# so that it not regularly called when running pytest/nosetest on
# the test directory.


import asyncio
import functools
import json
import multiprocessing
import os
import sys
import time
from typing import Callable, Union


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    if sys.platform.lower().startswith('win'):
        multiprocessing.set_start_method('spawn')
    # else:
    #     multiprocessing.set_start_method('forkserver')


scriptpath = os.path.abspath(os.path.dirname(__file__) or '.')
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import set_config_value
from DHParser.server import Server, spawn_tcp_server, stop_tcp_server, asyncio_run, asyncio_connect, \
    split_header, has_server_stopped, STOP_SERVER_REQUEST_BYTES, IDENTIFY_REQUEST, \
    SERVER_OFFLINE, connection_cb_dummy
from DHParser.lsp import gen_lsp_table
from DHParser.testing import unique_name

TEST_PORT = 8000 + os.getpid() % 1000
# print('>>> ', sys.version, TEST_PORT)
# adding pid % 100 hopefully prevents interference, if `test_server.py` is run in
# parallel with several different python versions, as done by `run.py`


def compiler_dummy(src: str, log_dir: str='') -> str:
    return src


def long_running(duration: float, **kwargs) -> float:
    time.sleep(float(duration))
    return duration


def send_request(request: str, expect_response: bool = True) -> str:
    response = ''
    async def send(request):
        nonlocal response
        reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
        writer.write(request.encode())
        if expect_response:
            response = (await reader.read(8192)).decode()
        writer.close()
        if sys.version_info >= (3, 7):  await writer.wait_closed()

    asyncio_run(send(request))
    return response


jrpc_id = 0


def json_rpc(method: str, params: dict) -> str:
    global jrpc_id
    jrpc_id += 1
    s = json.dumps({'jsonrpc': '2.0', 'id': jrpc_id, 'method': method, 'params': params})
    return 'Content-Length: %i\n\n' % len(s) + s


class TestServer:
    spawn = multiprocessing.get_start_method() in ["spawn", "forkserver"]

    def setup(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)

    def teardown(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)

    def test_server_process(self):
        """Basic Test of server module."""
        async def compile_remote(src):
            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            writer.write(src.encode())
            data = await reader.read(500)
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
            assert data.decode() == "Test", data.decode()

        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        p = None
        try:
            p = spawn_tcp_server('127.0.0.1', TEST_PORT,
                                 (compiler_dummy, set()))
            asyncio_run(compile_remote('Test'))
        finally:
            stop_tcp_server('127.0.0.1', TEST_PORT)
            if p is not None:
                p.join()

    def test_service_call(self):
        async def identify_server():
            main_reader, main_writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            main_writer.write(IDENTIFY_REQUEST.encode())
            data = await main_reader.read(500)
            assert b'already connected' not in data

            service_reader, service_writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            service_writer.write(IDENTIFY_REQUEST.encode())
            data = await service_reader.read(500)
            assert b'already connected' in data
            await asyncio.sleep(0.01)
            assert service_reader.at_eof()
            service_writer.close()
            if sys.version_info >= (3, 7):  await service_writer.wait_closed()

            service_reader, service_writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            service_writer.write(json_rpc('identify', {}).encode())
            data = await service_reader.read(500)
            assert b'already connected' in data
            await asyncio.sleep(0.01)
            assert service_reader.at_eof()
            service_writer.close()
            if sys.version_info >= (3, 7):  await service_writer.wait_closed()

            main_writer.close()
            if sys.version_info >= (3, 7):  await main_writer.wait_closed()

        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        p = None
        try:
            p = spawn_tcp_server('127.0.0.1', TEST_PORT)
            asyncio_run(identify_server())
        finally:
            stop_tcp_server('127.0.0.1', TEST_PORT)
            if p is not None:
                p.join()

    def test_identify(self):
        """Test server's 'identify/'-command."""
        async def send_request(request):
            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            writer.write(request.encode() if isinstance(request, str) else request)
            data = await reader.read(500)
            await writer.drain()
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
            return data.decode()
        try:
            from _ctypes import Union, Structure, Array
            p = None
            try:
                from timeit import timeit
                p = spawn_tcp_server('127.0.0.1', TEST_PORT, compiler_dummy)
                result = asyncio_run(send_request(IDENTIFY_REQUEST))
                assert isinstance(result, str) and result.startswith('DHParser'), result
            finally:
                stop_tcp_server('127.0.0.1', TEST_PORT)
                if p is not None:
                    p.join()
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')

    def test_terminate(self):
        """Test different ways of sending a termination message to server:
        http-request, plain-text and json-rpc."""
        async def terminate_server(termination_request, expected_response):
            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            writer.write(termination_request)
            data = await reader.read(500)
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()
            assert data.find(expected_response) >= 0, str(data)

        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        p = None
        try:
            # plain text stop request
            p = spawn_tcp_server('127.0.0.1', TEST_PORT, (compiler_dummy, set()))
            asyncio_run(terminate_server(STOP_SERVER_REQUEST_BYTES,
                                         b'DHParser server at 127.0.0.1:%i stopped!' % TEST_PORT))
            assert asyncio_run(has_server_stopped('127.0.0.1', TEST_PORT))

            # http stop request
            p = spawn_tcp_server('127.0.0.1', TEST_PORT, (compiler_dummy, set()))
            asyncio_run(terminate_server(b'GET ' + STOP_SERVER_REQUEST_BYTES + b' HTTP',
                                         b'DHParser server at 127.0.0.1:%i stopped!' % TEST_PORT))
            assert asyncio_run(has_server_stopped('127.0.0.1', TEST_PORT))

            # json_rpc stop request
            p = spawn_tcp_server('127.0.0.1', TEST_PORT, (compiler_dummy, set()))
            jsonrpc = json.dumps({"jsonrpc": "2.0", "method": STOP_SERVER_REQUEST_BYTES.decode(),
                                  'id': 1})
            asyncio_run(terminate_server(jsonrpc.encode(),
                                         b'DHParser server at 127.0.0.1:%i stopped!' % TEST_PORT))
            assert asyncio_run(has_server_stopped('127.0.0.1', TEST_PORT))
        finally:
            stop_tcp_server('127.0.0.1', TEST_PORT)
            if p is not None:
                p.join()

    def test_long_running_task(self):
        """Test, whether delegation of (long-running) tasks to
        processes or threads works."""
        sequence = []
        if self.spawn:
            SLOW, FAST = 0.1, 0.01
        else:
            SLOW, FAST = 0.02, 0.001

        async def run_tasks():
            def extract_result(data: bytes):
                header, data, backlog = split_header(data)
                return json.loads(data.decode())['result']

            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            sequence.append(SLOW)
            sequence.append(FAST)
            writer.write(json_rpc('long_running', {'duration': SLOW}).encode())
            writer.write(json_rpc('long_running', {'duration': FAST}).encode())
            await writer.drain()
            sequence.append(extract_result(await reader.read(500)))
            sequence.append(extract_result(await reader.read(500)))
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()

        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        if sys.version_info >= (3, 6):
            p = None
            try:
                p = spawn_tcp_server('127.0.0.1', TEST_PORT,
                                     (long_running, frozenset(['long_running']), frozenset(),
                                  connection_cb_dummy, 'Long-Running-Test', False))
                asyncio_run(run_tasks())
                assert sequence == [SLOW, FAST, FAST, SLOW], str(sequence)
            finally:
                stop_tcp_server('127.0.0.1', TEST_PORT)
                if p is not None:
                    p.join()
                sequence = []
            p = None
            try:
                p = spawn_tcp_server('127.0.0.1', TEST_PORT,
                                     (long_running, frozenset(), frozenset(['long_running']),
                                  connection_cb_dummy, 'Long-Running-Test', False))
                asyncio_run(run_tasks())
                assert sequence == [SLOW, FAST, FAST, SLOW], str(sequence)
            finally:
                stop_tcp_server('127.0.0.1', TEST_PORT)
                if p is not None:
                    p.join()
                sequence = []
        p = None
        try:
            p = spawn_tcp_server('127.0.0.1', TEST_PORT,
                                 (long_running, frozenset(), frozenset(),
                              connection_cb_dummy, 'Long-Running-Test', False))
            asyncio_run(run_tasks())
            assert sequence.count(SLOW) == 2 and sequence.count(FAST) == 2
        finally:
            stop_tcp_server('127.0.0.1', TEST_PORT)
            if p is not None:
                p.join()
            sequence = []


class TestSpawning:
    """Tests spawning a server by starting a script via subprocess.Popen."""

    def setup(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)

    def teardown(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)

    def test_spawn(self):
        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        spawn_tcp_server('127.0.0.1', TEST_PORT)
        async def identify():
            try:
                reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
                writer.write(IDENTIFY_REQUEST.encode())
                data = await reader.read(500)
                await writer.drain()
                writer.close()
                if sys.version_info >= (3, 7):  await writer.wait_closed()
                return data.decode()
            except ConnectionRefusedError:
                return ''

        result = asyncio_run(identify())
        assert result.startswith('DHParser'), result


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
        manager = multiprocessing.Manager()  # saving this in an object-variable would make objects unpickleable due to weak references
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
    def lsp_custom(self, *args, **kwargs):
        if args and not kwargs:
            return {'args': args}
        elif kwargs and not args:
            return kwargs
        else:
            return {'args': args, 'kwargs': kwargs }

    @lsp_rpc
    def lsp_check(self, **kwargs):
        return {'processId': self.shared.processId}

    @lsp_rpc
    def lsp_shutdown(self, **kwargs):
        self.shared.shutdown = True
        return {}

    def lsp_exit(self, **kwargs):
        self.shared.shutdown = True
        return None


class TestLanguageServer:
    """Tests for the generic LanguageServer-class."""

    def setup(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)
        self.p = None
        self.DEBUG = False
        if self.DEBUG:
            from DHParser import log
            log.start_logging('LOGS')
            set_config_value('log_server', True)

    def teardown(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)
        if self.p is not None:
            self.p.join()
        if self.DEBUG:
            from DHParser import log
            log.suspend_logging()

    def start_server(self):
        stop_tcp_server('127.0.0.1', TEST_PORT)
        if self.p is not None:
            self.p.join()
        self.lsp = LSP()
        lsp_table = gen_lsp_table(self.lsp, prefix='lsp_')
        self.p = spawn_tcp_server('127.0.0.1', TEST_PORT, (lsp_table, frozenset(), frozenset()))

    def test_initialize(self):
        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        self.start_server()

        async def sequence_test():
            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)

            async def send(request: str, expect_response: bool = True) -> str:
                writer.write(request.encode())
                await writer.drain()
                if expect_response:
                    return (await reader.read(8192)).decode()
                return ''
            response = await send(json_rpc('initialize',
                                             {'processId': 701,
                                              'rootUri': 'file://~/tmp',
                                              'capabilities': {}}))
            i = response.find('{') - 1
            res = json.loads(response[i:])
            assert 'result' in res and 'capabilities' in res['result'], str(res)

            r2, w2 = await asyncio_connect('127.0.0.1', TEST_PORT)
            w2.write(json_rpc('initialize', {'processId': 701,
                'rootUri': 'file://~/tmp', 'capabilities': {}}).encode())
            fail = await r2.read(8192)
            assert b'error' in fail and b'already connected' in fail
            w2.write_eof();  w2.close()
            if sys.version_info >= (3, 7):  await w2.wait_closed()

            r2, w2 = await asyncio_connect('127.0.0.1', TEST_PORT)
            w2.write(json_rpc('custom', {}).encode())
            fail = await r2.read(8192)
            assert b'result' not in fail
            assert b'not a service function' in fail
            w2.write_eof();  w2.close()
            if sys.version_info >= (3, 7):  await w2.wait_closed()

            response = await send(json_rpc('custom', {}))
            assert response.find('error') >= 0

            response = await send(json_rpc('initialized', {}), expect_response=False)
            assert response == '', response

            response = await send(json_rpc('custom', {'test': 1}))
            assert response.find('test') >= 0, str(response)

            response = await send(json_rpc('check', {}))
            assert response.find('701') >= 0

            response = await send(json_rpc('non_existant_function', {}))
            assert response.find('-32601') >= 0  # method not found
            response = await send(json_rpc('non_existant_function', {'a': 1, 'b': 2, 'c': 3}))
            assert response.find('-32601') >= 0  # method not found

            # test plain-data call
            response = await send('custom(1)')
            assert response.find('1') >= 0

            # test plain-data false call
            response = await send('non_existant_function()')
            assert response.find('No function named "non_extistant_function"')
            response = await send('non_existant_function(1)')
            assert response.find('No function named "non_extistant_function"')

            response = await send(json_rpc('shutdown', {}))
            assert response.find('error') < 0

            # after shutdown, any function call except "exit()" should yield error
            response = await send(json_rpc('custom', {}))
            assert response.find('error') >= 0

            response = await send(json_rpc('exit', {}))
            assert response == '', response

            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()

        asyncio_run(sequence_test())

    def test_initialization_sequence(self):
        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        self.start_server()
        async def initialization_sequence():
            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            writer.write(json_rpc('initialize',
                                  {'processId': 702,
                                   'rootUri': 'file://~/tmp',
                                   'capabilities': {}}).encode())
            response = (await reader.read(8192)).decode()
            i = response.find('{')
            res = json.loads(response[i:])
            assert 'result' in res and 'capabilities' in res['result'], str(res)

            writer.write(json_rpc('initialized', {}).encode())

            writer.write(json_rpc('custom', {'test': 1}).encode())
            response = (await reader.read(8192)).decode()
            assert response.find('test') >= 0

            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()

        asyncio_run(initialization_sequence())

    def test_varying_data_chunk_sizes(self):
        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        self.start_server()
        async def initialization_sequence():
            reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
            writer.write(json_rpc('initialize',
                                  {'processId': 702,
                                   'rootUri': 'file://~/tmp',
                                   'capabilities': {}}).encode())
            response = (await reader.read(8192)).decode()
            i = response.find('{')
            res = json.loads(response[i:])
            assert 'result' in res and 'capabilities' in res['result'], str(res)

            # several commands in one chunk
            writer.write(json_rpc('initialized', {}).encode() + json_rpc('custom', {'test': 1}).encode())
            response = (await reader.read(8192)).decode()
            assert response.find('test') >= 0

            data = json_rpc('custom', {'test': 2}).encode()
            i = data.find(b'\n\n')
            assert i > 0, str(data)
            writer.write(data[:i + 2])
            await asyncio.sleep(1)
            writer.write(data[i + 2:])
            response = (await reader.read(8192)).decode()
            assert response.find('test') >= 0

            data = json_rpc('custom', {'test': 3}).encode()
            i = data.find(b'\n\n')
            assert i > 0, str(data)
            writer.write(data[:i + 2])
            await asyncio.sleep(0.1)
            writer.write(data[i + 2:] + json_rpc('custom', {'test': 4}).encode())
            response = (await reader.read(8192)).decode()
            assert response.find('test') >= 0
            writer.write(b'')
            await writer.drain()
            writer.write_eof()
            await writer.drain()
            writer.close()
            if sys.version_info >= (3, 7):  await writer.wait_closed()

        asyncio_run(initialization_sequence())

    # def test_multiple_connections(self):
    #     self.start_server()
    #     async def initialization_sequence():
    #         reader, writer = await asyncio_connect('127.0.0.1', TEST_PORT)
    #         writer.write(json_rpc('initialize',
    #                               {'processId': 702,
    #                                'rootUri': 'file://~/tmp',
    #                                'capabilities': {}}).encode())
    #         response = (await reader.read(8192)).decode()
    #         i = response.find('{')
    #         # print(len(response), response)
    #         res = json.loads(response[i:])
    #         assert 'result' in res and 'capabilities' in res['result'], str(res)
    #
    #         writer.write(json_rpc('initialized', {}).encode())
    #
    #         writer.write(json_rpc('custom', {'test': 1}).encode())
    #         response = (await reader.read(8192)).decode()
    #         assert response.find('test') >= 0
    #
    #         writer.close()
    #         if sys.version_info >= (3, 7):  await writer.wait_closed()
    #
    #     asyncio_run(initialization_sequence())


if __name__ == "__main__":
    # BROKEN, because TEST_PORT ist not fixed any more
    # if "--killserver" in sys.argv:
    #     result = stop_tcp_server('127.0.0.1', TEST_PORT)
    #     print('server stopped' if result is None else "server wasn't running")
    #     sys.exit(0)
    from DHParser.testing import runner
    runner("", globals())
