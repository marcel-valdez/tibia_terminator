#!/usr/bin/env python3.8


from typing import Callable, TypeVar, Generic
from threading import Thread, Lock, Event

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
    def __init__(self, getter: Callable[[], M]):
        self.lazy_evaluator = LazyEvaluator(getter, self.__done_callback)
        self.value_ready_event = Event()

    def __done_callback(self, value: M, error: Exception):
        self.value = value
        self.error = error
        self.value_ready_event.set()

    def start(self):
        """Starts fetching the value asynchronously."""
        if not self.value_ready_event.is_set() and not self.lazy_evaluator.is_alive():
            self.lazy_evaluator.start()
        return self

    def __get(self) -> M:
        if self.error is not None:
            raise self.error
        else:
            return self.value

    def get(self, timeout_sec: float = None) -> M:
        if not self.value_ready_event.is_set():
            if not self.value_ready_event.wait(timeout_sec):
                raise LazyValueNotReadyError()

        return self.__get()


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


K = TypeVar("K")


def lazy(getter: Callable[[], K]) -> LazyValue[K]:
    return LazyValue(getter)


def future(getter: Callable[[], K]) -> FutureValue[K]:
    future_value = FutureValue(getter)
    future_value.start()
    return future_value
