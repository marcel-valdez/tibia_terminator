#!/usr/bin/env python3.8

import unittest

from unittest import (TestCase)
from unittest.mock import Mock

from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.keeper.char_keeper import CharKeeper
from tibia_terminator.reader.equipment_reader import MagicShieldStatus
from tibia_terminator.reader.color_spec import (AmuletName, RingName)

TOTAL_HP = 100
TOTAL_MANA = 100
BASE_SPEED = 100
HASTED_SPEED = 110
HEAL_AT_MISSING = 5
DOWNTIME_HEAL_AT_MISING = 2
EXURA_HEAL = 10
EXURA_GRAN_HEAL = 20
EXURA_SIO_HEAL = 40
CRITICAL_MANA = 10
MANA_HI = TOTAL_MANA - 50
MANA_LO = TOTAL_MANA - 25
DOWNTIME_MANA = TOTAL_MANA - 10

FULL_EQ = {
    'equipped_amulet': AmuletName.UNKNOWN.name,
    'equipped_ring': RingName.UNKNOWN.name,
    'emergency_action_amulet': AmuletName.UNKNOWN.name,
    'emergency_action_ring': RingName.UNKNOWN.name,
    'magic_shield_status': MagicShieldStatus.OFF_COOLDOWN
}


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
    def test_should_cast_exura(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura.assert_called_once_with(throttle_ms=500)

    def test_should_cast_exura_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = MANA_LO
        hp = TOTAL_HP - EXURA_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura.assert_called_once_with(throttle_ms=500)

    def test_should_spam_exura_gran(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_GRAN_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura_gran.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_gran_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP - EXURA_GRAN_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura_gran.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_sio(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_SIO_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura_sio.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_sio_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = MANA_HI
        hp = TOTAL_HP - EXURA_SIO_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura_sio.assert_called_once_with(throttle_ms=250)

    def test_should_cast_exura_downtime(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura.assert_called_once_with(throttle_ms=2500)

    def test_should_not_cast_exura_downtime_if_not_hasted(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura.assert_not_called()
        target.client.cast_exura_gran.assert_not_called()
        target.client.cast_exura_sio.assert_not_called()

    def test_should_not_cast_exura_downtime_if_unhealthy_mana(self):
        # given
        speed = HASTED_SPEED
        mana = MANA_LO
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(status(hp, mana, speed))
        # then
        target.client.cast_exura.assert_not_called()
        target.client.cast_exura_gran.assert_not_called()
        target.client.cast_exura_sio.assert_not_called()

    def test_should_drink_mana_at_mana_missing_hi(self):
        # given
        speed = BASE_SPEED
        mana = MANA_HI
        hp = TOTAL_HP - EXURA_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.called_once_with(500)

    def test_should_not_drink_mana_at_mana_missing_lo(self):
        # given
        speed = BASE_SPEED
        mana = MANA_LO
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(status(hp, mana, speed))
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_not_drink_hi_pri_mana_past_mana_lo(self):
        # given
        speed = BASE_SPEED
        hp = TOTAL_HP
        target = self.make_target()
        target.handle_mana_change(status(hp, MANA_HI, speed))
        target.client.drink_mana.assert_called_once_with(1000)
        target.client.reset_mock()
        # when
        target.handle_mana_change(status(hp, MANA_LO + 1, speed + 1))
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
        hp = TOTAL_HP - EXURA_GRAN_HEAL
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
        hp = TOTAL_HP - EXURA_SIO_HEAL
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
        target.client.drink_mana.assert_called_once_with(666)
        target.client.reset_mock()
        # when
        target.handle_mana_change(status(hp, MANA_HI, speed))
        # then
        target.client.drink_mana.assert_called_once_with(1000)

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
        hp = TOTAL_HP - EXURA_GRAN_HEAL
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

    def make_target(self, char_config=None):
        config = char_config or self.make_char_config()
        return CharKeeper(Mock(), [{
            'config': config
        }], {
            'cancel_emergency': 'a',
            'start_emergency': 'b'
        })

    def make_char_config(self,
                         total_hp=TOTAL_HP,
                         total_mana=TOTAL_MANA,
                         base_speed=BASE_SPEED,
                         hasted_speed=HASTED_SPEED,
                         heal_at_missing=HEAL_AT_MISSING,
                         downtime_heal_at_missing=DOWNTIME_HEAL_AT_MISING,
                         exura_heal=EXURA_HEAL,
                         exura_gran_heal=EXURA_GRAN_HEAL,
                         exura_sio_heal=EXURA_SIO_HEAL,
                         critical_mana=CRITICAL_MANA,
                         mana_hi=MANA_HI,
                         mana_lo=MANA_LO,
                         downtime_mana=DOWNTIME_MANA,
                         should_equip_amulet=True,
                         should_equip_ring=True,
                         should_eat_food=True,
                         emergency_shield_hp_treshold=TOTAL_HP * 0.5):
        return {
            'total_hp': total_hp,
            'total_mana': total_mana,
            'base_speed': base_speed,
            'hasted_speed': hasted_speed,
            'heal_at_missing': heal_at_missing,
            'downtime_heal_at_missing': downtime_heal_at_missing,
            'exura_heal': exura_heal,
            'exura_gran_heal': exura_gran_heal,
            'exura_sio_heal': exura_sio_heal,
            'critical_mana': critical_mana,
            'mana_hi': mana_hi,
            'mana_lo': mana_lo,
            'downtime_mana': downtime_mana,
            'should_equip_amulet': should_equip_amulet,
            'should_equip_ring': should_equip_ring,
            'should_eat_food': should_eat_food,
            'emergency_shield_hp_treshold': emergency_shield_hp_treshold
        }


if __name__ == '__main__':
    unittest.main()
