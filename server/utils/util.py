import time
from typing import Any

class Timer:
    def __init__(self, name: str = 'Timer'):
        self.start = None
        self.end = None
        self.name = name

    def __enter__(self):
        print(f'[{self.name}] start')
        self.start = time.perf_counter()

    def __exit__(self, type, value, traceback):
        self.end = time.perf_counter()
        print(f'[{self.name}] end, elapsed time: {self.end - self.start:.4f}s')