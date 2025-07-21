import sys

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
            with InterpreterPoolExecutor() as ex:
                result = ex.submit(task, 20)
            obj = result.result()
            assert obj.val == 20

    def test_wrapped_interpreterpool(self):
        pass


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())