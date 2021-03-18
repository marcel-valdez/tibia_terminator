#!/usr/bin/env python3.8

import unittest
import time

from unittest import TestCase
from threading import Event
from common.lazy_evaluator import LazyValue, FutureValueAsync, TaskLoop


def get_value(time_ms: float = 10) -> int:
    time.sleep(time_ms / 1000)
    return time.time() * 1000


class TestLazyEvaluator(TestCase):
    def test_get(self):
        # given
        target = LazyValue(lambda: get_value(10))
        # when
        millis = time.time() * 1000
        actual = target.get()
        # then
        self.assertGreater(actual, millis)

    def test_get_twice(self):
        # given
        target = LazyValue(lambda: get_value(10))
        expected = target.get()
        # when
        actual = target.get()
        # then
        self.assertEqual(actual, expected)

    def test_get_error(self):
        # given
        target = LazyValue(lambda: 1 / 0)
        # when
        self.assertRaises(ZeroDivisionError, target.get)


class TestFutureValueAsync(TestCase):
    def test_get(self):
        # given
        target = FutureValueAsync(lambda: get_value(10))
        millis = time.time() * 1000
        target.start()
        # when
        actual = target.get()
        # then
        self.assertGreater(actual, millis)

    def test_get_twice(self):
        # given
        target = FutureValueAsync(lambda: get_value(10))
        target.start()
        expected = target.get()
        # when
        actual = target.get()
        # then
        self.assertEqual(actual, expected)

    def test_get_error(self):
        # given
        target = FutureValueAsync(lambda: 1 / 0)
        target.start()
        # when
        self.assertRaises(ZeroDivisionError, target.get)


class TestTaskLoop(TestCase):
    def test_add_task(self):
        # given
        ready_event = Event()
        task_time = None

        def task():
            nonlocal task_time
            task_time = time.time()
            ready_event.set()

        target = TaskLoop()
        target.add_task(task)
        main_time = time.time()
        # when
        target.start()
        try:
            # then
            ready_event.wait()
            self.assertGreater(task_time, main_time)
        finally:
            target.stop()

    def test_add_future(self):
        # given
        target = TaskLoop()
        future_time = target.add_future(time.time)
        main_time = time.time()
        # when
        target.start()
        try:
            # then
            self.assertGreater(future_time.get(), main_time)
        finally:
            target.stop()

    def test_add_futures_sequential_exec(self):
        # given
        target = TaskLoop()
        future_time_1 = target.add_future(time.time)
        future_time_2 = target.add_future(time.time)
        future_time_3 = target.add_future(time.time)
        main_time = time.time()
        # when
        target.start()
        try:
            # then
            self.assertGreater(future_time_1.get(), main_time)
            self.assertGreater(future_time_2.get(), future_time_1.get())
            self.assertGreater(future_time_3.get(), future_time_2.get())
        finally:
            target.stop()

    def test_cancel_pending_tasks(self):
        # given
        task_done = Event()
        task_wait = Event()
        task_exec = False

        def task():
            nonlocal task_exec
            task_exec = True
            task_done.set()
            # the test will cancel tasks right before allowing
            # execution.
            task_wait.wait()

        cancelled_task_exec = False

        def cancelled_task():
            # this should not execute, due to cancel_pending_tasks
            nonlocal cancelled_task_exec
            cancelled_task_exec = True

        target = TaskLoop()
        target.add_task(task)
        target.add_task(cancelled_task)
        target.start()
        try:
            task_done.wait()
            # when
            target.cancel_pending_tasks()
            # then
            task_wait.set()
            # this future should execute after without
            # the cancelled task ever executing
            future = target.add_future(lambda: True)
            future.get()
            self.assertTrue(task_exec)
            self.assertFalse(cancelled_task_exec)
        finally:
            target.stop()


if __name__ == '__main__':
    unittest.main()
