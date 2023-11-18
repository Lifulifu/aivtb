import asyncio
from typing import Callable, List, Any, Optional

class AsyncSequentialWorker():
    def __init__(self, process_task: Callable, in_queue=None, out_queue=None, cooldown=0):
        self.process_task = process_task
        self.in_queue = asyncio.Queue() if in_queue is None else in_queue
        self.out_queue = out_queue
        self.cooldown = cooldown

    async def run(self):
        while True:
            task = await self.in_queue.get()
            result = await self.process_task(task)

            if self.out_queue:
                await self.out_queue.put(result)

            self.in_queue.task_done()

            if self.cooldown > 0:
                await asyncio.sleep(self.cooldown)

    def start(self):
        self.worker = asyncio.create_task(self.run())

    async def submit(self, task: Any):
        await self.in_queue.put(task)

    async def end(self):
        if self.worker:
            self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)

class AsyncPipelineWorker():
    def __init__(self, process_tasks: List[Callable], in_queue: Optional[asyncio.Queue] = None, out_queue: Optional[asyncio.Queue] = None):
        self.in_queue = in_queue or asyncio.Queue()
        self.out_queue = out_queue
        self.workers = []
        self._create_pipeline(process_tasks)

    def _create_pipeline(self, process_tasks: List[Callable]):
        queue = self.in_queue
        for i, process_task in enumerate(process_tasks):
            # For the last task, use the specified out_queue if provided
            next_queue = self.out_queue if i == len(process_tasks) - 1 else asyncio.Queue()
            worker = AsyncSequentialWorker(process_task, queue, next_queue if process_task != process_tasks[-1] else None)
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

    async def join(self):
        # Optionally wait for all tasks to be processed
        if self.workers:
            await self.workers[-1].in_queue.join()
