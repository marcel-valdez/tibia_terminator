"""Keeps mana at healthy levels."""

from common.logger import debug


class ManaKeeper():
    def __init__(self, client, mana_hi, mana_lo, critical_mana, downtime_mana,
                 total_mana):
        self.client = client
        self.last_cast_timestamp = 0
        self.cast_counter = 0
        self.mana_hi = mana_hi
        self.mana_lo = mana_lo
        self.critical_mana = critical_mana
        self.downtime_mana = downtime_mana
        self.total_mana = total_mana
        self.should_drink_mana_hi_pri = False
        self.should_drink_critical_mana = False

    def handle_status_change(self, char_status, is_downtime):
        self.update_max(char_status)
        should_drink_mana_critical = self.should_drink_mana_critical(
            char_status.mana)
        should_drink_mana_hi_pri = self.should_drink_mana_high_priority(
            char_status.mana)
        should_drink_mana_low_pri = self.should_drink_mana_low_priority(
            char_status, is_downtime)

        if should_drink_mana_critical:
            self.client.drink_mana(666)
        elif should_drink_mana_hi_pri:
            self.client.drink_mana(1000)
        elif should_drink_mana_low_pri:
            self.client.drink_mana(2500)

    def update_max(self, char_status):
        if char_status.mana > self.total_mana:
            self.total_mana = char_status.mana

    def get_missing_mana(self, mana):
        return self.total_mana - mana

    def is_critical_mana(self, mana):
        return mana <= self.critical_mana

    def is_healthy_mana(self, mana):
        return mana > self.mana_lo

    # Drink mana until high levels when HP is 100% and already hasted
    # with an interval of 2.5 seconds so it does not affect gameplay
    def should_drink_mana_low_priority(self, char_status, is_downtime):
        debug(
            '[should_drink_mana_low_priority] mana: ' + str(char_status.mana),
            3)

        if is_downtime and char_status.mana <= self.downtime_mana:
            return True
        else:
            return False

    def should_drink_mana_high_priority(self, mana):
        if mana > self.mana_lo:
            self.should_drink_mana_hi_pri = False
        elif mana <= self.mana_hi:
            self.should_drink_mana_hi_pri = True

        return self.should_drink_mana_hi_pri

    def should_drink_mana_critical(self, mana):
        if mana <= self.critical_mana:
            self.should_drink_critical_mana = True
        elif mana >= self.mana_hi:
            self.should_drink_critical_mana = False

        return self.should_drink_critical_mana
