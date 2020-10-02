#!/usr/bin/env pypy3

"""The ProcessPool example from the Python 3.7 documentation:
https://docs.python.org/3.7/library/concurrent.futures.html#processpoolexecutor-example

causes an OSError on exiting when run with pypy3 (PyPy 7.3.2-alpha0 with GCC 10.2.0)

Traceback (most recent call last):
  File "/opt/pypy3/lib-python/3/concurrent/futures/process.py", line 102, in _python_exit
    thread_wakeup.wakeup()
  File "/opt/pypy3/lib-python/3/concurrent/futures/process.py", line 90, in wakeup
    self._writer.send_bytes(b"")
  File "/opt/pypy3/lib-python/3/multiprocessing/connection.py", line 183, in send_bytes
    self._check_closed()
  File "/opt/pypy3/lib-python/3/multiprocessing/connection.py", line 136, in _check_closed
    raise OSError("handle is closed")

Probably, this is due to a bug in the standard library, concurrent/futures/process.py,
that has been corrected only in Python version 3.9.
"""

import concurrent.futures
import math

PRIMES = [
    112272535095293,
    112582705942171,
    112272535095293,
    115280095190773,
    115797848077099,
    1099726899285419]

def is_prime(n):
    if n % 2 == 0:
        return False

    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True

def main():
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for number, prime in zip(PRIMES, executor.map(is_prime, PRIMES)):
            print('%d is prime: %s' % (number, prime))

if __name__ == '__main__':
    main()
