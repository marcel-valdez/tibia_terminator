"""Keeps the magic shield (utamo vita) up."""

import time

MAGIC_SHIELD_DURATION_SECS = 14


class MagicShieldKeeper:
    def __init__(self, client):
        self.client = client
        self.last_cast_timestamp = 0
        self.cast_counter = 0

    def handle_status_change(self, char_status):
        if self.should_cast():
            self.cast()

    def should_cast(self):
        return self.secs_since_cast() >= (MAGIC_SHIELD_DURATION_SECS - 2)

    def secs_since_cast(self):
        return self.timestamp_secs() - self.last_cast_timestamp

    def cast(self):
        if self.last_cast_timestamp == 0:
            self.last_cast_timestamp = self.timestamp_secs()

        self.cast_counter += 1
        if self.cast_counter == 4:
            self.last_cast_timestamp = self.timestamp_secs()
            self.cast_counter = 0
        else:
            # cast magic shield every 2 seconds 4 times
            self.last_cast_timestamp += 2

        self.client.cast_magic_shield()

    def timestamp_secs(self):
        return time.time()
