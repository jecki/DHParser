#!/usr/bin/env python

import concurrent.futures
import os
import sys
import time


def test_f():
    result = 'json-module already imported? ' + str('json' in sys.modules)
    import json
    time.sleep(1)
    return result


def main():
    assert 'json' not in sys.modules
    print('start')

    cpus = os.cpu_count()
    futures = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpus) as executor:
        for _ in range(cpus * 3):
            futures.append(executor.submit(test_f))
        for future in futures:
            print(future.result())

    print('finished')


if __name__ == "__main__":
    main()
