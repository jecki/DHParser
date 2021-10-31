#!/usr/bin/env python3

"""test_server_streams.py - tests of the server module of DHParser,
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
from concurrent.futures import ThreadPoolExecutor
import threading
import os
import sys

scriptpath = os.path.abspath(os.path.dirname(__file__) or '.')
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.server import StreamReaderProxy, StreamWriterProxy, \
    IDENTIFY_REQUEST_BYTES, JSONRPC_HEADER_BYTES, asyncio_run, \
    spawn_stream_server, stop_stream_server, split_header
from DHParser.testing import read_full_content, add_header, MockStream


class TestStreamProxies:
    def setup(self):
        self.pipe = MockStream()
        self.reader = StreamReaderProxy(self.pipe)
        self.writer = StreamWriterProxy(self.pipe)

    def teardown(self):
        self.writer.close()

    def test_pipe(self):
        message = b"alpha\nbeta\ngamma\n"

        def writer(pipe: MockStream):
            nonlocal message
            for i in range(0, len(message), 2):
                pipe.write(message[i:i+2])
                pipe.flush()

        def reader(pipe: MockStream):
            nonlocal message
            received = []
            for i in range(3):
                received.append(pipe.readline())
            return b''.join(received)

        with ThreadPoolExecutor() as executor:
            future = executor.submit(reader, self.pipe)
            executor.submit(writer, self.pipe)
            assert future.result() == message

    def test_reader_writer_simple(self):
        async def main():
            self.writer.write(b'Hello\n')
            await self.writer.drain()
            data = await self.reader.read()
            self.writer.close()
            return data

        data = asyncio_run(main())
        assert data == b'Hello\n', str(data)
        assert self.pipe.closed

    def test_reader_writer(self):
        async def write(writer):
            writer.write(JSONRPC_HEADER_BYTES % len(IDENTIFY_REQUEST_BYTES) + IDENTIFY_REQUEST_BYTES)
            await writer.drain()

        async def read(reader):
            return await read_full_content(reader)

        async def main():
            if sys.version_info >= (3, 7):
                read_task = asyncio.create_task(read(self.reader))
                write_task = asyncio.create_task(write(self.writer))
            else:
                read_task = asyncio.ensure_future(read(self.reader))
                write_task = asyncio.ensure_future(write(self.writer))
            data = await read_task
            await write_task
            self.writer.close()
            return data

        data = asyncio_run(main())
        assert data == b'Content-Length: 10\r\n\r\nidentify()', str(data)
        assert self.pipe.closed


TRANS_TABLE = {ord(ch): ord(ch.upper()) for ch in 'abcdefghijklmnopqrstuvwxzy'}
TRANS_TABLE.update({ord(ch): ord(ch.lower()) for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXZY'})

def mock_compiler(src: str, log_dir: str='') -> str:
    return src.translate(TRANS_TABLE)


class TestServer:
    def setup(self):
        self.pipeA = MockStream('pipeA')
        self.pipeB = MockStream('pipeB')
        self.readerA = StreamReaderProxy(self.pipeA)
        self.writerA = StreamWriterProxy(self.pipeA)
        self.readerB = StreamReaderProxy(self.pipeB)
        self.writerB = StreamWriterProxy(self.pipeB)

    def teardown(self):
        self.writerA.close()
        self.writerB.close()

    def test_server_process(self):
        """Basic Test of server module."""
        async def compile_remote(src, reader, writer) -> bytes:
            writer.write(add_header(src.encode()))
            await writer.drain()
            data = await read_full_content(reader)
            # writer.close()
            # if sys.version_info >= (3, 7):  await writer.wait_closed()
            header, data, backlog = split_header(data)
            return data.decode()
            # assert data.decode() == "Test", data.decode()

        try:
            from _ctypes import Union, Structure, Array
        except ImportError:
            print('Skipping Test, because libffi has wrong version or does not exist!')
            return

        p = None
        try:
            p = spawn_stream_server(self.readerA, self.writerB,
                                    (mock_compiler, set()), threading.Thread)
            data = asyncio_run(compile_remote('Test', self.readerB, self.writerA))
            assert data == "tEST"
        finally:
            if p is not None:
                stop_stream_server(self.readerB, self.writerA)
                p.join()


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
