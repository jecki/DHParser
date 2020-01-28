#!/usr/bin/env python

import functools, asyncio, multiprocessing, time, concurrent.futures

class Work:
    def __init__(self):
        manager = multiprocessing.Manager()
        self.data = manager.dict()
        self.data.update({'a': 1, 'b': 2})
        self.shared = manager.Namespace()
        self.shared.a = 1

    def do_alt(self, start: int):
        for n in range(5):
            i = self.data['a']
            print(start + n, 'a:', i)
            self.data['a'] = i + 1
            time.sleep(0.5 + start / 40)
        return self.data['a']

    def do(self, start: int):
        for n in range(5):
            i = self.shared.a
            print(start + n, 'a:', i)
            self.shared.a = i + 1
            time.sleep(0.5 + start / 40)
        return self.shared.a


async def execute(executor, method, params):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, functools.partial(method, **params))
    return result


async def main(work):
    with concurrent.futures.ProcessPoolExecutor() as pool:
        task1 = asyncio.ensure_future(execute(pool, work.do, {'start': 10}))
        task2 = asyncio.ensure_future(execute(pool, work.do, {'start': 20}))
        for res in await asyncio.gather(task1, task2):
            print(res)

if __name__ == '__main__':
    work = Work()
    asyncio.run(main(work))



