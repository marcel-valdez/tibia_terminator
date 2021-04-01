#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from typing import Iterable

from tibia_terminator.schemas.item_crosshair_macro_config_schema import (
    ItemCrosshairMacroConfigSchema, ItemCrosshairMacroConfig, MacroAction,
    Direction)


class TestDirection(TestCase):
    def test_from_str(self):
        # given
        cases = [
            ("left", Direction.LEFT),
            ("right", Direction.RIGHT),
            ("up", Direction.UP),
            ("down", Direction.DOWN),
            ("lower_left", Direction.LOWER_LEFT),
            ("upper_left", Direction.UPPER_LEFT),
            ("lower_right", Direction.LOWER_RIGHT),
            ("upper_right", Direction.UPPER_RIGHT),
        ]
        for input, expected in cases:
            # when
            actual = Direction.from_str(input)
            # then
            self.assertEqual(actual, expected)

    def test___str__(self):
        # given
        cases = [
            ("left", Direction.LEFT),
            ("right", Direction.RIGHT),
            ("up", Direction.UP),
            ("down", Direction.DOWN),
            ("lower_left", Direction.LOWER_LEFT),
            ("upper_left", Direction.UPPER_LEFT),
            ("lower_right", Direction.LOWER_RIGHT),
            ("upper_right", Direction.UPPER_RIGHT),
        ]
        for expected, input in cases:
            # when
            actual = str(input)
            # then
            self.assertEqual(actual, expected)


class TestMacroAction(TestCase):
    def test_from_str(self):
        # given
        cases = [("click_behind", MacroAction.CLICK_BEHIND),
                 ("click", MacroAction.CLICK)]
        for input, expected in cases:
            # when
            actual = MacroAction.from_str(input)
            # then
            self.assertEqual(actual, expected)

    def test___str__(self):
        # given
        cases = [("click_behind", MacroAction.CLICK_BEHIND),
                 ("click", MacroAction.CLICK)]
        for expected, input in cases:
            # when
            actual = str(input)
            # then
            self.assertEqual(actual, expected)


class TestItemCrosshairMacroConfigSchema(TestCase):
    def test_click_behind(self):
        # given
        input = {'hotkey': 'x', 'action': 'click_behind'}
        expected = ItemCrosshairMacroConfig(hotkey='x',
                                            action=MacroAction.CLICK_BEHIND)
        target = ItemCrosshairMacroConfigSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)

    def test_click(self):
        # given
        input = {'hotkey': 'p', 'action': 'click'}
        expected = ItemCrosshairMacroConfig(hotkey='p',
                                            action=MacroAction.CLICK)
        target = ItemCrosshairMacroConfigSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)

    def test_click_default(self):
        # given
        input = {
            'hotkey': 'g',
        }
        expected = ItemCrosshairMacroConfig(hotkey='g',
                                            action=MacroAction.CLICK)
        target = ItemCrosshairMacroConfigSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)

    def test_click_behind_direction_map(self):
        # given
        input = {
            'hotkey': 'g',
            'action': 'click_behind',
            'direction_map': {
                's': 'left',
                'f': 'right',
                'e': 'up',
                'd': 'down',
            }
        }
        expected = ItemCrosshairMacroConfig(hotkey='g',
                                            action=MacroAction.CLICK_BEHIND,
                                            direction_map={
                                                's': Direction.LEFT,
                                                'f': Direction.RIGHT,
                                                'e': Direction.UP,
                                                'd': Direction.DOWN
                                            })
        target = ItemCrosshairMacroConfigSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
