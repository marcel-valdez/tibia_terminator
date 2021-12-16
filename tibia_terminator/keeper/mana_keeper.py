"""Keeps mana at healthy levels."""


from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.interface.client_interface import ClientInterface


class ManaKeeper:
    def __init__(
        self,
        client: ClientInterface,
        mana_hi: int,
        mana_lo: int,
        critical_mana: int,
        downtime_mana: int,
        total_mana: int,
    ):
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
    def should_drink_mana_low_priority(
        self, char_status: CharStatus, is_downtime: bool
    ) -> bool:
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
        critical_threshold_ms = 666
        if current_mana <= self.critical_mana:
            return critical_threshold_ms

        hi_pri_threshold_ms = 1000
        half_hi_pri_stat = (self.mana_hi + self.mana_lo) / 2
        if self.critical_mana < current_mana <= half_hi_pri_stat:
            hi_pri_pct = (current_mana - self.critical_mana) / (
                half_hi_pri_stat - self.critical_mana)
            critical_to_hi_pri_ms = hi_pri_threshold_ms - critical_threshold_ms
            return int(critical_threshold_ms +
                       (hi_pri_pct * critical_to_hi_pri_ms))

        downtime_threshold_ms = 2500
        if half_hi_pri_stat < current_mana <= self.downtime_mana:
            hi_pri_to_downtime_ms = downtime_threshold_ms - hi_pri_threshold_ms
            downtime_pct = (current_mana - half_hi_pri_stat) / (
                self.downtime_mana - half_hi_pri_stat)
            return int(hi_pri_threshold_ms +
                       (downtime_pct * hi_pri_to_downtime_ms))

        if current_mana > self.downtime_mana:
            return 1000 * 60 * 5

        raise Exception("This should never happen.")
