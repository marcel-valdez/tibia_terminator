"""Keeps mana at healthy levels."""

from tibia_terminator.keeper.common import StatConfig, RefillPriority, ThresholdCalculator
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.interface.client_interface import ClientInterface


class ManaKeeper:
    THRESHOLD_PRIORITY_MAP = {
        RefillPriority.CRITICAL: 666,
        RefillPriority.HIGH_PRIORITY: 1000,
        RefillPriority.DOWNTIME: 2500,
        RefillPriority.NO_REFILL: 60000 * 5,
    }

    def __init__(
        self,
        client: ClientInterface,
        mana_hi: int,
        mana_lo: int,
        critical_mana: int,
        downtime_mana: int,
        total_mana: int,
    ):
        self.threshold_calculator = ThresholdCalculator(
            stat_config=StatConfig(downtime=downtime_mana,
                                   critical=critical_mana,
                                   hi=mana_hi,
                                   lo=mana_lo),
            priority_threshold_map=type(self).THRESHOLD_PRIORITY_MAP)
        self.threshold_calculator.stat_config.validate()
        self.client = client
        self.mana_hi = mana_hi
        self.mana_lo = mana_lo
        self.critical_mana = critical_mana
        self.downtime_mana = downtime_mana
        self.total_mana = total_mana
        self.should_drink_mana_hi_pri = False
        self.should_drink_critical_mana = False

    def handle_status_change(self, char_status: CharStatus, is_downtime: bool):
        self.update_max(char_status)
        threshold_ms = self.get_threshold_ms(char_status.mana)
        if self.should_drink_mana_critical(char_status.mana):
            self.client.drink_mana(threshold_ms)
        elif self.should_drink_mana_high_priority(char_status.mana):
            self.client.drink_mana(threshold_ms)
        elif self.should_drink_mana_low_priority(char_status, is_downtime):
            self.client.drink_mana(threshold_ms)

    def update_max(self, char_status: CharStatus) -> None:
        if char_status.mana > self.total_mana:
            self.total_mana = char_status.mana

    def is_critical_mana(self, current_mana: int) -> bool:
        return current_mana <= self.critical_mana

    def is_healthy(self, char_status: CharStatus) -> bool:
        return char_status.mana > self.mana_lo

    # Drink mana until high levels when HP is 100% and already hasted
    # with an interval of 2.5 seconds so it does not affect gameplay
    def should_drink_mana_low_priority(self, char_status: CharStatus,
                                       is_downtime: bool) -> bool:
        return is_downtime and char_status.mana <= self.downtime_mana

    def should_drink_mana_high_priority(self, current_mana: int) -> bool:
        if current_mana <= self.mana_hi:
            self.should_drink_mana_hi_pri = True
        elif current_mana > self.mana_lo:
            self.should_drink_mana_hi_pri = False

        return self.should_drink_mana_hi_pri

    def should_drink_mana_critical(self, current_mana: int) -> bool:
        if current_mana <= self.critical_mana:
            self.should_drink_critical_mana = True
        elif current_mana >= self.mana_hi:
            self.should_drink_critical_mana = False

        return self.should_drink_critical_mana

    def get_threshold_ms(self, current_mana: int) -> int:
        return self.threshold_calculator.gen_threshold_ms(current_mana)
