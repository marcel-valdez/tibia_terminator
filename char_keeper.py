#!/usr/bin/env python2.7


import time


class CharKeeper:
    def __init__(self, client, char_config, print_async=lambda x: None):
        self.client = client
        self.char_config = char_config
        self.print_async = print_async

    def get_missing_hp(self, hp):
        return self.char_config['total_hp'] - hp

    def is_healthy_hp(self, hp):
        missing_hp = self.get_missing_hp(hp)
        return missing_hp < self.char_config['heal_at_missing']

    def is_critical_hp(self, hp):
        missing_hp = self.get_missing_hp(hp)
        return missing_hp >= self.char_config['exura_gran_heal']

    def handle_hp_change(self, hp, speed, mana):
        missing_hp = self.get_missing_hp(hp)
        if missing_hp >= self.char_config['heal_at_missing']:
            if missing_hp <= self.char_config['exura_heal']:
                self.client.cast_exura(throttle_ms=500)
            elif missing_hp <= self.char_config['exura_gran_heal']:
                self.client.cast_exura_gran(throttle_ms=250)
            else:
                self.client.cast_exura_sio(throttle_ms=250)
        else:
            is_downtime = self.is_hasted(speed) and \
                self.is_healthy_mana(mana)
            # during downtime heal every 2.5 seconds when we're missing HP
            if is_downtime and \
               missing_hp >= self.char_config['downtime_heal_at_missing']:
                self.client.cast_exura(throttle_ms=2500)

    def get_missing_mana(self, mana):
        return self.char_config['total_mana'] - mana

    def is_healthy_mana(self, mana):
        missing_mana = self.get_missing_mana(mana)
        return missing_mana < self.char_config['mana_at_missing_lo']

    def is_critical_mana(self, mana):
        return mana <= self.char_config['critical_mana']

    def should_skip_drinking_mana(self, hp, speed, mana):
        # Do not issue order to use mana potion if we're at critical HP levels,
        # unless we're at critical mana levels in order to avoid delaying heals.
        if self.is_critical_hp(hp) and not self.is_critical_mana(mana):
            return True

        # Do not issue order to use mana potion if we are paralyzed unless
        # we're at critical mana levels, in order to avoid delaying haste.
        if self.is_paralized(speed) and not self.is_critical_mana(mana):
            return True

        return False

    def should_drink_mana_high_priority(self, mana):
        missing_mana = self.get_missing_mana(mana)
        # Keep mana within the hi - lo range
        if missing_mana >= self.char_config['mana_at_missing_hi']:
            return True
        elif missing_mana <= self.char_config['mana_at_missing_lo']:
            return False

    # Drink mana until high levels when HP is 100% and already hasted
    # with an interval of 2.5 seconds so it does not affect gameplay
    def should_drink_mana_low_priority(self, hp, speed, mana):
        missing_mana = self.get_missing_mana(mana)
        is_downtime = \
            self.is_healthy_hp(hp) and self.is_hasted(speed)

        if is_downtime and \
           missing_mana >= self.char_config['downtime_mana_missing']:
            return True
        else:
            return False

    def handle_mana_change(self, hp, speed, mana):
        if self.should_skip_drinking_mana(hp, speed, mana):
            return False

        should_drink_mana_hi_pri = self.should_drink_mana_high_priority(mana)
        should_drink_mana_low_pri = self.should_drink_mana_low_priority(
            hp, speed, mana)
        if should_drink_mana_hi_pri:
            throttle_ms = 500
        else:
            throttle_ms = 2500

        if should_drink_mana_hi_pri or should_drink_mana_low_pri:
            self.client.drink_mana(throttle_ms)

    def is_hasted(self, speed):
        return speed >= self.char_config['hasted_speed']

    def is_paralized(self, speed):
        return speed < self.char_config['base_speed']

    def should_skip_haste(self, hp, speed, mana):
        # Do not issue order to haste if we're at critical HP levels.
        if self.is_critical_hp(hp):
            return True

        # Do not issue a haste order if we're not paralyzed and we're at
        # critical mana levels.
        if self.is_critical_mana(mana) and not self.is_paralized(speed):
            return True
        else:
            return False

    def handle_speed_change(self, hp, speed, mana):
        if self.should_skip_haste(hp, speed, mana):
            return False

        # when paralized we want to prioritize issuing haste
        if self.is_paralized(speed):
            throttle_ms = 500
        else:
            throttle_ms = 1000

        if self.is_paralized(speed) or not self.is_hasted(speed):
            self.client.cast_haste(throttle_ms)

    def timestamp_millis(self):
        return int(round(time.time() * 1000))
