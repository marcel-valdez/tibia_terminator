#!/usr/bin/env python3.8

import unittest

from unittest import (TestCase)
from lazy_evaluator import LazyValue


import time


class TestLazyEvaluator(TestCase):
    def test_get_value(self):
        # given
        target = LazyValue(lambda: self.get_value(10))
        # when
        millis = time.time() * 1000
        actual = target.get()
        # then
        self.assertGreater(actual, millis)

    def test_get_value_twice(self):
        # given
        target = LazyValue(lambda: self.get_value(10))
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

    def get_value(self, time_ms=10) -> int:
        time.sleep(time_ms / 1000)
        return time.time() * 1000


if __name__ == '__main__':
    unittest.main()
