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
import functools
import io
import json
import multiprocessing
import os
import sys
import time
from typing import Callable



from DHParser.server import Server, RPC_Type, StreamReaderProxy, StreamWriterProxy, STOP_SERVER_REQUEST_BYTES



def compiler_dummy(src: str, log_dir: str='') -> str:
    return src


def run_server_streams(rpc_functions: RPC_Type,
                       in_stream: io.BufferedIOBase,
                       out_stream: io.BufferedIOBase):
    reader = StreamReaderProxy(in_stream)
    writer = StreamWriterProxy(out_stream)
    server = Server(rpc_functions)
    print("starting server")
    server.handle(reader, writer)


class TestServerStream:
    def setup(self):
        if os.path.exists('test_identify.bin'):
            os.remove('test_identify.bin')

    def teardown(self):
        if os.path.exists('test_identify.bin'):
            os.remove('test_identify.bin')

    def test_identify(self):
        outs = open("test_identify.bin", 'wb')
        ins = open("test_identify.bin", 'rb')
        p = multiprocessing.Process(target=run_server_streams, args=(compiler_dummy, ins, outs))
        p.start()
        print('server-process up')
        outs.write(b'ECHO')
        print(ins.read())
        outs.write(STOP_SERVER_REQUEST_BYTES)
        print(ins.read())
        outs.close()
        ins.close()
        p.join()

