#!/usr/bin/env python3.8

import unittest

from typing import Callable, Union

from unittest import TestCase
from unittest.mock import Mock
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.schemas.char_config_schema import BattleConfig
from tibia_terminator.keeper.knight_potion_keeper import (
    RefillPriority,
    RefillPriorities,
    StatConfig,
    KnightPrioritiesStrategy,
    KnightPotionKeeper,
)

STAT_LO = 30
STAT_HI = 80
STAT_DOWNTIME = 110
STAT_CRIT = 10

TOTAL_HP = 120
TOTAL_MANA = 100
BASE_SPEED = 100
HASTED_SPEED = 110
HEAL_AT_MISSING = 5
POTION_HP_HI = STAT_HI
POTION_HP_LO = STAT_LO
POTION_HP_CRITICAL = STAT_CRIT
DOWNTIME_HEAL_AT_MISSING = TOTAL_HP - STAT_DOWNTIME
MINOR_HEAL = 10
MEDIUM_HEAL = 20
GREATER_HEAL = 40
CRITICAL_MANA = 10
MANA_HI = TOTAL_MANA - 25
MANA_LO = TOTAL_MANA - 50
DOWNTIME_MANA = TOTAL_MANA - 10


class TestKnightPrioritiesStrategy(TestCase):
    def test_get_priority_critical_continues(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.CRITICAL,
            stat_value=2,
            # then
            expected=RefillPriority.CRITICAL,
        )

    def test_get_priority_critical_starts(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.HIGH_PRIORITY,
            stat_value=0,
            # then
            expected=RefillPriority.CRITICAL,
        )

    def test_get_priority_critical_ends_hipri_starts(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.CRITICAL,
            stat_value=3,
            # then
            expected=RefillPriority.HIGH_PRIORITY,
        )

    def test_get_priority_hipri_continues(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.HIGH_PRIORITY,
            stat_value=4,
            # then
            expected=RefillPriority.HIGH_PRIORITY,
        )

    def test_get_priority_hipri_continues_lo(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.HIGH_PRIORITY,
            stat_value=2,
            # then
            expected=RefillPriority.HIGH_PRIORITY,
        )

    def test_get_priority_hipri_ends_downtime_starts(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.HIGH_PRIORITY,
            stat_value=5,
            # then
            expected=RefillPriority.DOWNTIME,
        )

    def test_get_priority_downtime_continues(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.DOWNTIME,
            stat_value=6,
            # then
            expected=RefillPriority.DOWNTIME,
        )

    def test_get_priority_downtime_ends(self) -> None:
        self.check_get_priority(
            # given
            stat_config=StatConfig(critical=1, lo=3, hi=5, downtime=7),
            last_priority=RefillPriority.DOWNTIME,
            stat_value=7,
            # then
            expected=RefillPriority.NO_REFILL,
        )

    def check_get_priority(
        self,
        stat_config: StatConfig,
        last_priority: RefillPriority,
        stat_value: int,
        expected: RefillPriority,
    ) -> None:
        # when
        actual = KnightPrioritiesStrategy.get_priority(stat_config,
                                                       last_priority,
                                                       stat_value)
        # then
        self.assertEqual(actual, expected)


class TestKnightPotionKeeper(TestCase):
    def test_refill_probabilities_map_hp_critical(self) -> None:
        # given
        keeper = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        target = keeper.gen_refill_probability_map()
        # then
        for mana_priority in RefillPriority:
            self.assertEqual(
                target[RefillPriorities(hp_priority=RefillPriority.CRITICAL,
                                        mana_priority=mana_priority)],
                1.0,
            )

    def test_refill_probabilities_map_hp_hipri(self) -> None:
        # given
        keeper = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        target = keeper.gen_refill_probability_map()
        # then
        self.assertEqual(
            target[RefillPriorities(
                hp_priority=RefillPriority.HIGH_PRIORITY,
                mana_priority=RefillPriority.HIGH_PRIORITY,
            )],
            0.6,
        )
        self.assertEqual(
            target[RefillPriorities(
                hp_priority=RefillPriority.HIGH_PRIORITY,
                mana_priority=RefillPriority.CRITICAL,
            )],
            0.33,
        )

    def test_refill_probabilities_map_hp_no_refill(self) -> None:
        # given
        keeper = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        target = keeper.gen_refill_probability_map()
        # then
        for mana_priority in RefillPriority:
            if mana_priority is not RefillPriority.NO_REFILL:
                self.assertEqual(
                    target[RefillPriorities(
                        hp_priority=RefillPriority.NO_REFILL,
                        mana_priority=mana_priority,
                    )],
                    0.0,
                )

    def test_refill_probabilities_map_mana_no_refill(self) -> None:
        # given
        keeper = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        target = keeper.gen_refill_probability_map()
        # then
        for hp_priority in RefillPriority:
            if hp_priority is not RefillPriority.NO_REFILL:
                self.assertEqual(
                    target[RefillPriorities(
                        hp_priority=hp_priority,
                        mana_priority=RefillPriority.NO_REFILL,
                    )],
                    1.0,
                )

    def test_refill_probabilities_map_hp_downtime(self) -> None:
        # given
        keeper = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        target = keeper.gen_refill_probability_map()
        # then
        for mana_priority in RefillPriority:
            if mana_priority > RefillPriority.DOWNTIME:
                self.assertEqual(
                    target[RefillPriorities(
                        hp_priority=RefillPriority.DOWNTIME,
                        mana_priority=mana_priority,
                    )],
                    0.0,
                )
        self.assertEqual(
            target[RefillPriorities(
                hp_priority=RefillPriority.DOWNTIME,
                mana_priority=RefillPriority.DOWNTIME,
            )],
            0.25,
        )
        self.assertEqual(
            target[RefillPriorities(
                hp_priority=RefillPriority.DOWNTIME,
                mana_priority=RefillPriority.NO_REFILL,
            )],
            1.0,
        )

    def test_refill_probabilities_map_mana_downtime(self) -> None:
        # given
        keeper = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        target = keeper.gen_refill_probability_map()
        # then
        for hp_priority in RefillPriority:
            if hp_priority > RefillPriority.DOWNTIME:
                self.assertEqual(
                    target[RefillPriorities(
                        hp_priority=hp_priority,
                        mana_priority=RefillPriority.DOWNTIME,
                    )],
                    1.0,
                )

    def test_get_threshold_ms_lo(self) -> None:
        #   lo-v        v-hi
        # ▯▯▯▯▯▮▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯
        #  ^-crit             ^-downtime
        self.check_get_threshold_ms(stat_value=STAT_LO, expected=814)

    def test_get_threshold_ms_half_crit_to_lo(self) -> None:
        #   lo-v        v-hi
        # ▯▯▯▮▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯
        #  ^-crit             ^-downtime
        half_lo_to_hi = (STAT_HI + STAT_LO) / 2
        quarter_crit_to_half = STAT_CRIT + (half_lo_to_hi - STAT_CRIT) / 2
        quarter_crit_to_hi_pri_ms = int(666 + (1000 - 666) / 2)
        self.check_get_threshold_ms(stat_value=quarter_crit_to_half,
                                    expected=quarter_crit_to_hi_pri_ms)

    def test_get_threshold_ms_three_quarters_crit_to_mid(self) -> None:
        #   lo-v        v-hi
        # ▯▯▯▯▯▯▯▯▯▮▯▯▯▯▯▯▯▯▯▯▯▯▯
        #  ^-crit             ^-downtime
        half_lo_to_hi = (STAT_HI + STAT_LO) / 2
        three_quarters_crit_to_mid = STAT_CRIT + (half_lo_to_hi -
                                                  STAT_CRIT) * 0.75
        three_quarters_crit_to_mid_ms = int(666 + ((1000 - 666) * 0.75))
        self.check_get_threshold_ms(stat_value=three_quarters_crit_to_mid,
                                    expected=three_quarters_crit_to_mid_ms)

    def test_get_threshold_ms_half_hi_pri(self) -> None:
        #   lo_v        v_hi
        # ▯▯▯▯▯▯▯▯▯▯▮▯▯▯▯▯▯▯▯▯▯▯▯
        #  ^-crit             ^-downtime
        self.check_get_threshold_ms(stat_value=(STAT_LO + STAT_HI) / 2,
                                    expected=1000)

    def test_get_threshold_ms_hi(self) -> None:
        #   lo_v        v_hi
        # ▯▯▯▯▯▯▯▯▯▯▯▯▯▯▮▯▯▯▯▯▯▯▯
        #  ^-crit             ^-downtime
        self.check_get_threshold_ms(stat_value=STAT_HI, expected=1681)

    def test_get_threshold_ms_half_hi(self) -> None:
        #   lo_v        v_hi
        # ▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▮▯▯▯▯▯
        #  ^-crit             ^-downtime
        self.check_get_threshold_ms(stat_value=(STAT_HI + STAT_DOWNTIME) / 2,
                                    expected=2090)

    def test_get_threshold_ms_critical(self) -> None:
        #   lo_v        v_hi
        # ▮▮▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯
        #  ^-crit             ^-downtime
        for stat_value in [STAT_CRIT, STAT_CRIT - 1, 0, 1, 2, STAT_CRIT - 2]:
            self.check_get_threshold_ms(stat_value=stat_value, expected=666)

    def check_get_threshold_ms(self,
                               stat_value: Union[int, float],
                               expected: int,
                               critical: int = STAT_CRIT,
                               lo: int = STAT_LO,
                               hi: int = STAT_HI,
                               downtime: int = STAT_DOWNTIME) -> None:
        # given
        target = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=Mock(),
                                    battle_config=make_battle_config())
        # when
        actual = target.get_threshold_ms(stat_value=stat_value,
                                         stat_config=StatConfig(
                                             critical=critical,
                                             lo=lo,
                                             hi=hi,
                                             downtime=downtime))
        # then
        self.assertEqual(actual, expected)

    def test_handle_status_change_no_refill(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=TOTAL_HP,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            is_downtime=False,
            # then
            assert_fn=lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_downtime_but_not_is_downtime(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=TOTAL_HP - HEAL_AT_MISSING - 1,
                mana=DOWNTIME_MANA - 1,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            is_downtime=False,
            # then
            assert_fn=lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_hp_full_mana_downtime_but_not_is_downtime(
            self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=TOTAL_HP - DOWNTIME_HEAL_AT_MISSING + 1,
                mana=DOWNTIME_MANA - 1,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            is_downtime=False,
            # then
            assert_fn=lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_hp_downtime(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=TOTAL_HP - HEAL_AT_MISSING - 1,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_minor_heal.assert_called_with(2475),
        )

    def test_handle_status_change_mana_downtime(self) -> None:
        self.check_handle_status_change(
            # given
            CharStatus(
                hp=TOTAL_HP,
                mana=DOWNTIME_MANA - 1,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(2445),
        )

    def test_handle_status_change_hp_critical(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_CRITICAL - 1,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_greater_heal.assert_called_with(666),
        )

    def test_handle_status_change_hp_critical_no_greater_heal(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_CRITICAL - 1,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={"has_greater_heal_potions": False},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_medium_heal.assert_called_with(666),
        )

    def test_handle_status_change_hp_critical_only_minor_heal(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_CRITICAL - 1,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_minor_heal.assert_called_with(666),
        )

    def test_handle_status_change_hp_critical_no_heal_potions(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_CRITICAL - 1,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                    "has_minor_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_hp_critical_mana_lo_no_heal_potions(
            self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_CRITICAL - 1,
                mana=MANA_LO,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                    "has_minor_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(920),
        )

    def test_handle_status_change_hp_potion_crit_to_lo(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_LO - 1,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_medium_heal.assert_called_with(807),
        )

    def test_handle_status_change_hp_potion_lo(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_LO,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_medium_heal.assert_called_with(814),
        )

    def test_handle_status_change_critical_mana_then_hi_pri_hp(self) -> None:
        # given
        char_status_crit_mana = CharStatus(
            hp=TOTAL_HP,
            mana=0,
            magic_shield_level=0,
            equipment_status={},
            speed=HASTED_SPEED,
        )
        char_status_hi_pri_hp = CharStatus(
            hp=POTION_HP_LO + 1,
            mana=TOTAL_MANA,
            magic_shield_level=0,
            equipment_status={
                "has_greater_heal_potions": True,
                "has_medium_heal_potions": True,
            },
            speed=HASTED_SPEED,
        )
        mock_client = Mock()
        target = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=mock_client,
                                    battle_config=make_battle_config())
        target.handle_status_change(char_status=char_status_crit_mana,
                                    is_downtime=True)
        # when
        target.handle_status_change(char_status=char_status_hi_pri_hp,
                                    is_downtime=True)
        # then
        mock_client.drink_medium_heal.assert_called_with(666)

    def test_handle_status_change_hp_potion_lo_no_medium_heal(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_LO,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={"has_medium_heal_potions": False},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_greater_heal.assert_called_with(814),
        )

    def test_handle_status_change_hp_potion_lo_only_minor_heal(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_LO,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_minor_heal.assert_called_with(814),
        )

    def test_handle_status_change_hp_potion_lo_no_heal_potions(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_LO,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                    "has_minor_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_hp_potion_lo_mana_lo_no_heal_potions(
            self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_LO,
                mana=MANA_LO,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                    "has_minor_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(920),
        )

    def test_handle_status_change_hp_potion_hi(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_HI,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_minor_heal.assert_called_with(1625),
        )

    def test_handle_status_change_hp_potion_hi_no_minor_heal(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_HI,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={"has_minor_heal_potions": False},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_hp_potion_hi_only_minor_heal(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_HI,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_minor_heal.assert_called_with(1625),
        )

    def test_handle_status_change_hp_potion_hi_no_heal_potions(self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_HI,
                mana=TOTAL_MANA,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                    "has_minor_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: self.assertEqual(len(m.method_calls), 0),
        )

    def test_handle_status_change_hp_potion_hi_mana_lo_no_heal_potions(
            self) -> None:
        # given
        self.check_handle_status_change(
            CharStatus(
                hp=POTION_HP_HI,
                mana=MANA_LO,
                magic_shield_level=0,
                equipment_status={
                    "has_greater_heal_potions": False,
                    "has_medium_heal_potions": False,
                    "has_minor_heal_potions": False,
                },
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(920),
        )

    def test_handle_status_change_mana_critical(self) -> None:
        self.check_handle_status_change(
            # given
            CharStatus(
                hp=TOTAL_HP,
                mana=CRITICAL_MANA - 1,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(666),
        )

    def test_handle_status_change_mana_crit_to_lo(self) -> None:
        self.check_handle_status_change(
            # given
            CharStatus(
                hp=TOTAL_HP,
                mana=MANA_LO - 1,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(914),
        )

    def test_handle_status_change_mana_lo(self) -> None:
        self.check_handle_status_change(
            # given
            CharStatus(
                hp=TOTAL_HP,
                mana=MANA_LO,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(920),
        )

    def test_handle_status_change_mana_hi(self) -> None:
        self.check_handle_status_change(
            # given
            CharStatus(
                hp=TOTAL_HP,
                mana=MANA_HI,
                magic_shield_level=0,
                equipment_status={},
                speed=HASTED_SPEED,
            ),
            # then
            lambda m: m.drink_mana.assert_called_with(1681),
        )

    def check_handle_status_change(
        self,
        char_status: CharStatus,
        assert_fn: Callable[[Mock], None],
        is_downtime: bool = True,
    ) -> None:
        # given
        mock_client = Mock()
        target = KnightPotionKeeper(total_hp=TOTAL_HP,
                                    client=mock_client,
                                    battle_config=make_battle_config())
        # when
        target.handle_status_change(char_status=char_status,
                                    is_downtime=is_downtime)
        # then
        assert_fn(mock_client)


def make_battle_config(
    heal_at_missing=HEAL_AT_MISSING,
    potion_hp_hi=POTION_HP_HI,
    potion_hp_lo=POTION_HP_LO,
    potion_hp_critical=POTION_HP_CRITICAL,
    downtime_mana=DOWNTIME_MANA,
    mana_hi=MANA_HI,
    mana_lo=MANA_LO,
    critical_mana=CRITICAL_MANA,
):
    return BattleConfig(
        **{
            "config_name": "test_battle_config",
            "hasted_speed": HASTED_SPEED,
            "heal_at_missing": heal_at_missing,
            "downtime_heal_at_missing": DOWNTIME_HEAL_AT_MISSING,
            "minor_heal": MINOR_HEAL,
            "medium_heal": MEDIUM_HEAL,
            "greater_heal": GREATER_HEAL,
            "potion_hp_hi": potion_hp_hi,
            "potion_hp_lo": potion_hp_lo,
            "potion_hp_critical": potion_hp_critical,
            "critical_mana": critical_mana,
            "mana_hi": mana_hi,
            "mana_lo": mana_lo,
            "downtime_mana": downtime_mana,
            "should_equip_amulet": True,
            "should_equip_ring": True,
            "should_eat_food": True,
            "emergency_hp_threshold": TOTAL_HP * 0.5,
        })


if __name__ == "__main__":
    unittest.main()
