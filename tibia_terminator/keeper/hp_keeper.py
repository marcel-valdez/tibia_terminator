"""Keeps health points at healthy levels."""

from tibia_terminator.keeper.emergency_reporter import EmergencyReporter


class HpKeeper:
    def __init__(self, client, emergency_reporter: EmergencyReporter, total_hp,
                 heal_at_missing, minor_heal, medium_heal,
                 downtime_heal_at_missing):
        self.client = client
        self.emergency_reporter = emergency_reporter
        self.total_hp = total_hp
        self.heal_at_missing = heal_at_missing
        self.minor_heal_threshold = minor_heal
        self.medium_heal_threshold = medium_heal
        self.downtime_heal_at_missing = downtime_heal_at_missing

    def handle_status_change(self, char_status, is_downtime):
        self.update_max(char_status)
        missing_hp = self.get_missing_hp(char_status.hp)
        if missing_hp >= self.heal_at_missing:
            # Always use strongest heal during emergencies, because by the time
            # the heal goes through, we've already received a several hits.
            if self.emergency_reporter.in_emergency:
                self.client.cast_greater_heal(throttle_ms=250)
            elif missing_hp <= self.minor_heal_threshold:
                self.client.cast_minor_heal(throttle_ms=500)
            elif missing_hp <= self.medium_heal_threshold:
                self.client.cast_medium_heal(throttle_ms=250)
            else:
                self.client.cast_greater_heal(throttle_ms=250)
        elif is_downtime and missing_hp >= self.downtime_heal_at_missing:
            # during downtime heal every 2.5 seconds when we're missing HP
            self.client.cast_minor_heal(throttle_ms=2500)

    def update_max(self, char_status):
        if char_status.hp > self.total_hp:
            self.total_hp = char_status.hp

    def get_missing_hp(self, hp):
        return self.total_hp - hp

    def is_healthy_hp(self, hp):
        missing_hp = self.get_missing_hp(hp)
        return missing_hp < self.heal_at_missing

    def is_critical_hp(self, hp):
        missing_hp = self.get_missing_hp(hp)
        return missing_hp >= self.medium_heal_threshold
