#!/usr/bin/env python

import sys, os

script_dir = os.path.abspath(os.path.dirname(__file__))

class SomeClass:
    def __init__(self, val):
        self.val = val


def task(val) -> SomeClass:
    obj = SomeClass(val)
    return obj


class TestInterpreterPoolWrapper:
    def test_interpreterpool(self):
        if sys.version_info >= (3, 14, 0):
            from concurrent.futures import InterpreterPoolExecutor
            if __name__ != '__main__':
                os.chdir('..')
                import scratch.interpreterpool as interpreterpool
            else:
                import interpreterpool
            with InterpreterPoolExecutor() as ex:
                result = ex.submit(interpreterpool.task, 20)
            obj = result.result()
            assert obj.val == 20

    def test_wrapped_interpreterpool(self):
        if sys.version_info >= (3, 14, 0):
            from concurrent.futures import InterpreterPoolExecutor
            if __name__ != '__main__':
                os.chdir('..')
                import scratch.interpreterpool as interpreterpool
            else:
                import interpreterpool
            from DHParser.toolkit import InterpreterPoolWrapper
            with InterpreterPoolWrapper(InterpreterPoolExecutor()) as ex:
                result = ex.submit(interpreterpool.task, 20)
            print(type(result))
            obj = result.result()
            assert obj.val == 20


if __name__ == "__main__":
    sys.path.append(os.path.abspath('..'))
    from DHParser.testing import runner
    runner("", globals())