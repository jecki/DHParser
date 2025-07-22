#!/usr/bin/env python

import sys, os

script_dir = os.path.abspath(os.path.dirname(__file__))

class SomeClass:
    def __init__(self, val):
        self.val = val


def task(val) -> SomeClass:
    print(sys.path)
    obj = SomeClass(val)
    return obj

def initialize_interpreter():
    import sys
    print(sys.path)

class TestInterpreterPoolWrapper:
    def test_interpreterpool(self):
        if sys.version_info >= (3, 14, 0):
            from concurrent.futures import InterpreterPoolExecutor
            # save_pp = os.getenv("PYTHONPATH")
            # if save_pp:
            #     os.environ["PYTHONPATH"] = save_pp + ":" + script_dir
            # else:
            #     os.environ["PYTHONPATH"] = script_dir
            import interpreterpool
            with InterpreterPoolExecutor() as ex:
                result = ex.submit(interpreterpool.task, 20)
            # if save_pp:
            #     os.environ["PYTHONPATH"] = save_pp
            # else:
            #     os.unsetenv("PYTHONPATH")
            obj = result.result()
            assert obj.val == 20
            print("YO!")

    def test_wrapped_interpreterpool(self):
        pass


if __name__ == "__main__":
    sys.path.append(os.path.abspath('..'))
    from DHParser.testing import runner
    runner("", globals())