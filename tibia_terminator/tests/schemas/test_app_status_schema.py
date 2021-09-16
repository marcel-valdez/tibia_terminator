#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from tibia_terminator.schemas.app_status_schema import (
    AppStatus, AppState, AppStatusSchema
)


class TestAppState(TestCase):
    def test_from_str(self):
        # given
        cases = [
            ("paused", AppState.PAUSED),
            ("running", AppState.RUNNING),
            ("config_selection", AppState.CONFIG_SELECTION),
            ("exit", AppState.EXIT),
        ]
        for input, expected in cases:
            # when
            actual = AppState.from_str(input)
            # then
            self.assertEqual(actual, expected)

    def test___str__(self):
        # given
        cases = [
            ("paused", AppState.PAUSED),
            ("running", AppState.RUNNING),
            ("config_selection", AppState.CONFIG_SELECTION),
            ("exit", AppState.EXIT),
        ]
        for expected, input in cases:
            # when
            actual = str(input)
            # then
            self.assertEqual(actual, expected)


class TestAppStatusSchema(TestCase):
    def test_can_load_input(self):
        # given
        input = {
            'selected_config_name': 'char_name.battle_config_name',
            'state': 'running'
        }
        expected = AppStatus(
            selected_config_name="char_name.battle_config_name",
            state=AppState.RUNNING
        )
        target = AppStatusSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)

    def test_default_values(self):
        # given
        input = {}
        expected = AppStatus(
            selected_config_name="",
            state=AppState.CONFIG_SELECTION
        )
        target = AppStatusSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
