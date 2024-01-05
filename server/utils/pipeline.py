import threading
from typing import Callable, List
from dataclasses import dataclass
import types
from queue import Queue
import time
from utils.event import EventManager

@dataclass
class PipelineStage:
    run: Callable
    pre_process_delay: float = 0
    post_process_delay: float = 0

class Worker(threading.Thread):
    def __init__(self, stage: PipelineStage, in_queue: Queue, out_queue: Queue, event_manager: EventManager = None):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.stage = stage
        self.events = event_manager

    def run(self):
        while True:
            task = self.in_queue.get()
            if task is None: break
            if self.events:
                self.events.publish(f'{self.stage.run.__name__}:start', task)

            if self.stage.pre_process_delay > 0: time.sleep(self.stage.pre_process_delay)
            try:
                result = self.stage.run(task)
            except Exception as e:
                print(f'[{self.stage.run.__name__}] error:', e)
                result = None
            if self.stage.post_process_delay > 0: time.sleep(self.stage.post_process_delay)

            if isinstance(result, types.GeneratorType):
                for item in result:
                    self.out_queue.put(item)
                    if self.events:
                        self.events.publish(f'{self.stage.run.__name__}:end', task, item)
            elif result is not None:
                self.out_queue.put(result)
                if self.events:
                    self.events.publish(f'{self.stage.run.__name__}:end', task, result)
            else: # abort this task by not putting anything into the next queue
                if self.events:
                    self.events.publish(f'{self.stage.run.__name__}:abort', task)

            self.in_queue.task_done()


class Pipeline():
    def __init__(self, stages: List[PipelineStage], in_queue: Queue = None, out_queue: Queue = None):
        self.in_queue = in_queue if in_queue is not None else Queue()
        self.out_queue = out_queue if out_queue is not None else Queue()
        self.workers: List[Worker] = []
        self.events = EventManager()
        self._create_pipeline(stages)

    def _create_pipeline(self, stages: List[Callable]):
        queue = self.in_queue
        for i, stage in enumerate(stages):
            # For the last task, use the specified out_queue if provided
            if i == len(stages) - 1:
                next_queue = self.out_queue
            else:
                next_queue = Queue()
            worker = Worker(stage, queue, next_queue, event_manager=self.events)
            self.workers.append(worker)
            queue = next_queue

    def submit(self, task):
        self.in_queue.put(task)

    def start(self):
        for worker in self.workers:
            worker.start()

    def end(self):
        for worker in self.workers:
            worker.join()

if __name__ == '__main__':
    def input_generator():
        for i in range(3):
            time.sleep(1)
            yield f'task{i}'

    def func1(task):
        time.sleep(1)
        yield task + ' -> stage1(1)'
        time.sleep(1)
        yield task + ' -> stage1(2)'

    def func2(task):
        time.sleep(2)
        return task + ' -> stage2'

    in_queue = Queue()
    stages = [
        PipelineStage(run=func1),
        PipelineStage(run=func2, post_process_delay=1),
    ]
    pipeline = Pipeline(stages, in_queue)
    pipeline.events.subscribe('func1:start', lambda task: print(f'func1:start {task}'))
    pipeline.events.subscribe('func2:start', lambda task: print(f'func2:start {task}'))
    pipeline.start()

    for task in input_generator():
        in_queue.put(task)