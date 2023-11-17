from queue import Queue
import threading
from typing import Generator, Callable, List, Optional, Any

class Pipeline:
    def __init__(self, stages: List[Callable[[Any], int]]):
        self.stages = stages
        self.threads: List[threading.Thread] = []

    def _feed_from_generator(self, gen: Generator[Any, None, None], out_queue: Queue[Optional[int]]) -> None:
        for item in gen:
            out_queue.put(item)
        out_queue.put(None)

    def _stage_worker(self, in_queue: Queue[Optional[Any]], out_queue: Queue[Optional[Any]], function: Callable) -> None:
        while True:
            item = in_queue.get()
            result = function(item)
            if item is None: break
            out_queue.put(result)
        out_queue.put(None)

    def run(self, input_generator: Generator[Any, None, None]) -> Generator[Any, None, None]:
        queues = [Queue() for _ in range(len(self.stages) + 1)]

        # Create threads for the generator and stages
        thread = threading.Thread(target=self._feed_from_generator, args=(input_generator, queues[0]))
        thread.start()
        self.threads.append(thread)

        for i, function in enumerate(self.stages):
            thread = threading.Thread(target=self._stage_worker, args=(queues[i], queues[i + 1], function))
            thread.start()
            self.threads.append(thread)

        # Wait for all stages to finish
        for thread in self.threads:
            thread.join()

        # Return generator for final queue results
        def output_generator():
            while True:
                item = queues[-1].get()
                if item is None: return
                yield item

        return output_generator