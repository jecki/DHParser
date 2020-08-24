#!/usr/bin/env python3

"""notest_server_streams.py - tests of the server module of DHParser,
    connection with streams.


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
import collections
import functools
import io
import json
import threading
import os
import sys
import time
from typing import Callable, List, Union, Deque


scriptpath = os.path.abspath(os.path.dirname(__file__) or '.')
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.server import Server, RPC_Type, StreamReaderProxy, StreamWriterProxy, \
    STOP_SERVER_REQUEST_BYTES, IDENTIFY_REQUEST_BYTES



def compiler_dummy(src: str, log_dir: str='') -> str:
    return src


# async def stdio(limit=asyncio.streams._DEFAULT_LIMIT, loop=None):
#     if loop is None:
#         loop = asyncio.get_event_loop()
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

class PipeStream:
    def __init__(self):
        self.lock = threading.Lock()
        self.data_wating = threading.Event()
        self.data_waiting.clear()
        self.data = collections.deque()
        self.closed = False  # type: bool

    def close(self):
        assert not self.closed
        self.data_wating.clear()
        self.data = collections.deque()
        self.closed = True

    def write(self, data: bytes):
        with self.lock.acquire():
            self.data.append(data)
            self.data_wating.set()

    def writelines(self, data: List[bytes]):
        with self.lock.acquire():
            self.data.extend(data)
            self.data_wating.set()

    def flush(self):
        pass

    def _read(self, n=-1) -> Union[List[bytes], Deque[bytes]]:
        with self.lock.acquire():
            if n < 0:
                self.data_wating.clear()
                if len(self.data) == 1:
                    return [self.data.popleft()]
                else:
                    data = self.data
                    while self.data:
                        self.data.pop()
                    return data
            elif n > 0:
                size = 0
                data = []
                while size < n and self.data:
                    i = len(self.data[0])
                    if size + i <= n:
                        data.append(self.data.popleft())
                        size += i
                    else:
                        cut = size + i - n
                        data.append(self.data[0][:cut])
                        self.data[0] = self.data[0][cut:]
                        size = n
                if not self.data:
                    self.data_wating.clear()
                return data
            else:
                return [b'']

    def _readline(self) -> Union[List[bytes], Deque[bytes]]:
        with self.lock.acquire():
            data = []
            while self.data:
                i = self.data[0].find(b'\n')
                if i < 0:
                    data.append(self.data.popleft())
                elif i == len(self.data[0]) - 1:
                    data.append(self.data.popleft())
                    break
                else:
                    data.append(self.data[0][:i + 1])
                    self.data[0] = self.data[0][i + 1:]
                    break
            if not self.data:
                self.data_wating.clear()
            return data

    def read(self, n=-1) -> bytes:
        data = self._read(n)
        if n > 0:
            N = sum(len(chunk) for chunk in data)
            while N < n:
                self.data_wating.wait()
                more = self._read(n)
                N += sum(len(chunk) for chunk in more)
                data.extend(more)
        return b''.join(data)

    def readline(self) -> bytes:
        data = self._readline()
        while data[-1][-1] != b'\n':
            self.data_wating.wait()
            data.extend(self._readline())
        return b''.join(data)


class TestServer:
    def setup(self):
        self.reader = ...


# async def run_server_streams(rpc_functions: RPC_Type,
#                        reader: asyncio.StreamReader,
#                        writer: asyncio.StreamWriter):
#     server = Server(rpc_functions)
#     await server.handle(reader, writer)
#
#
#
# class TestServerStream:
#
#     def test_identify(self):
#         stages = []
#
#         def pr(txt: str):
#             stages.append(txt)
#             print(txt)
#
#         async def echo(reader, writer):
#             nonlocal stages
#             pr('echo task')
#             writer.write(IDENTIFY_REQUEST_BYTES)
#             pr('echo: was geschrieben')
#             await writer.drain()
#             pr('echo: warte auf Antwort')
#             answer = await reader.read()
#             pr('echo Antwort: ' + str(answer))
#
#         async def main():
#             # if sys.platform.lower().startswith('win'):
#             reader = StreamReaderProxy(sys.stdin)
#             writer = StreamWriterProxy(sys.stdout)
#             # else:
#             #     reader, writer = await stdio()
#             server_task = asyncio.create_task(run_server_streams(compiler_dummy, reader, writer))
#             echo_task = asyncio.create_task(echo(reader, writer))
#             await echo_task
#             await server_task
#
#         asyncio.run(main())
#         print(stages)


# async def run_server_streams(rpc_functions: RPC_Type,
#                        in_stream: io.BufferedIOBase,
#                        out_stream: io.BufferedIOBase):
#     reader = StreamReaderProxy(in_stream)
#     writer = StreamWriterProxy(out_stream)
#     server = Server(rpc_functions)
#     print("starting server")
#     await server.handle(reader, writer)

# class TestServerStream:
#
#     def test_identify(self):
#
#         outs = sys.stdout
#         print(type(outs))
#         ins = sys.stdin
#
#         # p = threading.Process(target=run_server_streams, args=(compiler_dummy, ins, outs))
#         # p.start()
#
#         async def echo():
#             print('echo task')
#             outs.write('ECHO')
#             print('\n1')
#             outs.flush()
#             print("Echo written, now waiting")
#             await asyncio.sleep(5)
#             print('echo written')
#             print(ins.read())
#             print('write stop-request')
#             outs.write(STOP_SERVER_REQUEST_BYTES)
#             print('stop-request written')
#             print(ins.read())
#             print('echo result')
#             outs.close()
#             ins.close()
#
#         async def main():
#             server_task = asyncio.create_task(run_server_streams(compiler_dummy, ins, outs))
#             print('server-task created')
#             echo_task = asyncio.create_task(echo())
#             print('echo-task created')
#             print('await server-task')
#             await server_task
#             print('await echo-task')
#             await echo_task
#             print('end of main')
#
#         asyncio.run(main())
#         # p.join()

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
