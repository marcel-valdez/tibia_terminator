#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from mock import Mock
from keeper.magic_shield_keeper import MagicShieldKeeper
from common.char_status import CharStatus

START_TIME = 100
TOTAL_HP = 1000
TOTAL_MANA = 1000
MAGIC_SHIELD = 1000
MAGIC_SHIELD_TRESHOLD = 900


class TestMagicShieldKeeper(TestCase):
    def setUp(self):
        self.char_status = CharStatus(TOTAL_MANA, TOTAL_HP, 1000, MAGIC_SHIELD)
        self.mock_client = Mock()
        self.mock_cast_magic_shield = self.mock_client.cast_magic_shield
        self.target = MagicShieldKeeper(self.mock_client, TOTAL_HP,
                                        MAGIC_SHIELD_TRESHOLD, self.time_fn)
        self.time = START_TIME

    def time_fn(self):
        return self.time

    def test_should_cast_magic_shield(self):
        # given
        # when
        self.target.handle_status_change(self.char_status)
        # then
        self.mock_cast_magic_shield.assert_called_once()


if __name__ == '__main__':
    unittest.main()
