#!/usr/bin/env python2.7


from logger import debug
import time

MAGIC_SHIELD_DURATION_SECS = 210

class CharKeeper:
    def __init__(self, client, char_config):
        self.client = client
        self.char_config = char_config
        self.should_drink_mana_hi_pri = False
        self.should_drink_critical_mana = False
        self.timestamps = {
            'ring': 0,
            'amulet': 0,
            'food': 0,
            'magic_shield': 0
        }
        self.magic_shield_counter = 0
        self.eat_food_counter = 0

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
        return mana > self.char_config['mana_lo']

    def should_skip_drinking_mana(self, hp, speed, mana):
        # Do not issue order to use mana potion if we're at critical HP levels,
        # unless we're at critical mana levels in order to avoid delaying
        # heals.
        if self.is_critical_hp(hp) and not self.is_critical_mana(mana):
            return True

        # Do not issue order to use mana potion if we are paralyzed unless
        # we're at critical mana levels, in order to avoid delaying haste.
        if self.is_paralized(speed) and not self.is_critical_mana(mana):
            return True

        return False

    # Drink mana until high levels when HP is 100% and already hasted
    # with an interval of 2.5 seconds so it does not affect gameplay
    def should_drink_mana_low_priority(self, hp, speed, mana):
        debug(
            '[should_drink_mana_low_priority] mana: ' +
            str(mana), 3)
        is_downtime = \
            self.is_healthy_hp(hp) and self.is_hasted(speed)

        if is_downtime and mana <= self.char_config['downtime_mana']:
            return True
        else:
            return False


    def should_drink_mana_high_priority(self, mana):
        if mana > self.char_config['mana_lo']:
            self.should_drink_mana_hi_pri = False
        elif mana <= self.char_config['mana_hi']:
            self.should_drink_mana_hi_pri = True

        return self.should_drink_mana_hi_pri

    def is_critical_mana(self, mana):
        return mana <= self.char_config['critical_mana']

    def should_drink_mana_critical(self, mana):
        if mana <= self.char_config['critical_mana']:
            self.should_drink_critical_mana = True
        elif mana >= self.char_config['mana_hi']:
            self.should_drink_critical_mana = False

        return self.should_drink_critical_mana

    def handle_mana_change(self, hp, speed, mana):
        if self.should_skip_drinking_mana(hp, speed, mana):
            return False

        should_drink_mana_critical = self.should_drink_mana_critical(mana)
        should_drink_mana_hi_pri = self.should_drink_mana_high_priority(mana)
        should_drink_mana_low_pri = self.should_drink_mana_low_priority(
            hp, speed, mana)

        if should_drink_mana_critical:
            self.client.drink_mana(666)
        elif should_drink_mana_hi_pri:
            self.client.drink_mana(1000)
        elif should_drink_mana_low_pri:
            self.client.drink_mana(2500)

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

    def handle_equipment(self, hp, speed, mana):
        if self.char_config.get('should_cast_magic_shield', False) and \
                self.secs_since_magic_shield() >= (MAGIC_SHIELD_DURATION_SECS - 40):
            self.cast_magic_shield()
        if self.char_config.get('should_equip_amulet', False) and \
                self.secs_since_equip_amulet() >= 5:
            self.equip_amulet()
        if self.char_config.get('should_equip_ring', False) and \
                self.secs_since_equip_ring() >= \
                self.char_config.get('equip_ring_secs', 6):
            self.equip_ring()
        if self.char_config.get('should_eat_food', True) and \
                self.secs_since_eat_food() >= 60:
            self.eat_food()

    def secs_since_equip_ring(self):
        return self.timestamp_secs() - self.timestamps['ring']

    def equip_ring(self):
        self.timestamps['ring'] = self.timestamp_secs()
        self.client.equip_ring()

    def secs_since_equip_amulet(self):
        return self.timestamp_secs() - self.timestamps['amulet']

    def equip_amulet(self):
        self.timestamps['amulet'] = self.timestamp_secs()
        self.client.equip_amulet()

    def secs_since_eat_food(self):
        return self.timestamp_secs() - self.timestamps['food']

    def eat_food(self):
        self.eat_food_counter += 1
        if self.eat_food_counter == 4:
            self.timestamps['food'] = self.timestamp_secs()
            self.eat_food_counter = 0
        else:
            self.timestamps['food'] += 9

        self.client.eat_food()

    def secs_since_magic_shield(self):
        return self.timestamp_secs() - self.timestamps['magic_shield']

    def cast_magic_shield(self):
        self.magic_shield_counter += 1
        if self.magic_shield_counter == 4:
            self.timestamps['magic_shield'] = self.timestamp_secs()
            self.magic_shield_counter = 0
        else:
            # cast magic shield every 8 seconds 4 times
            self.timestamps['magic_shield'] += 8

        self.client.cast_magic_shield()

    def timestamp_secs(self):
        return time.time()
