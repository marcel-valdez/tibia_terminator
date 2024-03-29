"""Keeps the magic shield (utamo vita) up."""

import time
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.reader.equipment_reader import MagicShieldStatus

MAGIC_SHIELD_DURATION_SECS = 180
MAGIC_SHIELD_CD_SECS = 14


class MagicShieldKeeper:
    def __init__(self, client, total_hp, magic_shield_threshold, time_fn=None):
        self.client = client
        self.total_hp = total_hp
        self.magic_shield_threshold = magic_shield_threshold
        self.last_cast_ts = 0
        self.last_attempted_cast_ts = None
        self.prev_magic_shield_status = MagicShieldStatus.ON_COOLDOWN
        if time_fn is None:
            self.time = time.time
        else:
            self.time = time_fn

    def handle_status_change(self, char_status: CharStatus):
        # WARNING: NOT THREAD SAFE
        if char_status.hp > self.total_hp:
            self.total_hp = char_status.hp

        if (self.last_attempted_cast_ts is not None and
                self.prev_magic_shield_status is MagicShieldStatus.OFF_COOLDOWN
                and
            (char_status.magic_shield_status is MagicShieldStatus.RECENTLY_CAST
             or char_status.magic_shield_status is
             MagicShieldStatus.ON_COOLDOWN)):
            self.last_cast_ts = self.last_attempted_cast_ts
            self.last_attempted_cast_ts = None

        self.prev_magic_shield_status = char_status.magic_shield_status
        if (self.should_cast(char_status) and char_status.magic_shield_status
                is MagicShieldStatus.OFF_COOLDOWN):
            self.last_attempted_cast_ts = self.timestamp_secs()
            self.cast()
        elif self.should_cast_cancel(char_status):
            self.cast_cancel()

    def is_healthy(self, char_status: CharStatus) -> bool:
        return (
            char_status.magic_shield_level > self.magic_shield_threshold and
            not self.should_cast(char_status)
        )

    def should_cast(self, char_status: CharStatus):
        # Do not cast magic shield if mana is at less than or equal to 150% HP.
        # In that case we have better chances casting healing spells.
        if char_status.mana <= self.total_hp * 1.5:
            return False

        return (char_status.magic_shield_level <= self.magic_shield_threshold
                or self.secs_since_cast() >= MAGIC_SHIELD_DURATION_SECS - 10)

    def should_cast_cancel(self, char_status):
        # cancel magic shield if we have less mana than 125% total HP
        # and there is more than half the current mana points left in the
        # shield.
        return char_status.mana <= self.total_hp * 1.25 and  \
            char_status.magic_shield_level > char_status.mana / 2

    def secs_since_cast(self):
        return self.timestamp_secs() - self.last_cast_ts

    def cast(self):
        self.client.cast_magic_shield()

    def cast_cancel(self):
        self.client.cancel_magic_shield()

    def timestamp_secs(self):
        return self.time()
