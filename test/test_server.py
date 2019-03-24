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
import os
from multiprocessing import Process
import sys
from typing import Tuple

sys.path.extend(['../', './'])

from DHParser.server import Server


scriptdir = os.path.dirname(os.path.realpath(__file__))


def compiler_dummy(src: str, log_dir: str) -> Tuple[str, str]:
    return (src, log_dir)


class TestServer:
    # def test_server(self):
    #     cs = Server(compiler_dummy)
    #     cs.run_server()

    def test_server_proces(self):
        cs = Server(compiler_dummy, cpu_bound=set())
        cs.run_as_process()

        async def compile(src, log_dir):
            reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
            writer.write(src.encode())
            data = await reader.read(500)
            print(f'Received: {data.decode()!r}')
            writer.close()

        asyncio.run(compile('Test', ''))
        cs.terminate_server_process()
        cs.wait_for_termination_request()

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
