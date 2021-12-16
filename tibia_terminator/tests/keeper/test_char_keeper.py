#!/usr/bin/env python3.8

import unittest

from unittest import (TestCase)
from unittest.mock import Mock

from tibia_terminator.schemas.char_config_schema import (
    CharConfig, BattleConfig, ItemCrosshairMacroConfig
)
from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.keeper.char_keeper import CharKeeper
from tibia_terminator.reader.equipment_reader import MagicShieldStatus
from tibia_terminator.reader.color_spec import (AmuletName, RingName)

from tibia_terminator.schemas.directional_macro_config_schema import (
    DirectionalMacroConfig
)

TOTAL_HP = 100
TOTAL_MANA = 100
BASE_SPEED = 100
HASTED_SPEED = 110
HEAL_AT_MISSING = 5
DOWNTIME_HEAL_AT_MISING = 2
MINOR_HEAL = 10
MEDIUM_HEAL = 20
GREATER_HEAL = 40
EMERGENCY_HP_THRESHOLD = TOTAL_HP * 0.5
CRITICAL_MANA = 10
MANA_HI = TOTAL_MANA - 25
MANA_LO = TOTAL_MANA - 50
DOWNTIME_MANA = TOTAL_MANA - 10


def status(hp=TOTAL_HP,
           mana=TOTAL_MANA,
           speed=HASTED_SPEED,
           magic_shield_level=0,
           equipped_amulet=AmuletName.UNKNOWN.name,
           equipped_ring=RingName.UNKNOWN.name,
           emergency_action_amulet=AmuletName.UNKNOWN.name,
           emergency_action_ring=RingName.UNKNOWN.name,
           magic_shield_status=MagicShieldStatus.OFF_COOLDOWN):
    return CharStatus(
        hp, speed, mana, magic_shield_level, {
            'equipped_amulet': equipped_amulet,
            'equipped_ring': equipped_ring,
            'emergency_action_amulet': emergency_action_amulet,
            'emergency_action_ring': emergency_action_ring,
            'magic_shield_status': magic_shield_status,
        })


class TestCharKeeper(TestCase):
    def test_should_cast_minor_heal(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - MINOR_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_minor_heal.assert_called_once_with(throttle_ms=500)

    def test_should_cast_minor_heal_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = MANA_LO
        hp = TOTAL_HP - MINOR_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_minor_heal.assert_called_once_with(throttle_ms=500)

    def test_should_spam_medium_heal(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - MEDIUM_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_medium_heal.assert_called_once_with(throttle_ms=250)

    def test_should_spam_medium_heal_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP - MEDIUM_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_medium_heal.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_sio(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - GREATER_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_greater_heal.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_sio_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = MANA_HI
        hp = TOTAL_HP - GREATER_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_greater_heal.assert_called_once_with(throttle_ms=250)

    def test_should_cast_minor_heal_downtime(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_minor_heal.assert_called_once_with(throttle_ms=2500)

    def test_should_not_cast_minor_heal_downtime_if_not_hasted(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_minor_heal.assert_not_called()
        target.client.cast_medium_heal.assert_not_called()
        target.client.cast_greater_heal.assert_not_called()

    def test_should_not_cast_minor_heal_downtime_if_unhealthy_mana(self):
        # given
        speed = HASTED_SPEED
        mana = MANA_LO
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_minor_heal.assert_not_called()
        target.client.cast_medium_heal.assert_not_called()
        target.client.cast_greater_heal.assert_not_called()

    def test_should_drink_mana_at_mana_lo(self):
        # given
        speed = BASE_SPEED
        mana = MANA_LO
        hp = TOTAL_HP - MINOR_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_called_once_with(920)

    def test_should_not_drink_mana_at_mana_missing_lo(self):
        # given
        speed = BASE_SPEED
        mana = MANA_HI
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_called_with(1681)

    def test_should_not_drink_hi_pri_mana_past_mana_hi(self):
        # given
        speed = BASE_SPEED
        hp = TOTAL_HP
        target = self.make_target()
        target.handle_mana_change(status(hp, MANA_LO, speed))
        target.client.drink_mana.assert_called_once_with(920)
        target.client.reset_mock()
        # when
        target.handle_mana_change(status(hp, MANA_HI + 1, speed + 1))
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_drink_downtime_mana(self):
        # given
        speed = HASTED_SPEED
        mana = DOWNTIME_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.called_with(2500)

    def should_not_drink_mana_when_paralized(self):
        # given
        speed = BASE_SPEED - 10
        mana = MANA_HI
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_not_called()

    def should_not_drink_mana_when_critical_hp(self):
        # given
        speed = HASTED_SPEED
        mana = MANA_HI
        hp = TOTAL_HP - MEDIUM_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_not_drink_downtime_mana_when_not_hasted(self):
        # given
        speed = BASE_SPEED
        mana = DOWNTIME_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_not_drink_downtime_mana_when_not_healthy_hp(self):
        # given
        speed = HASTED_SPEED
        mana = DOWNTIME_MANA
        hp = TOTAL_HP - HEAL_AT_MISSING
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_always_drink_mana_when_critical_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP - GREATER_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_called_once_with(666)

    def test_should_drink_mana_critical_until_hi_pri_range(self):
        # given
        speed = BASE_SPEED
        mana = CRITICAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        target.handle_mana_change(status(hp, mana, speed))
        target.client.drink_mana.assert_called_once_with(666)
        target.client.reset_mock()
        target.handle_mana_change(status(hp, MANA_HI - 1, speed))
        target.client.drink_mana.assert_called_once_with(1627)
        target.client.reset_mock()
        # when
        target.handle_mana_change(status(hp, MANA_HI, speed))
        # then
        target.client.drink_mana.assert_called_once_with(1681)

    def test_should_haste(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(status(hp, mana, speed))
        # then
        target.client.cast_haste.assert_called_once_with(1000)

    def test_should_spam_haste_when_paralized(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(status(hp, mana, speed))
        # then
        target.client.cast_haste.assert_called_once_with(500)

    def test_should_not_haste_when_critical_hp(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA
        hp = EMERGENCY_HP_THRESHOLD
        target = self.make_target()
        # when
        target.handle_speed_change(status(hp, mana, speed))
        # then
        target.client.cast_haste.assert_not_called()

    def test_should_not_haste_when_critical_mana_and_not_paralized(self):
        # given
        speed = BASE_SPEED
        mana = CRITICAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(status(hp, mana, speed))
        # then
        target.client.cast_haste.assert_not_called()

    def test_should_haste_when_critical_mana_and_paralized(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(status(hp, mana, speed))
        # then
        target.client.cast_haste.assert_called_once_with(500)

    def test_should_equip_amulet_then_ring_then_eat(self):
        # given
        target = self.make_target()
        # when
        target.handle_equipment(
            status(equipped_ring=RingName.UNKNOWN,
                   equipped_amulet=AmuletName.EMPTY))
        # then
        target.client.equip_amulet.assert_called_once()
        # when
        target.handle_equipment(
            status(equipped_ring=RingName.EMPTY,
                   equipped_amulet=AmuletName.UNKNOWN))
        # then
        target.client.equip_ring.assert_called_once()
        # when
        target.handle_equipment(
            status(equipped_ring=RingName.UNKNOWN,
                   equipped_amulet=AmuletName.UNKNOWN))
        # then
        self.assertEqual(target.client.eat_food.call_count, 3)

    def test_should_not_equip_amulet_if_configured(self):
        # given
        target = self.make_target(
            self.make_char_config(should_equip_amulet=False))
        # when
        target.handle_equipment(
            status(equipped_amulet=AmuletName.EMPTY.name,
                   equipped_ring=RingName.EMPTY))
        # then
        target.client.equip_amulet.assert_not_called()

    def test_should_not_equip_ring_if_configured(self):
        # given
        target = self.make_target(
            self.make_char_config(should_equip_ring=False))
        target.handle_equipment(
            status(equipped_amulet=AmuletName.EMPTY,
                   equipped_ring=RingName.UNKNOWN))
        target.client.equip_amulet.assert_called_once()
        # when
        target.handle_equipment(
            status(equipped_ring=RingName.EMPTY,
                   equipped_amulet=AmuletName.UNKNOWN))
        # then
        target.client.equip_ring.assert_not_called()

    def test_should_not_eat_food_if_configured(self):
        # given
        target = self.make_target(self.make_char_config(should_eat_food=False))
        target.handle_equipment(
            status(equipped_ring=RingName.UNKNOWN,
                   equipped_amulet=AmuletName.EMPTY))
        target.client.equip_amulet.assert_called_once()
        target.handle_equipment(
            status(equipped_ring=RingName.EMPTY,
                   equipped_amulet=AmuletName.EMPTY))
        target.client.equip_ring.assert_called_once()
        # when
        target.handle_equipment(
            status(equipped_ring=RingName.UNKNOWN,
                   equipped_amulet=AmuletName.EMPTY))
        # then
        target.client.eat_food.assert_not_called()

    def make_target(self, char_config: CharConfig = None):
        config = char_config or self.make_char_config()
        return CharKeeper(
            Mock(),
            config,
            config.battle_configs[0],
            HotkeysConfig(**{
                "minor_heal": "F3",
                "medium_heal": "F4",
                "greater_heal": "F5",
                "haste": "6",
                "equip_ring": "F6",
                "equip_amulet": "F7",
                "eat_food": "F8",
                "magic_shield": "F9",
                "cancel_magic_shield": "F10",
                "mana_potion": "F11",
                "toggle_emergency_amulet": "F2",
                "toggle_emergency_ring": "F1",
                "loot": "z",
                "cancel_emergency": "end",
                "start_emergency": "home",
                "up": "w",
                "down": "s",
                "left": "a",
                "right": "d",
                "upper_left": "q",
                "upper_right": "r",
                "lower_left": "z",
                "lower_right": "v"
            })
        )

    def make_char_config(self,
                         total_hp=TOTAL_HP,
                         total_mana=TOTAL_MANA,
                         base_speed=BASE_SPEED,
                         hasted_speed=HASTED_SPEED,
                         heal_at_missing=HEAL_AT_MISSING,
                         downtime_heal_at_missing=DOWNTIME_HEAL_AT_MISING,
                         minor_heal=MINOR_HEAL,
                         medium_heal=MEDIUM_HEAL,
                         greater_heal=GREATER_HEAL,
                         critical_mana=CRITICAL_MANA,
                         mana_hi=MANA_HI,
                         mana_lo=MANA_LO,
                         downtime_mana=DOWNTIME_MANA,
                         should_equip_amulet=True,
                         should_equip_ring=True,
                         should_eat_food=True,
                         emergency_hp_threshold=EMERGENCY_HP_THRESHOLD):
        return CharConfig(**{
            'char_name': 'test_char',
            'vocation': 'mage',
            'strong_hasted_speed': 500,
            'total_hp': total_hp,
            'total_mana': total_mana,
            'base_speed': base_speed,
            'hasted_speed': hasted_speed,
            'battle_configs': [
                BattleConfig(**{
                    'config_name': 'test_battle_config',
                    'hasted_speed': hasted_speed,
                    'heal_at_missing': heal_at_missing,
                    'downtime_heal_at_missing': downtime_heal_at_missing,
                    'minor_heal': minor_heal,
                    'medium_heal': medium_heal,
                    'greater_heal': greater_heal,
                    'critical_mana': critical_mana,
                    'mana_hi': mana_hi,
                    'mana_lo': mana_lo,
                    'downtime_mana': downtime_mana,
                    'should_equip_amulet': should_equip_amulet,
                    'should_equip_ring': should_equip_ring,
                    'should_eat_food': should_eat_food,
                    'emergency_hp_threshold': emergency_hp_threshold,
                    'item_crosshair_macros': [
                        ItemCrosshairMacroConfig(**{'hotkey': 'x'})
                    ],
                    'directional_macros': [
                        DirectionalMacroConfig(**{
                            'spell_key_rotation': ['a'],
                            'rotation_threshold_secs': 3,
                            'direction_pairs': [
                                ('a', 'b')
                            ]
                        })
                    ]
                })],
        })


if __name__ == '__main__':
    unittest.main()
