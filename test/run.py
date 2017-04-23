import inspect


class SelfTest:
    def setup(self):
        print("setup")

    def teardown(self):
        print("teardown")

    def test1(self):
        print("test1")

    def test2(self):
        print("test2")


def runner(tests, namespace):
    """ Runs only some selected tests from a test suite. To run all
    tests in a module, call ``runner("", globals())`` from within
    that module.

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

    if tests:
        if isinstance(tests, str):
            tests = tests.split(" ")
    else:
        # collect all test classes, in case no methods or classes have been passed explicitly
        tests = []
        for name in namespace.keys():
            if name.lower().startswith('test') and inspect.isclass(namespace[name]):
                tests.append(name)

    obj = None
    for test in tests:
        try:
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
        finally:
            if "teardown" in dir(obj):
                obj.teardown()

if __name__ == "__main__":
    # runner("", globals())
    # runner("TestSelf.test1 TestSelf", globals())
    import os

    os.chdir('..')
    print("Running nosetests:")
    os.system("nosetests")
