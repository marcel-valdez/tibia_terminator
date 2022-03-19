"""Keeps the magic shield (utamo vita) up."""

from typing import Callable
from tibia_terminator.keeper.emergency_reporter import SimpleModeReporter
from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.keeper.magic_shield_keeper import (
    MagicShieldKeeper,
    MAGIC_SHIELD_DURATION_SECS,
)


class EmergencyMagicShieldKeeper(MagicShieldKeeper):

    def __init__(
        self,
        client: ClientInterface,
        emergency_reporter: SimpleModeReporter,
        tank_mode_reporter: SimpleModeReporter,
        total_hp: int,
        magic_shield_threshold: int,
        time_fn: Callable[[], int] = None,
    ):
        super().__init__(client, total_hp, magic_shield_threshold, time_fn)
        self.emergency_reporter = emergency_reporter
        self.tank_mode_reporter = tank_mode_reporter

    def should_cast(self, char_status):
        return (
            self.emergency_reporter.is_mode_on() or self.tank_mode_reporter.is_mode_on()
        ) and (
            char_status.magic_shield_level <= self.magic_shield_threshold
            or self.secs_since_cast() >= MAGIC_SHIELD_DURATION_SECS - 10
        )

    def should_cast_cancel(self, char_status):
        is_full_hp = char_status.hp >= self.total_hp
        # Cancel magic shield when we're in safety
        if (
            not (
                self.emergency_reporter.is_mode_on()
                or self.tank_mode_reporter.is_mode_on()
            )
            and char_status.magic_shield_level > 1000
        ):
            return True
        # Cancel magic shield if we have better chances tanking with HP
        is_mana_very_low = char_status.mana <= self.total_hp * 1.25
        is_magic_shield_too_high = char_status.magic_shield_level > char_status.mana / 2
        return is_full_hp and is_mana_very_low and is_magic_shield_too_high
