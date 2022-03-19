"""Keeps the protector spell (utamo tempo) up."""


import time

from typing import Callable, Optional

from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.keeper.emergency_reporter import SimpleModeReporter


PROTECTOR_DURATION_SECS = 12
COOLDOWN = 2
# There should be a balance between CAST_ATTEMPTS and CAST_FREQUENCY_SEC,
# the larger CAST_FREQUENCY_SEC, the more certain we need to be that
# protector was actually cast, therefore we will need a larger CAST_ATTEMPTS
# number.
#
# How often to renew protector. A low number will imply that we'll use
# more mana, too high a number risks protector not being cast when we
# don't have enough mana.
CAST_FREQUENCY_SEC = 9
# TODO: Figure out a way to check whether it was cast or not via
# pixel checking.
# Number of times to try and cast protector before considering it
# 'already cast'.
CAST_ATTEMPTS = 4
# Make CAST_ATTEMPTS calls with a separation of 250 ms between each
CAST_ATTEMPT_FREQ_SEC = 0.25


# There is no easy way to check if utamo tempo is setup or not
# the easiest way is to simply cast it every 5 seconds.
class ProtectorKeeper:
    def __init__(
            self,
            client: ClientInterface,
            timestamp_sec_fn: Callable[[], float] = None
    ):
        self.client = client
        self.timestamp_sec_fn = timestamp_sec_fn or time.time
        self.last_cast_ts = self.timestamp_sec_fn() - PROTECTOR_DURATION_SECS
        self.last_cast_attempt_ts = self.last_cast_ts
        self.cast_count = 0

    def handle_status_change(self, _: Optional[CharStatus] = None) -> None:
        if self.should_cast(_):
            self.cast_protector()

    def is_healthy(self, _: CharStatus) -> bool:
        return not self.should_cast(_)

    def should_cast(self, _: Optional[CharStatus] = None) -> bool:
        now = self.timestamp_sec_fn()
        return (now - self.last_cast_ts >= CAST_FREQUENCY_SEC and
                self.cast_count < CAST_ATTEMPTS and
                now - self.last_cast_attempt_ts >= CAST_ATTEMPT_FREQ_SEC)

    def cast_protector(self) -> None:
        # NOTE: We assume the player sets utamo tempo and utamo vita on the
        # same key.
        self.client.cast_magic_shield()
        self.cast_count += 1
        self.last_cast_attempt_ts = self.timestamp_sec_fn()
        if self.cast_count >= CAST_ATTEMPTS:
            self.last_cast_ts = self.last_cast_attempt_ts
            self.cast_count = 0


class EmergencyProtectorKeeper(ProtectorKeeper):
    def __init__(
            self,
            client: ClientInterface,
            emergency_reporter: SimpleModeReporter,
            tank_mode_reporter: SimpleModeReporter,
            timestamp_sec_fn: Callable[[], float] = None,
    ):
        super().__init__(client, timestamp_sec_fn)
        self.emergency_reporter = emergency_reporter
        self.tank_mode_reporter = tank_mode_reporter

    def should_cast(self, _: Optional[CharStatus] = None) -> bool:
        return (
            self.emergency_reporter.is_mode_on() or
            self.tank_mode_reporter.is_mode_on()
        ) and super().should_cast()
