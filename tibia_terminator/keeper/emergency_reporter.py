from time import time


class SimpleModeReporter():
    def __init__(self):
        self.mode_enabled = False

    def is_mode_on(self) -> bool:
        return self.mode_enabled

    def start_mode(self) -> None:
        self.mode_enabled = True

    def stop_mode(self) -> None:
        self.mode_enabled = False


class EmergencyReporter(SimpleModeReporter):
    def __init__(self, total_hp, mana_lo, emergency_shield_hp_treshold):
        super().__init__()
        self.total_hp = total_hp
        self.mana_lo = mana_lo
        self.emergency_shield_hp_treshold = emergency_shield_hp_treshold
        self.emergency_start_timestamp_sec = 0
        self.is_emergency_override = False

    # Start: Implement SimpleModeReporter interface

    def is_mode_on(self) -> bool:
        return self.mode_enabled or self.is_emergency_override

    def start_mode(self) -> None:
        if not self.mode_enabled:
            self.emergency_start_timestamp_sec = time()
            self.mode_enabled = True

    def stop_mode(self) -> None:
        """Stops an emergency due to automated behavior. Unless the current
        emergency is due to a user's manual override."""

        if not self.is_emergency_override:
            self.mode_enabled = False
            self.emergency_start_timestamp_sec = 0

    # End: Implement SimpleModeReporter interface

    def is_emergency(self, char_status):
        if char_status.hp > self.total_hp:
            self.total_hp = char_status.hp
        return char_status.hp <= self.emergency_shield_hp_treshold

    def should_stop_emergency(self, char_status):
        """Whether the emergency should be stopped due to the char's status."""
        if self.is_emergency_override:
            # Can only be stopped with a stop_emergency_manual_override
            return False
        if not self.mode_enabled:
            return True

        is_full_hp = char_status.hp >= self.total_hp
        is_healthy_mana = char_status.mana > self.mana_lo
        # Stop when we're in safety
        return is_full_hp and is_healthy_mana and self.secs_since_start() >= 6

    def gen_override_reporter(self) -> SimpleModeReporter:
        return EmergencyOverrideReporter(self)

    def secs_since_start(self):
        return time() - self.emergency_start_timestamp_sec


class EmergencyOverrideReporter(SimpleModeReporter):
    def __init__(self, emergency_reporter: EmergencyReporter):
        super().__init__()
        self.emergency_reporter = emergency_reporter

    def is_mode_on(self) -> bool:
        return self.emergency_reporter.is_mode_on()

    def start_mode(self) -> None:
        """Start an emergency due to a user's override."""
        super().start_mode()
        self.emergency_reporter.is_emergency_override = True
        self.emergency_reporter.emergency_start_timestamp_sec = time()

    def stop_mode(self) -> None:
        """Forcefully stop any type of emergency due to a user's override."""
        super().stop_mode()
        self.emergency_reporter.is_emergency_override = False
        self.emergency_reporter.stop_mode()
