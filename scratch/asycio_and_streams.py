import asyncio
import os
import sys


logfile = open('log_asyncio_and_streams.txt', 'w')

def log(txt: str):
    logfile.write(txt)
    logfile.flush()


log('asyncio_and_streams progress log:\n\n')


async def long_running():
    log('enter long_running()\n')
    await asyncio.sleep(0.05)
    log('long_running: 1\n')
    await asyncio.sleep(0.05)
    log('long_running: 2\n')
    await asyncio.sleep(0.05)
    log('exit long_running()\n')


def read_from_stdin():
    log('enter read_from_stdin()\n')
    data = sys.stdin.read()
    logfile.write('read_from_stdin: read: ' + str(data) + '\n')
    return data


async def blocking():
    log('enter blocking()\n')   
    loop = asyncio.get_running_loop()
    log('blocking: running read task in separate thread\n')
    data = await loop.run_in_executor(None, read_from_stdin)
    log('blocking: received: ' + str(data) + '\n')
    return data


async def main():
    log('enter main()\n')
    task1 = asyncio.create_task(long_running())
    log('main: task long_running created\n')
    task2 = asyncio.create_task(blocking())
    log('main: task blocking created\n')
    await task2
    log('main: in between two awaits\n')
    await task1
    log('exit main()\n')


log('starting main coroutine\n')
import atexit
atexit.register(logfile.close)
asyncio.run(main())

