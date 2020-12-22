"""Keeps the magic shield (utamo vita) up."""

import time
from equipment_reader import MagicShieldStatus

MAGIC_SHIELD_DURATION_SECS = 180


class EmergencyMagicShieldKeeper:
    def __init__(self, client, total_hp, mana_lo, magic_shield_treshold,
                 emergency_shield_hp_treshold=None,
                 time_fn=None):
        self.client = client
        self.total_hp = total_hp
        self.mana_lo = mana_lo
        self.magic_shield_treshold = magic_shield_treshold
        self.emergency_shield_hp_treshold = emergency_shield_hp_treshold or total_hp * 0.33
        self.last_cast_timestamp = 0
        self.cast_counter = 0
        self.prev_magic_shield_status = MagicShieldStatus.ON_COOLDOWN
        if time_fn is None:
            self.time = time.time
        else:
            self.time = time_fn

    def handle_status_change(self, char_status):
        # WARNING: NOT THREAD SAFE
        magic_shield_status = char_status.magic_shield_status
        if self.prev_magic_shield_status is MagicShieldStatus.OFF_COOLDOWN and\
           magic_shield_status is MagicShieldStatus.RECENTLY_CAST:
            self.last_cast_timestamp = self.timestamp_secs() - 0.5
        self.prev_magic_shield_status = magic_shield_status

        if char_status.magic_shield_status is MagicShieldStatus.OFF_COOLDOWN \
           and self.should_cast(char_status):
            self.cast()
        elif self.should_cast_cancel(char_status):
            self.cast_cancel()

    def should_cast(self, char_status):
        return char_status.hp <= self.emergency_shield_hp_treshold

    def should_cast_cancel(self, char_status):
        is_full_hp = char_status.hp >= self.total_hp
        is_healthy_mana = char_status.mana > self.mana_lo

        # Cancel magic shield when we're in safety
        if char_status.magic_shield_level > 1000 and is_full_hp and \
           is_healthy_mana and self.secs_since_cast() >= 6:
            return True
        # Cancel magic shield if we have better chances tanking with HP
        is_mana_very_low = char_status.mana <= self.total_hp * 1.25
        is_magic_shield_too_high = \
            char_status.magic_shield_level > char_status.mana / 2
        return is_full_hp and is_mana_very_low and is_magic_shield_too_high

    def secs_since_cast(self):
        return self.timestamp_secs() - self.last_cast_timestamp

    def cast(self):
        self.client.cast_magic_shield()

    def cast_cancel(self):
        self.client.cancel_magic_shield()

    def timestamp_secs(self):
        return self.time()
