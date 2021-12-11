#!/usr/bin/env python3.8

import unittest

from unittest import TestCase

from tibia_terminator.schemas.char_config_schema import (
    BattleConfigSchema, BattleConfig, CharConfigSchema, CharConfig,
    ItemCrosshairMacroConfig)
from tibia_terminator.schemas.directional_macro_config_schema import (
    DirectionalMacroConfig)


class TestBattleConfigSchema(TestCase):
    def test_load_minimal(self):
        # given
        root = {
            "config_name": "test",
            "hasted_speed": 110,
            "heal_at_missing": 109,
            "downtime_heal_at_missing": 108,
            "mana_hi": 107,
            "mana_lo": 106,
            "critical_mana": 105,
            "downtime_mana": 104,
            "minor_heal": 103,
            "medium_heal": 102,
            "greater_heal": 101,
            "emergency_hp_threshold": 100,
        }
        expected = BattleConfig(**root)
        target = BattleConfigSchema()
        # when
        actual = target.load(root)
        # then
        self.assertEqual(actual, expected)

    def test_load_maximal(self):
        # given
        input = {
            "config_name": "default",
            "hidden": True,
            "hasted_speed": 100,
            "heal_at_missing": 101,
            "downtime_heal_at_missing": 102,
            "mana_hi": 103,
            "mana_lo": 104,
            "critical_mana": 104,
            "downtime_mana": 105,
            "minor_heal": 106,
            "medium_heal": 107,
            "greater_heal": 108,
            "should_equip_amulet": False,
            "should_equip_ring": False,
            "should_eat_food": True,
            "magic_shield_type": "emergency",
            "magic_shield_threshold": 109,
            "emergency_hp_threshold": 110,
            "item_crosshair_macros": [
                {"hotkey": "delete"},
                {"hotkey": "x"},
            ],
            "directional_macros": [{
                "spell_key_rotation": ["8"],
                "rotation_threshold_secs": 4,
                "direction_pairs": [
                    ["ctrl+f", None],
                    ["ctrl+e", None],
                    ["ctrl+s", None],
                    ["ctrl+d", None],
                ]
            }]
        }
        expected = BattleConfig(
            config_name="default",
            hidden=True,
            hasted_speed=100,
            heal_at_missing=101,
            downtime_heal_at_missing=102,
            mana_hi=103,
            mana_lo=104,
            critical_mana=104,
            downtime_mana=105,
            minor_heal=106,
            medium_heal=107,
            greater_heal=108,
            should_equip_amulet=False,
            should_equip_ring=False,
            should_eat_food=True,
            magic_shield_type="emergency",
            magic_shield_threshold=109,
            emergency_hp_threshold=110,
            item_crosshair_macros=[
                ItemCrosshairMacroConfig(hotkey="delete"),
                ItemCrosshairMacroConfig(hotkey="x"),
            ],
            directional_macros=[
                DirectionalMacroConfig(
                    spell_key_rotation=["8"],
                    rotation_threshold_secs=4,
                    direction_pairs=[
                        ("ctrl+f", None),
                        ("ctrl+e", None),
                        ("ctrl+s", None),
                        ("ctrl+d", None),
                    ])
            ])
        target = BattleConfigSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)


class TestCharConfigSchema(TestCase):
    def test_load_resolve(self):
        # given
        input = {
            "char_name": "test_char_name",
            "vocation": "mage",
            "total_hp": 100,
            "total_mana": 101,
            "base_speed": 102,
            "hasted_speed": 103,
            "strong_hasted_speed": 104,
            "battle_configs": [
                {
                    "config_name": "test_base",
                    "hasted_speed": "{strong_hasted_speed}",
                    "heal_at_missing": "{total_hp-10}",
                    "downtime_heal_at_missing": "{total_hp-10}",
                    "mana_hi": "{total_mana-10}",
                    "mana_lo": "{total_mana-10}",
                    "critical_mana": 110,
                    "downtime_mana": "{total_mana-10}",
                    "minor_heal": "{total_hp-10}",
                    "medium_heal": "{total_hp-20}",
                    "greater_heal": "{total_hp-30}",
                    "emergency_hp_threshold": "{total_hp-40}",
                }
            ]
        }
        expected = CharConfig(
            char_name="test_char_name",
            vocation="mage",
            total_hp=100,
            total_mana=101,
            base_speed=102,
            hasted_speed=103,
            strong_hasted_speed=104,
            battle_configs=[
                BattleConfig(
                    config_name="test_base",
                    hasted_speed=104,
                    heal_at_missing=90,
                    downtime_heal_at_missing=90,
                    mana_hi=91,
                    mana_lo=91,
                    critical_mana=110,
                    downtime_mana=91,
                    minor_heal=90,
                    medium_heal=80,
                    greater_heal=70,
                    emergency_hp_threshold=60
                )
            ]
        )
        target = CharConfigSchema()
        # when
        actual = target.load(input)
        # then
        self.assertEqual(actual, expected)

    def test_load_inherit_resolve(self):
        # given
        input = {
            "char_name": "test_char_name",
            "vocation": "mage",
            "total_hp": 100,
            "total_mana": 101,
            "base_speed": 102,
            "hasted_speed": 103,
            "strong_hasted_speed": 104,
            "battle_configs": [
                {
                    "config_name": "test_base",
                    "hasted_speed": "{strong_hasted_speed}",
                    "heal_at_missing": "{total_hp-10}",
                    "downtime_heal_at_missing": "{total_hp-10}",
                    "mana_hi": "{total_mana-10}",
                    "mana_lo": "{total_mana-10}",
                    "critical_mana": 110,
                    "downtime_mana": "{total_mana-10}",
                    "minor_heal": "{total_hp-10}",
                    "medium_heal": "{total_hp-20}",
                    "greater_heal": "{total_hp-30}",
                    "emergency_hp_threshold": "{total_hp-40}",
                },
                {
                    "base": "test_base",
                    "config_name": "test_child",
                    "hasted_speed": "{hasted_speed}",
                    "heal_at_missing": 117,
                }
            ]
        }
        target = CharConfigSchema()
        # when
        actual = target.load(input)
        # then
        test_base = actual.battle_configs[0]
        test_child = actual.battle_configs[1]
        self.assertEqual(test_base.config_name, "test_base")
        self.assertEqual(test_child.config_name, "test_child")
        self.assertNotEqual(test_base.hasted_speed, test_child.hasted_speed)
        self.assertNotEqual(test_base.heal_at_missing,
                            test_child.heal_at_missing)
        self.assertEqual(test_base.downtime_heal_at_missing,
                         test_child.downtime_heal_at_missing)
        self.assertEqual(test_base.mana_hi, test_child.mana_hi)
        self.assertEqual(test_base.mana_lo, test_child.mana_lo)
        self.assertEqual(test_base.critical_mana, test_child.critical_mana)
        self.assertEqual(test_base.downtime_mana, test_child.downtime_mana)
        self.assertEqual(test_base.minor_heal, test_child.minor_heal)
        self.assertEqual(test_base.medium_heal, test_child.medium_heal)
        self.assertEqual(test_base.greater_heal, test_child.greater_heal)
        self.assertEqual(test_base.emergency_hp_threshold,
                         test_child.emergency_hp_threshold)

    def test_load_inherit_inherit_resolve(self):
        # given
        input = {
            "char_name": "test_char_name",
            "vocation": "mage",
            "total_hp": 100,
            "total_mana": 101,
            "base_speed": 102,
            "hasted_speed": 103,
            "strong_hasted_speed": 104,
            "battle_configs": [
                {
                    "config_name": "test_base_base",
                    "hasted_speed": "{strong_hasted_speed}",
                    "heal_at_missing": "{total_hp-10}",
                    "downtime_heal_at_missing": "{total_hp-10}",
                    "mana_hi": "{total_mana-10}",
                    "mana_lo": "{total_mana-10}",
                    "critical_mana": 110,
                    "downtime_mana": "{total_mana-10}",
                    "minor_heal": "{total_hp-10}",
                    "medium_heal": "{total_hp-20}",
                    "greater_heal": "{total_hp-30}",
                    "emergency_hp_threshold": "{total_hp-40}",
                },
                {
                    "base": "test_base_base",
                    "config_name": "test_base",
                    "hasted_speed": "{hasted_speed}",
                    "heal_at_missing": 117,
                },
                {
                    "base": "test_base",
                    "config_name": "test_child",
                    "hasted_speed": 118,
                }
            ]
        }
        target = CharConfigSchema()
        # when
        actual = target.load(input)
        # then
        test_base_base = actual.battle_configs[0]
        test_base = actual.battle_configs[1]
        test_child = actual.battle_configs[2]
        self.assertEqual(test_base_base.config_name, "test_base_base")
        self.assertEqual(test_base.config_name, "test_base")
        self.assertEqual(test_child.config_name, "test_child")
        self.assertEqual(test_child.hasted_speed, 118)
        self.assertEqual(test_child.heal_at_missing, 117)
        self.assertEqual(test_child.greater_heal, 70)


if __name__ == '__main__':
    unittest.main()
