
class SelfTest:
    def setup(self):
        print("setup")

    def teardown(self):
        print("teardown")

    def test1(self):
        print("test1")

    def test2(self):
        print("test2")


def run_tests(tests, namespace):
    """ Runs only some selected tests from a test suite.

    Args:
        tests: Either a string or a list of strings that contains the
            names of test or test classes. Each test and, in the case
            of a test class, all tests within the test class will be
            run.
        namespace: The namespace for running the test, usually 
            ``globals()`` should be used.
    """
    def instantiate(cls_name):
        exec("obj = " + cls_name + "()", namespace)
        obj = namespace["obj"]
        if "setup" in dir(obj):
            obj.setup()
        return obj

    if isinstance(tests, str):
        tests = tests.split(" ")
    for test in tests:
        if test.find('.') >= 0:
            cls_name, method_name = test.split('.')
            obj = instantiate(cls_name)
            print("Running " + cls_name + "." + method_name)
            exec('obj.' + method_name + '()')
        else:
            obj = instantiate(test)
            for name in dir(obj):
                if name.lower().startswith("test"):
                    print("Running " + test + "." + name)
                    exec('obj.' + name + '()')
        if "teardown" in dir(obj):
            obj.teardown()

if __name__ == "__main__":
    # run_tests("SelfTest.test1 SelfTest")
    import os
    os.system("nosetests")
