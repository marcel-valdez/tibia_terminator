#!/usr/bin/env python3.8


from typing import Callable, TypeVar, Generic
from threading import Thread, Lock, Event
from queue import Queue

T = TypeVar("T")


class LazyEvaluator(Generic[T], Thread):
    def __init__(self, fn: Callable[[], T],
                 cb: Callable[[T, Exception], None]):
        super().__init__(daemon=False)
        self.fn = fn
        self.cb = cb

    def run(self):
        value = None
        error = None
        try:
            value = self.fn()
        except Exception as e:
            error = e
        finally:
            self.cb(value, error)


class LazyValueNotReadyError(Exception):
    pass


M = TypeVar("M")

class FutureValue(Generic[M]):
    def __init__(self):
        self._result_ready_event = Event()

    def set_result(self, value: M, error: Exception):
        self.value = value
        self.error = error
        self._result_ready_event.set()

    def __get(self):
        if self.error is not None:
            raise self.error
        else:
            return self.value

    def get(self, timeout_sec: float = None) -> M:
        if not self._result_ready_event.is_set():
            if not self._result_ready_event.wait(timeout_sec):
                raise LazyValueNotReadyError()

        return self.__get()

class FutureValueAsync(FutureValue[M]):
    def __init__(self, getter: Callable[[], M]):
        super().__init__()
        self.lazy_evaluator = LazyEvaluator(getter, self.set_result)

    def start(self):
        """Starts fetching the value asynchronously."""
        if not self._result_ready_event.is_set() and not self.lazy_evaluator.is_alive():
            self.lazy_evaluator.start()
        return self


N = TypeVar("N")


class LazyValue(Generic[N]):
    def __init__(self, getter: Callable[[], N]):
        self.getter = getter
        self.value_ready_event = Event()
        self.value = None
        self.error = None
        self.lock = Lock()

    def __evaluate(self):
        if not self.value_ready_event.is_set():
            self.lock.acquire()
            if not self.value_ready_event.is_set():
                try:
                    self.value = self.getter()
                except Exception as e:
                    self.error = e
                finally:
                    self.value_ready_event.set()
            self.lock.release()

    def __get(self) -> N:
        if self.error is not None:
            raise self.error
        else:
            return self.value

    def get(self, timeout_sec: float = None) -> N:
        if not self.value_ready_event.is_set():
            self.__evaluate()
            if not self.value_ready_event.wait(timeout_sec):
                raise LazyValueNotReadyError()

        return self.__get()


class TaskLoop(Thread):
    """Daemon thread that executes tasks that provide Future values."""
    STOP = "__STOP__TaskLoop"
    task_queue: Queue = None
    cancel_pending_tasks: bool = False

    def __init__(self, task_queue: Queue = None):
        super().__init__(daemon=True)
        self.task_queue = Queue()

    def cancel_pending_tasks(self):
        """Cancels pending tasks by clearing them."""
        self.task_queue = Queue()

    def stop(self):
        """Completely stops this task loop and becomes unusable."""
        self.task_queue.put_nowait(TaskLoop.STOP)

    def run(self):
        while True:
            next_task = self.task_queue.get()
            if next_task is TaskLoop.STOP:
                self.cancel_pending_tasks()
                break
            else:
                next_task()

    def add_task(self, task: Callable[[], None]):
        self.task_queue.put_nowait(task)

    def add_future(self, getter: Callable[[], M]) -> FutureValue[M]:
        """Creates a future value that will be set by this task loop."""
        future_value = FutureValue()
        def task():
            try:
                value = getter()
                future_value.set_result(value, None)
            except Exception as e:
                future_value.set_result(None, e)
        self.add_task(task)
        return future_value


K = TypeVar("K")


def lazy(getter: Callable[[], K]) -> LazyValue[K]:
    return LazyValue(getter)


def future(getter: Callable[[], K]) -> FutureValue[K]:
    future_value = FutureValueAsync(getter)
    future_value.start()
    return future_value
