from queue import Queue
import threading
from typing import Generator, Callable, List, Optional

class Pipeline:
    def __init__(self, input_generator: Callable[[], Generator[int, None, None]], stages: List[Callable[[int], int]]):
        self.input_generator = input_generator
        self.stages = stages

    def _feed_from_generator(self, gen: Generator[int, None, None], out_queue: Queue[Optional[int]]) -> None:
        for item in gen:
            out_queue.put(item)
        out_queue.put(None)

    def _stage_worker(self, in_queue: Queue[Optional[int]], out_queue: Queue[Optional[int]], function: Callable[[int], int]) -> None:
        while True:
            item = in_queue.get()
            if item is None: break
            result = function(item)
            out_queue.put(result)
        out_queue.put(None)

    def run(self) -> Generator[int, None, None]:
        queues = [Queue() for _ in range(len(self.stages) + 1)]

        # Create threads for the generator and stages
        threading.Thread(target=self._feed_from_generator, args=(self.input_generator, queues[0])).start()

        for i, function in enumerate(self.stages):
            threading.Thread(target=self._stage_worker, args=(queues[i], queues[i + 1], function)).start()

        # Return generator for final queue results
        def output_generator():
            while True:
                item = queues[-1].get()
                if item is None: return
                yield item

        return output_generator