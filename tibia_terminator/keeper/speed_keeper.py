"""Keeps the character hasted."""

from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.common.char_status import CharStatus


class SpeedKeeper:
    def __init__(
            self,
            client: ClientInterface,
            base_speed: int,
            hasted_speed: int
    ):
        self.client = client
        self.base_speed = base_speed
        self.hasted_speed = hasted_speed

    def handle_status_change(self, char_status: CharStatus):
        # when paralized we want to prioritize issuing haste
        if self.is_paralized(char_status.speed):
            throttle_ms = 500
        else:
            throttle_ms = 1000

        if (
                self.is_paralized(char_status.speed) or
                not self.is_hasted(char_status.speed)
        ):
            self.client.cast_haste(throttle_ms)

    def is_hasted(self, speed: int) -> bool:
        return speed >= self.hasted_speed

    def is_paralized(self, speed: int) -> bool:
        return speed < self.base_speed
