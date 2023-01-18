
import concurrent.futures
import multiprocessing
import time

class CancelledError(Exception):
    def __init__(self, i=0):
        self.i = i

    def __repr__(self):
        return f"CancelledError({self.i})"

    def __str__(self):
        return f"CancelledError({self.i})"

# def init_pool(event):
#     global the_event
#     the_event = event
#     the_event.set()


def task(event) -> str:
    for i in range(10_000):
        time.sleep(1)
        if event.is_set():
            raise CancelledError(i)
    return "finished"


def run():
    manager = multiprocessing.Manager()
    try:
        event = manager.Event()
        # event = multiprocessing.Event()
        with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
            # print('initializing...')
            # res = pool.submit(init_pool, event)
            # print(event.is_set())
            # event.wait()
            # event.clear()
            # print('initialized')
            results = []
            print('submitting task...')
            results.append(pool.submit(task, event))
            results.append(pool.submit(task, event))
            print('waiting 5 seconds')
            time.sleep(5)
            event.set()
            concurrent.futures.wait(results)
            event.clear()
            for f in results:
                try:
                    print(f.result())
                except CancelledError as e:
                    print(e)
    finally:
        manager.shutdown()


if __name__ == "__main__":
    run()

