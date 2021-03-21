#!/usr/bin/env python3.8

import unittest

from typing import Dict, Any
from unittest import TestCase
from unittest.mock import Mock
from tibia_terminator.keeper.magic_shield_keeper import MagicShieldKeeper
from tibia_terminator.reader.color_spec import (AmuletName, RingName)
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.reader.equipment_reader import MagicShieldStatus

START_TIME = 100
TOTAL_HP = 1000
TOTAL_MANA = 1000
SPEED = 100
MAGIC_SHIELD = 1000
MAGIC_SHIELD_TRESHOLD = 900
EQUIPMENT_STATUS = {
    'emergency_action_amulet': AmuletName.UNKNOWN,
    'equipped_amulet': AmuletName.EMPTY,
    'emergency_action_ring': RingName.UNKNOWN,
    'equipped_ring': RingName.EMPTY,
    'magic_shield_status': MagicShieldStatus.OFF_COOLDOWN
}


class CharStatusStub(CharStatus):
    def __init__(self,
                 hp: int = TOTAL_HP,
                 speed: int = SPEED,
                 mana: int = TOTAL_MANA,
                 magic_shield_level: int = MAGIC_SHIELD,
                 equipment_status: Dict[str, Any] = EQUIPMENT_STATUS):
        super().__init__(hp, speed, mana, magic_shield_level, equipment_status)


class TestMagicShieldKeeper(TestCase):
    def setUp(self):
        self.char_status = CharStatus(TOTAL_MANA, TOTAL_HP, 1000, MAGIC_SHIELD,
                                      EQUIPMENT_STATUS)
        self.mock_client = Mock()
        self.mock_cast_magic_shield = self.mock_client.cast_magic_shield
        self.mock_cancel_magic_shield = self.mock_client.cancel_magic_shield
        self.target = MagicShieldKeeper(self.mock_client, TOTAL_HP,
                                        MAGIC_SHIELD_TRESHOLD, self.time_fn)
        self.time = START_TIME

    def time_fn(self):
        return self.time

    def make_equipment_status(self, **kwargs) -> Dict[str, Any]:
        result = EQUIPMENT_STATUS.copy()
        for key, value in kwargs.items():
            result[key] = value
        return result

    def make_char_status(self, *args, **kwargs):
        return CharStatusStub(*args, **kwargs)

    def test_should_cast_magic_shield(self):
        # given
        char_status = self.make_char_status(
            mana=(TOTAL_HP * 1.5) + 1,
            magic_shield_level=MAGIC_SHIELD_TRESHOLD,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        cases = [
            char_status,
            char_status.copy(mana=(TOTAL_HP * 1.5) + 2),
            char_status.copy(magic_shield_level=MAGIC_SHIELD_TRESHOLD - 1)
        ]
        # when - then
        for _char_status in cases:
            self.check_should_cast_magic_shield(_char_status)

    def check_should_cast_magic_shield(self, char_status: CharStatus):
        # given
        self.mock_cast_magic_shield.reset_mock()
        # when
        self.target.handle_status_change(char_status)
        # then
        self.mock_cast_magic_shield.assert_called_once()

    def test_should_not_cast_magic_shield(self):
        # given
        char_status = self.make_char_status(
            mana=(TOTAL_HP * 1.5) + 1,
            magic_shield_level=MAGIC_SHIELD_TRESHOLD,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        cases = [
            char_status.copy(magic_shield_level=MAGIC_SHIELD_TRESHOLD + 1),
            char_status.copy(mana=TOTAL_HP * 1.5),
            char_status.copy(equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.ON_COOLDOWN))
        ]
        # when - then
        for _char_status in cases:
            self.check_should_not_cast_magic_shield(_char_status)

    def check_should_not_cast_magic_shield(self, char_status: CharStatus):
        # given
        # when
        self.target.handle_status_change(char_status)
        # then
        self.mock_cast_magic_shield.assert_not_called()

    def test_should_cast_cancel_magic_shield(self):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        cast_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=cast_mana / 2,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        cancel_mana = (TOTAL_HP * 1.25)
        cases = [
            cast_char_status.copy(mana=cancel_mana),
            cast_char_status.copy(mana=cancel_mana - 1),
            cast_char_status.copy(mana=cancel_mana,
                                  magic_shield_level=(cancel_mana / 2) + 1)
        ]
        for cancel_char_status in cases:
            self.mock_cancel_magic_shield.reset_mock()
            self.target.handle_status_change(cast_char_status)
            # when
            self.target.handle_status_change(cancel_char_status)
            # then
            self.mock_cancel_magic_shield.assert_called_once()

    def test_should_not_cast_cancel_magic_shield(self):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        cast_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=cast_mana / 2,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        cancel_mana = (TOTAL_HP * 1.25)
        cases = [
            cast_char_status.copy(mana=cancel_mana + 1),
            cast_char_status.copy(mana=cancel_mana + 2),
            cast_char_status.copy(mana=cancel_mana,
                                  magic_shield_level=(cancel_mana / 2)),
            cast_char_status.copy(mana=cancel_mana,
                                  magic_shield_level=(cancel_mana / 2) - 1),
            cast_char_status.copy(mana=cancel_mana,
                                  magic_shield_level=(cancel_mana / 2) - 2)
        ]
        for not_cast_cancel_char_status in cases:
            self.mock_cancel_magic_shield.reset_mock()
            self.target.handle_status_change(cast_char_status)
            # when
            self.target.handle_status_change(not_cast_cancel_char_status)
            # then
            self.mock_cancel_magic_shield.assert_not_called()

    def test_should_recast_magic_shield(self):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        cast_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=cast_mana / 2,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        recast_char_status = cast_char_status.copy(
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        self.target.handle_status_change(cast_char_status)
        # when
        self.target.handle_status_change(recast_char_status)
        # then
        self.assertEqual(self.mock_cast_magic_shield.call_count, 2)

    def test_should_not_recast_magic_shield(self):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        cast_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=cast_mana / 2,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        cases = [
            cast_char_status.copy(equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.ON_COOLDOWN)),
            cast_char_status.copy(equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.RECENTLY_CAST))
        ]
        for not_recast_char_status in cases:
            self.mock_cast_magic_shield.reset_mock()
            self.target.handle_status_change(cast_char_status)
            # when
            self.target.handle_status_change(not_recast_char_status)
            # then
            self.assertEqual(self.mock_cast_magic_shield.call_count, 1)

    def test_should_refresh_magic_shield(self):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        refresh_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=MAGIC_SHIELD_TRESHOLD + 1,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        # when-then
        for time in [179, 180, 181, 170, 171]:
            self.check_refresh_magic_shield(refresh_char_status,
                                            time,
                                            call_count=1)

    def test_should_not_refresh_magic_shield(self):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        refresh_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=MAGIC_SHIELD_TRESHOLD + 1,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        # when-then
        for time in [169, 168, 0, 1]:
            self.check_refresh_magic_shield(refresh_char_status,
                                            time,
                                            call_count=0)

    def check_refresh_magic_shield(self, refresh_char_status: CharStatus,
                                   time: int, call_count: int):
        # given
        cast_mana = (TOTAL_HP * 1.5) + 1
        cast_char_status = self.make_char_status(
            mana=cast_mana,
            magic_shield_level=cast_mana / 2,
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.OFF_COOLDOWN))
        casted_char_status = cast_char_status.copy(
            equipment_status=self.make_equipment_status(
                magic_shield_status=MagicShieldStatus.ON_COOLDOWN))
        self.mock_cast_magic_shield.reset_mock()
        self.target.handle_status_change(cast_char_status)
        self.target.handle_status_change(casted_char_status)
        # when
        self.time += time
        self.target.handle_status_change(refresh_char_status)
        # then
        self.assertEqual(self.mock_cast_magic_shield.call_count,
                         call_count + 1)


if __name__ == '__main__':
    unittest.main()
