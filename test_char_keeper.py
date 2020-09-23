#!/usr/bin/env python2.7

import unittest

from unittest import TestCase
from mock import Mock
from char_keeper import CharKeeper


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
MANA_AT_MISSING_HI = 50
MANA_AT_MISSING_LO = 25
DOWNTIME_MANA_MISSING = 10


class TestCharKeeper(TestCase):

    def test_should_cast_exura(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura.assert_called_once_with(throttle_ms=500)

    def test_should_cast_exura_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA - MANA_AT_MISSING_LO
        hp = TOTAL_HP - EXURA_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura.assert_called_once_with(throttle_ms=500)

    def test_should_spam_exura_gran(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_GRAN_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura_gran.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_gran_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP - EXURA_GRAN_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura_gran.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_sio(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_SIO_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura_sio.assert_called_once_with(throttle_ms=250)

    def test_should_spam_exura_sio_even_if_paralyzed_or_missing_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA - MANA_AT_MISSING_HI
        hp = TOTAL_HP - EXURA_SIO_HEAL
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura_sio.assert_called_once_with(throttle_ms=250)

    def test_should_cast_exura_downtime(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura.assert_called_once_with(throttle_ms=2500)

    def test_should_not_cast_exura_downtime_if_not_hasted(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura.assert_not_called()
        target.client.cast_exura_gran.assert_not_called()
        target.client.cast_exura_sio.assert_not_called()

    def test_should_not_cast_exura_downtime_if_unhealthy_mana(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA - MANA_AT_MISSING_LO
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_hp_change(hp, speed, mana)
        # then
        target.client.cast_exura.assert_not_called()
        target.client.cast_exura_gran.assert_not_called()
        target.client.cast_exura_sio.assert_not_called()

    def test_should_drink_mana_at_mana_missing_hi(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA - MANA_AT_MISSING_HI
        hp = TOTAL_HP - EXURA_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.called_once_with(500)

    def test_should_not_drink_mana_at_mana_missing_lo(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA - MANA_AT_MISSING_LO
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_not_drink_hi_pri_mana_past_mana_at_missing_lo(self):
        # given
        speed = BASE_SPEED
        hp = TOTAL_HP
        target = self.make_target()
        target.handle_mana_change(hp, speed, TOTAL_MANA - MANA_AT_MISSING_HI)
        target.client.drink_mana.assert_called_once_with(1000)
        # when
        target.handle_mana_change(hp, speed,
                                  TOTAL_MANA - MANA_AT_MISSING_LO + 1)
        # then
        target.client.drink_mana.assert_called_once_with(1000)

    def test_should_drink_downtime_mana(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA - DOWNTIME_MANA_MISSING
        hp = TOTAL_HP - DOWNTIME_HEAL_AT_MISING
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.called_with(2500)

    def should_not_drink_mana_when_paralized(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA - MANA_AT_MISSING_HI
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.assert_not_called()

    def should_not_drink_mana_when_critical_hp(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA - MANA_AT_MISSING_HI
        hp = TOTAL_HP - EXURA_GRAN_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_not_drink_downtime_mana_when_not_hasted(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA - DOWNTIME_MANA_MISSING
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_not_drink_downtime_mana_when_not_healthy_hp(self):
        # given
        speed = HASTED_SPEED
        mana = TOTAL_MANA - DOWNTIME_MANA_MISSING
        hp = TOTAL_HP - HEAL_AT_MISSING
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.assert_not_called()

    def test_should_always_drink_mana_when_critical_mana(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP - EXURA_SIO_HEAL
        target = self.make_target()
        # when
        target.handle_mana_change(hp, speed, mana)
        # then
        target.client.drink_mana.assert_called_once_with(666)

    def test_should_haste(self):
        # given
        speed = BASE_SPEED
        mana = TOTAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(hp, speed, mana)
        # then
        target.client.cast_haste.assert_called_once_with(1000)

    def test_should_spam_haste_when_paralized(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(hp, speed, mana)
        # then
        target.client.cast_haste.assert_called_once_with(500)

    def test_should_not_haste_when_critical_hp(self):
        # given
        speed = BASE_SPEED - 10
        mana = TOTAL_MANA
        hp = TOTAL_HP - EXURA_GRAN_HEAL
        target = self.make_target()
        # when
        target.handle_speed_change(hp, speed, mana)
        # then
        target.client.cast_haste.assert_not_called()

    def test_should_not_haste_when_critical_mana_and_not_paralized(self):
        # given
        speed = BASE_SPEED
        mana = CRITICAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(hp, speed, mana)
        # then
        target.client.cast_haste.assert_not_called()

    def test_should_haste_when_critical_mana_and_paralized(self):
        # given
        speed = BASE_SPEED - 10
        mana = CRITICAL_MANA
        hp = TOTAL_HP
        target = self.make_target()
        # when
        target.handle_speed_change(hp, speed, mana)
        # then
        target.client.cast_haste.assert_called_once_with(500)

    def make_target(self):
        return CharKeeper(Mock(), self.make_char_config())

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
                         mana_at_missing_hi=MANA_AT_MISSING_HI,
                         mana_at_missing_lo=MANA_AT_MISSING_LO,
                         downtime_mana_missing=DOWNTIME_MANA_MISSING):
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
            'mana_at_missing_hi': mana_at_missing_hi,
            'mana_at_missing_lo': mana_at_missing_lo,
            'downtime_mana_missing': downtime_mana_missing
        }


if __name__ == '__main__':
    unittest.main()
