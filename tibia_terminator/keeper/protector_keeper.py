"""Keeps the protector spell (utamo tempo) up."""


import time

from typing import Callable

from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.keeper.emergency_reporter import EmergencyReporter, TankModeReporter


PROTECTOR_DURATION_SECS = 12
COOLDOWN = 2
CAST_FREQUENCY_SEC = 6
CAST_ATTEMPTS = 2
# Make two calls with a separation of 250 ms between each
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
        self.last_cast_ts = time.time() - PROTECTOR_DURATION_SECS
        self.last_cast_attempt_ts = self.last_cast_ts
        self.cast_count = 0

    def hangle_status_change(self, _: CharStatus) -> None:
        if self.should_cast():
            self.cast_protector()

    def should_cast(self) -> bool:
        now = self.timestamp_sec_fn()
        return now - self.last_cast_ts >= CAST_FREQUENCY_SEC and \
            self.cast_count < CAST_ATTEMPTS and \
            now - self.last_cast_attempt_ts >= CAST_ATTEMPT_FREQ_SEC

    def cast_protector(self) -> None:
        # NOTE: We assume the player sets utamo tempo and utamo vita on the
        # same key.
        self.client.cast_magic_shield()
        self.cast_count += 1
        self.last_cast_attempt_ts = time.time()
        if self.cast_count >= CAST_ATTEMPTS:
            self.last_cast_ts = self.last_cast_attempt_ts
            self.cast_count = 0


class EmergencyProtectorKeeper(ProtectorKeeper):
    def __init__(
            self,
            client: ClientInterface,
            emergency_reporter: EmergencyReporter,
            tank_mode_reporter: TankModeReporter,
            timestamp_sec_fn: Callable[[], float] = None,
    ):
        super().__init__(client, timestamp_sec_fn)
        self.emergency_reporter = emergency_reporter
        self.tank_mode_reporter = tank_mode_reporter

    def should_cast(self) -> bool:
        return (
            self.emergency_reporter.is_in_emergency() or
            self.tank_mode_reporter.is_tank_mode_on()
        ) and super().should_cast()
