from typing import Callable
import asyncio
import inspect

class EventManager:
    def __init__(self):
        self.subscribers: dict[str, list] = dict()

    def subscribe(self, event: str, func: Callable):
        if not event in self.subscribers:
            self.subscribers[event] = []
        self.subscribers[event].append(func)

    def unsubscribe(self, event: str, func: Callable):
        if event in self.subscribers:
            self.subscribers[event].remove(func)

    def publish(self, event: str, *args):
        if event in self.subscribers:
            for func in self.subscribers[event]:
                if inspect.iscoroutinefunction(func):
                    asyncio.run(func(*args))
                else:
                    func(*args)
