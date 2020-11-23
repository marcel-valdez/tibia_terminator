"""Keeps the character hasted."""


class SpeedKeeper:
    def __init__(self, client, base_speed, hasted_speed):
        self.client = client
        self.base_speed = base_speed
        self.hasted_speed = hasted_speed

    def handle_status_change(self, char_status):
        # when paralized we want to prioritize issuing haste
        if self.is_paralized(char_status.speed):
            throttle_ms = 500
        else:
            throttle_ms = 1000

        if self.is_paralized(char_status.speed) or \
           not self.is_hasted(char_status.speed):
            self.client.cast_haste(throttle_ms)

    def is_hasted(self, speed):
        return speed >= self.hasted_speed

    def is_paralized(self, speed):
        return speed < self.base_speed