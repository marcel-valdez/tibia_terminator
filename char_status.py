"""Knows the character's status."""


from typing import Dict, Any, TypeVar
from color_spec import (AmuletName, RingName)
from lazy_evaluator import FutureValue, future


class CharStatus:
    def __init__(self, hp: int, speed: int, mana: int, magic_shield_level: int,
                 equipment_status: Dict):
        self.hp = hp
        self.speed = speed
        self.mana = mana
        self.magic_shield_level = magic_shield_level
        self.emergency_action_amulet = \
            equipment_status.get('emergency_action_amulet', 'ERROR')
        self.equipped_amulet = equipment_status.get('equipped_amulet', 'ERROR')
        self.emergency_action_ring = \
            equipment_status.get('emergency_action_ring', 'ERROR')
        self.equipped_ring = equipment_status.get('equipped_ring', 'ERROR')
        self.is_amulet_slot_empty = self.equipped_amulet == AmuletName.EMPTY
        self.is_ring_slot_empty = self.equipped_ring == RingName.EMPTY
        self.magic_shield_status = \
            equipment_status.get('magic_shield_status', 'ERROR')


class CharStatusAsync(CharStatus):
    def __init__(self,
                 future_stats: FutureValue[Dict[str, int]],
                 future_eq_status: FutureValue[Dict[str, Any]]):
        self.__future_stats = future_stats
        self.__future_eq_status = future_eq_status

    @property
    def __stats(self) -> Dict[str, int]:
        return self.__future_stats.get()

    K = TypeVar('K')

    def __get_eq_status(self, name: str, default_value: K) -> K:
        return self.__future_eq_status.get().get(name, default_value)

    @property
    def hp(self) -> int:
        return self.__stats.get("hp", -1)

    @property
    def speed(self) -> int:
        return self.__stats.get("speed", -1)

    @property
    def mana(self) -> int:
        return self.__stats.get("mana", -1)

    @property
    def magic_shield_level(self) -> int:
        return self.__stats.get("magic_shield", -1)

    @property
    def emergency_action_amulet(self):
        return self.__get_eq_status('emergency_action_amulet', 'ERROR')

    @property
    def equipped_amulet(self):
        return self.__get_eq_status('equipped_amulet', 'ERROR')

    @property
    def emergency_action_ring(self):
        return self.__get_eq_status('emergency_action_ring', 'ERROR')

    @property
    def equipped_ring(self):
        return self.__get_eq_status('equipped_ring', 'ERROR')

    @property
    def magic_shield_status(self):
        return self.__get_eq_status('magic_shield_status', 'ERROR')

    @property
    def is_amulet_slot_empty(self):
        return self.equipped_amulet == AmuletName.EMPTY

    @property
    def is_ring_slot_empty(self):
        return self.equipped_ring == RingName.EMPTY

T = TypeVar('T')
def immediate(value: T) -> FutureValue[T]:
    return future(lambda: value)
