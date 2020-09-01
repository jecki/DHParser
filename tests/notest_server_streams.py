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
from concurrent.futures import ThreadPoolExecutor
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
    STOP_SERVER_REQUEST_BYTES, IDENTIFY_REQUEST_BYTES, JSONRPC_HEADER, asyncio_run, \
    RX_CONTENT_LENGTH, RE_DATA_START
from DHParser.toolkit import re_find


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
        self.data_waiting = threading.Event()
        self.data_waiting.clear()
        self.data = collections.deque()
        self._closed = False  # type: bool

    def close(self):
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed and not self.data

    def write(self, data: bytes):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        with self.lock:
            self.data.append(data)
            self.data_waiting.set()

    def writelines(self, data: List[bytes]):
        if self._closed:
            raise ValueError("I/O operation on closed file.")
        with self.lock:
            self.data.extend(data)
            self.data_waiting.set()

    def flush(self):
        pass

    def _read(self, n=-1) -> Union[List[bytes], Deque[bytes]]:
        with self.lock:
            if n < 0:
                self.data_waiting.clear()
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
                    self.data_waiting.clear()
                return data
            else:
                return [b'']

    def _readline(self) -> Union[List[bytes], Deque[bytes]]:
        with self.lock:
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
                self.data_waiting.clear()
            return data

    def read(self, n=-1) -> bytes:
        data = self._read(n)
        if n > 0:
            N = sum(len(chunk) for chunk in data)
            while N < n:
                self.data_waiting.wait()
                more = self._read(n)
                N += sum(len(chunk) for chunk in more)
                data.extend(more)
        return b''.join(data)

    def readline(self) -> bytes:
        data = self._readline()
        while not data or data[-1][-1] != ord(b'\n'):
            self.data_waiting.wait()
            data.extend(self._readline())
        return b''.join(data)


class TestServer:
    def setup(self):
        self.pipe = PipeStream()
        self.reader = StreamReaderProxy(self.pipe)
        self.writer = StreamWriterProxy(self.pipe)

    def teardown(self):
        self.writer.close()

    def test_pipe(self):
        message = b"alpha\nbeta\ngamma\n"

        def writer(pipe: PipeStream):
            nonlocal message
            for i in range(0, len(message), 2):
                pipe.write(message[i:i+2])

        def reader(pipe: PipeStream):
            nonlocal message
            received = []
            for i in range(3):
                received.append(pipe.readline())
            return b''.join(received)

        with ThreadPoolExecutor() as executor:
            future = executor.submit(reader, self.pipe)
            executor.submit(writer, self.pipe)
            assert future.result() == message

    def test_reader_writer(self):
        async def write(writer):
            writer.write(JSONRPC_HEADER % len(IDENTIFY_REQUEST_BYTES) + IDENTIFY_REQUEST_BYTES)
            await writer.drain()
            writer.close()

        async def read(reader):
            data = b''
            content_length = 0
            while not reader.at_eof():
                data += await reader.read(content_length or -1)
                i = data.find(b'Content-Length:', 0, 512)
                m = RX_CONTENT_LENGTH.match(data, i, i + 100) if i >= 0 else None
                if m:
                    content_length = int(m.group(1))
                    m2 = re_find(data, RE_DATA_START)
                    if m2:
                        header_size = m2.end()
                        if len(data) < header_size + content_length:
                            content_length = header_size + content_length - len(data)
                        else:
                            break
            return data

        async def main():
            read_task = asyncio.create_task(read(self.reader))
            write_task = asyncio.create_task(write(self.writer))
            data = await read_task
            await write_task
            return data

        data = asyncio_run(main())
        assert data == b'Content-Length: 10\r\n\r\nidentify()'
        assert self.pipe.closed


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
