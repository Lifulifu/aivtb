import asyncio
from typing import Callable, List, Any, Optional

class AsyncSequentialWorker():
    def __init__(self, process_task: Callable, in_queue=None, out_queue=None, cooldown=0, debug=False, name=''):
        self.process_task = process_task
        self.in_queue = asyncio.Queue() if in_queue is None else in_queue
        self.out_queue = out_queue
        self.cooldown = cooldown
        self.debug = debug
        self.name = name

    async def run(self):
        while True:
            task = await self.in_queue.get()
            if self.debug: print(f'[{self.name}] get task:', task)

            result = await self.process_task(task)
            if self.debug: print(f'[{self.name}] finish task:', task)

            if self.out_queue:
                await self.out_queue.put(result)
                if self.debug: print(f'[{self.name}] out_queue size:', self.out_queue.qsize())

            self.in_queue.task_done()
            if self.cooldown > 0: await asyncio.sleep(self.cooldown)

    def start(self):
        self.worker = asyncio.create_task(self.run())

    async def submit(self, task: Any):
        await self.in_queue.put(task)

    async def end(self):
        if self.worker:
            self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)

class AsyncPipelineWorker():
    def __init__(self, process_tasks: List[Callable], in_queue: Optional[asyncio.Queue] = None, out_queue: Optional[asyncio.Queue] = None, debug = False, process_task_names = []):
        self.in_queue = in_queue or asyncio.Queue()
        self.out_queue = out_queue
        self.workers = []
        self.debug = debug
        self.process_task_names = process_task_names
        self._create_pipeline(process_tasks)

    def _create_pipeline(self, process_tasks: List[Callable]):
        queue = self.in_queue
        for i, process_task in enumerate(process_tasks):
            # For the last task, use the specified out_queue if provided
            if i == len(process_tasks) - 1:
                next_queue = self.out_queue if self.out_queue is not None else None
            else:
                next_queue = asyncio.Queue()
            worker_name = self.process_task_names[i] if self.debug else ''
            worker = AsyncSequentialWorker(process_task, queue, next_queue, debug=self.debug, name=worker_name)
            self.workers.append(worker)
            queue = next_queue

    def start(self):
        for worker in self.workers:
            worker.start()

    async def submit(self, task: Any):
        await self.in_queue.put(task)

    async def end(self):
        for worker in self.workers:
            await worker.end()