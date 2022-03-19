"""Keeps health points at healthy levels."""

from typing import Dict

from tibia_terminator.keeper.common import ThresholdCalculator, RefillPriority, StatConfig
from tibia_terminator.keeper.emergency_reporter import SimpleModeReporter
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.interface.client_interface import ClientInterface


class HpKeeper:
    THRESHOLD_PRIORITY_MAP = {
        RefillPriority.CRITICAL: 250,
        RefillPriority.HIGH_PRIORITY: 500,
        RefillPriority.DOWNTIME: 750,
        RefillPriority.NO_REFILL: 2500,
    }

    def __init__(
        self,
        client: ClientInterface,
        emergency_reporter: SimpleModeReporter,
        total_hp: int,
        heal_at_missing: int,
        minor_heal: int,
        medium_heal: int,
        greater_heal: int,
        downtime_heal_at_missing: int,
        emergency_hp_threshold: int,
    ):
        self.threshold_calculator = ThresholdCalculator(
            stat_config=StatConfig(downtime=total_hp - heal_at_missing,
                                   hi=total_hp - medium_heal,
                                   lo=total_hp - greater_heal,
                                   critical=emergency_hp_threshold),
            priority_threshold_map=type(self).THRESHOLD_PRIORITY_MAP)
        self.threshold_calculator.stat_config.validate()
        self.client = client
        self.emergency_reporter = emergency_reporter
        self.total_hp = total_hp
        self.heal_at_missing = heal_at_missing
        self.minor_heal_threshold = minor_heal
        self.medium_heal_threshold = medium_heal
        self.greater_heal_threshold = greater_heal
        self.emergency_hp_threshold = emergency_hp_threshold
        self.downtime_heal_at_missing = downtime_heal_at_missing

    def handle_status_change(self, char_status: CharStatus, is_downtime: bool):
        self.update_max(char_status)
        missing_hp = self.get_missing_hp(char_status.hp)
        throttle_ms = self.threshold_calculator.gen_threshold_ms(char_status.hp)
        if missing_hp >= self.heal_at_missing:
            # Always use strongest heal during emergencies, because by the time
            # the heal goes through, we've already received a several hits.
            if self.emergency_reporter.is_mode_on():
                critical_threshold_ms = HpKeeper.THRESHOLD_PRIORITY_MAP[
                    RefillPriority.CRITICAL]
                self.client.cast_greater_heal(
                    throttle_ms=critical_threshold_ms)
            else:
                throttle_ms = self.threshold_calculator.gen_threshold_ms(
                    char_status.hp)
                if missing_hp <= self.minor_heal_threshold:
                    self.client.cast_minor_heal(throttle_ms=throttle_ms)
                elif missing_hp <= self.medium_heal_threshold:
                    self.client.cast_medium_heal(throttle_ms=throttle_ms)
                else:
                    self.client.cast_greater_heal(throttle_ms=throttle_ms)
        elif is_downtime and missing_hp >= self.downtime_heal_at_missing:
            # during downtime heal every 2.5 seconds when we're missing HP
            self.client.cast_minor_heal(throttle_ms=throttle_ms)

    def update_max(self, char_status):
        if char_status.hp > self.total_hp:
            self.total_hp = char_status.hp

    def get_missing_hp(self, current_hp: int) -> int:
        return self.total_hp - current_hp

    def is_healthy(self, char_status: CharStatus) -> bool:
        return self.get_missing_hp(char_status.hp) < self.heal_at_missing

    def is_critical_hp(self, current_hp: int) -> bool:
        return current_hp <= self.emergency_hp_threshold
