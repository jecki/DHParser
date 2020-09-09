import asyncio
import json
import os
import sys
import threading

testpath = os.path.abspath(os.path.dirname(__file__))
mainpath = os.path.dirname(testpath)
dhparserpath = os.path.dirname(os.path.dirname(mainpath))

sys.path.append(mainpath)

from DHParser.error import ERROR
from DHParser.server import ExecutionEnvironment, asyncio_run, Server, StreamReaderProxy, \
    StreamWriterProxy

import EBNFServer, EBNFParser


class TestCPUBoundTasks:
    def test_cpubound(self):
        diagnostics = EBNFServer.compile_EBNF('')
        json_obj = json.loads(diagnostics)
        assert json_obj[0]['code'] >= ERROR
        diagnostics = EBNFServer.compile_EBNF('document = /.*/')
        assert diagnostics == '[]'

    def test_compile_process(self):
        async def main():
            loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            exec = ExecutionEnvironment(loop)

            diagnostics, rpc_error = await exec.execute(
                exec.process_executor, EBNFServer.compile_EBNF, ('',)
            )
            json_obj = json.loads(diagnostics)
            assert json_obj[0]['code'] >= ERROR

            diagnostics, rpc_error = await exec.execute(
                exec.process_executor, EBNFServer.compile_EBNF, ('document = /.*/',)
            )
            assert diagnostics == '[]'

            diagnostics, rpc_error = await exec.execute(
                exec.thread_executor, EBNFServer.compile_EBNF, ('',)
            )
            json_obj = json.loads(diagnostics)
            assert json_obj[0]['code'] >= ERROR

            diagnostics, rpc_error = await exec.execute(
                exec.thread_executor, EBNFServer.compile_EBNF, ('document = /.*/',)
            )
            assert diagnostics == '[]'

            exec.shutdown()

        asyncio_run(main())


    def test_compileEBNFFork(self):
        fname = '/home/eckhart/Entwicklung/DHParser/examples/EBNF_fork/FixedEBNF.ebnf'
        with open(fname, 'r') as f:
            source = f.read()
        diagnostics = EBNFServer.compile_EBNF(source)
        print(json.dumps(json.loads(diagnostics), indent=2))


class TestServer:
    def setup(self):
        EBNF_lsp = EBNFServer.EBNFLanguageServerProtocol()
        lsp_table = EBNF_lsp.lsp_fulltable.copy()
        lsp_table.setdefault('default', EBNFParser.compile_src)
        self.EBNF_server = Server(rpc_functions=lsp_table,
                                  cpu_bound=set(EBNF_lsp.cpu_bound.lsp_table.keys()),
                                  blocking=set(EBNF_lsp.blocking.lsp_table.keys()),
                                  connection_callback=EBNF_lsp.connect,
                                  server_name='EBNFServer',
                                  strict_lsp=True)

    def test_server_processes(self):
        reader = StreamReaderProxy(sys.stdin)
        writer = StreamWriterProxy(sys.stdout)
        p = threading.Thread(self.EBNF_server.run_stream_server, (reader, writer))
        # p.start()
        # writer.write(...)
        # ... = reader.read()
        # p.join()



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
