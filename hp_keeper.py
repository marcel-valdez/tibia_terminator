"""Keeps health points at healthy levels."""

class HpKeeper:
    def __init__(self, client, total_hp, heal_at_missing, exura_heal,
                 exura_gran_heal, downtime_heal_at_missing):
        self.client = client
        self.total_hp = total_hp
        self.heal_at_missing = heal_at_missing
        self.exura_heal = exura_heal
        self.exura_gran_heal = exura_gran_heal
        self.downtime_heal_at_missing = downtime_heal_at_missing

    def handle_status_change(self, char_status, is_downtime):
        self.update_max(char_status)
        missing_hp = self.get_missing_hp(char_status.hp)
        if missing_hp >= self.heal_at_missing:
            if missing_hp <= self.exura_heal:
                self.client.cast_exura(throttle_ms=500)
            elif missing_hp <= self.exura_gran_heal:
                self.client.cast_exura_gran(throttle_ms=250)
            else:
                self.client.cast_exura_sio(throttle_ms=250)
        elif is_downtime and missing_hp >= self.downtime_heal_at_missing:
            # during downtime heal every 2.5 seconds when we're missing HP
            self.client.cast_exura(throttle_ms=2500)

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
        return missing_hp >= self.exura_gran_heal
