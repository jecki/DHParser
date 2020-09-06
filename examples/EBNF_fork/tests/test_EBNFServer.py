import asyncio
import json
import os
import sys

testpath = os.path.abspath(os.path.dirname(__file__))
mainpath = os.path.dirname(testpath)
dhparserpath = os.path.dirname(os.path.dirname(mainpath))

print(dhparserpath)

sys.path.append(mainpath)

from DHParser.error import ERROR
from DHParser.server import ExecutionEnvironment, asyncio_run
from DHParser.toolkit import json_dumps, json_rpc

import EBNFServer


class TestCPUBoundTasks:
    def test_cpubound(self):
        cpu_bound = EBNFServer.EBNFCPUBoundTasks({})
        diagnostics = cpu_bound.compile_EBNF('')
        json_obj = json.loads(diagnostics)
        assert json_obj[0]['code'] >= ERROR
        diagnostics = cpu_bound.compile_EBNF('document = /.*/')
        assert diagnostics == '[]'

    def test_compile_process(self):
        cpu_bound = EBNFServer.EBNFCPUBoundTasks({})

        async def main():
            loop = asyncio.get_running_loop() if sys.version_info >= (3, 7) \
                else asyncio.get_event_loop()
            exec = ExecutionEnvironment(loop)

            diagnostics, rpc_error = await exec.execute(
                exec.process_executor, cpu_bound.compile_EBNF, ('',)
            )
            json_obj = json.loads(diagnostics)
            assert json_obj[0]['code'] >= ERROR

            diagnostics, rpc_error = await exec.execute(
                exec.process_executor, cpu_bound.compile_EBNF, ('document = /.*/',)
            )
            assert diagnostics == '[]'

            diagnostics, rpc_error = await exec.execute(
                exec.thread_executor, cpu_bound.compile_EBNF, ('',)
            )
            json_obj = json.loads(diagnostics)
            assert json_obj[0]['code'] >= ERROR

            diagnostics, rpc_error = await exec.execute(
                exec.thread_executor, cpu_bound.compile_EBNF, ('document = /.*/',)
            )
            assert diagnostics == '[]'

            exec.shutdown()

        asyncio_run(main())


    def test_compileEBNFFork(self):
        fname = '/home/eckhart/Entwicklung/DHParser/examples/EBNF_fork/FixedEBNF.ebnf'
        with open(fname, 'r') as f:
            source = f.read()
        cpu_bound = EBNFServer.EBNFCPUBoundTasks({})
        diagnostics = cpu_bound.compile_EBNF(source)
        print(json.dumps(json.loads(diagnostics), indent=2))


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
