from time import time


class EmergencyReporter():
    def __init__(self, total_hp, mana_lo, emergency_shield_hp_treshold):
        self.total_hp = total_hp
        self.mana_lo = mana_lo
        self.emergency_shield_hp_treshold = emergency_shield_hp_treshold
        self.emergency_start_timestamp_sec = None
        self.in_emergency = False
        self.in_emergency_override = False

    def is_emergency(self, char_status):
        if char_status.hp > self.total_hp:
            self.total_hp = char_status.hp
        return char_status.hp <= self.emergency_shield_hp_treshold

    def start_emergency(self):
        if not self.in_emergency:
            self.emergency_start_timestamp_sec = time()
            self.in_emergency = True

    def should_stop_emergency(self, char_status):
        """Whether the emergency should be stopped due to the char's status."""
        if self.in_emergency_override:
            return False  # Can only be stopped with a stop_emergency_manual_override
        if not self.in_emergency:
            return True

        is_full_hp = char_status.hp >= self.total_hp
        is_healthy_mana = char_status.mana > self.mana_lo
        # Stop when we're in safety
        return is_full_hp and is_healthy_mana and self.secs_since_start() >= 6

    def stop_emergency(self):
        """Stops an emergency due to automated behavior. Unless the current
        emergency is due to a user's manual override."""

        if not self.in_emergency_override:
            self.in_emergency = False
            self.emergency_start_timestamp_sec = None

    def start_emergency_override(self):
        """Start an emergency due to a user's override."""
        self.in_emergency = True
        self.in_emergency_override = True
        self.emergency_start_timestamp_sec = time()

    def stop_emergency_override(self):
        """Forcefully stop any type of emergency due to a user's override."""
        self.in_emergency = False
        self.in_emergency_override = False
        self.emergency_start_timestamp_sec = None

    def secs_since_start(self):
        return time() - self.emergency_start_timestamp_sec
