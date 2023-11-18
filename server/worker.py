import asyncio
from typing import Callable, List, Any

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
    def __init__(self, stages: List[Callable], in_queue=None, out_queue=None, cooldown=0):
        self.stages = stages
        self.in_queue = asyncio.Queue() if in_queue is None else in_queue
        self.out_queue = out_queue
        self.cooldown = cooldown
        self.workers = self._create_workers()

    def _create_workers(self):
        workers = []
        next_in_queue = self.in_queue

        for stage in self.stages[:-1]:
            next_out_queue = asyncio.Queue()
            worker = AsyncSequentialWorker(process_task=stage, in_queue=next_in_queue, out_queue=next_out_queue, cooldown=self.cooldown)
            workers.append(worker)
            next_in_queue = next_out_queue

        final_worker = AsyncSequentialWorker(
            process_task=self.stages[-1], in_queue=next_in_queue, out_queue=self.out_queue, cooldown=self.cooldown)
        workers.append(final_worker)

        return workers

    async def start(self):
        for worker in self.workers:
            worker.start()

    async def submit(self, task: Any):
        await self.workers[0].submit(task)

    async def end(self):
        for worker in self.workers:
            await worker.end()