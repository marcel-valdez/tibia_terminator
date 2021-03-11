#!/usr/bin/env python3.8

import asyncio

from queue import Queue
from typing import Callable, Any, TypeVar, Generic, TypeVar
from asyncio import Task
from threading import Thread, Lock, Event

T = TypeVar("T")
class LazyEvaluator(Generic[T], Thread):
    def __init__(self, fn: Callable[[], T],
                 cb: Callable[[T, Exception], None]):
        super().__init__(daemon = False)
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
class LazyValue(Generic[M]):
    def __init__(self, getter: Callable[[], M]):
        self.lazy_evaluator = LazyEvaluator(getter, self.__done_callback)
        self.value_ready_event = Event()
        self.lock = Lock()

    def __done_callback(self, value: M, error: Exception):
        self.value = value
        self.error = error
        self.value_ready_event.set()

    def __start_evaluator(self):
        if (not self.value_ready_event.is_set() and
                not self.lazy_evaluator.is_alive()):
            self.lock.acquire()
            if (not self.value_ready_event.is_set() and
                    not self.lazy_evaluator.is_alive()):
                self.lazy_evaluator.start()
            self.lock.release()

    def __get(self) -> M:
        if self.error is not None:
            raise self.error
        else:
            return self.value

    def get(self, timeout_sec=None) -> M:
        if not self.value_ready_event.is_set():
            self.__start_evaluator()
            if not self.value_ready_event.wait(timeout_sec):
                raise LazyValueNotReadyError()

        return self.__get()
