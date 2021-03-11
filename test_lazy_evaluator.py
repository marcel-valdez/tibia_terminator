#!/usr/bin/env python3.8

import unittest
import time

from unittest import (TestCase)
from lazy_evaluator import LazyValue, FutureValue


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
        target = LazyValue(lambda: 1/0)
        # when
        self.assertRaises(ZeroDivisionError, target.get)


class TestFutureValue(TestCase):
    def test_get(self):
        # given
        target = FutureValue(lambda: get_value(10))
        millis = time.time() * 1000
        target.start()
        # when
        actual = target.get()
        # then
        self.assertGreater(actual, millis)

    def test_get_twice(self):
        # given
        target = FutureValue(lambda: get_value(10))
        target.start()
        expected = target.get()
        # when
        actual = target.get()
        # then
        self.assertEqual(actual, expected)

    def test_get_error(self):
        # given
        target = FutureValue(lambda: 1/0)
        target.start()
        # when
        self.assertRaises(ZeroDivisionError, target.get)


if __name__ == '__main__':
    unittest.main()
