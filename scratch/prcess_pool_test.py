# bug in pypy3.6 ?  -> OSError

import concurrent.futures
import multiprocessing

def task(i):
    import time
    time.sleep(i)
    return i

with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
    results = []
    for i in range(3):
        results.append(pool.submit(task, i))

    concurrent.futures.wait(results)
    for f in results:
        print(f.result())



