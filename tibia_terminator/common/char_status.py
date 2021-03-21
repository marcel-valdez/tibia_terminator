"""Knows the character's status."""

from typing import Dict, Any, TypeVar

from tibia_terminator.reader.color_spec import (AmuletName, RingName)
from tibia_terminator.common.lazy_evaluator import FutureValue, immediate


class CharStatus:
    def __init__(self, hp: int, speed: int, mana: int, magic_shield_level: int,
                 equipment_status: Dict[str, Any]):
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

    def copy(self,
             hp: int = None,
             speed: int = None,
             mana: int = None,
             magic_shield_level: int = None,
             equipment_status: Dict[str, any] = None):
        return CharStatus(
            hp or self.hp, speed or self.speed, mana or self.mana,
            magic_shield_level or self.magic_shield_level, equipment_status
            or {
                'emergency_action_amulet': self.emergency_action_amulet,
                'emergency_action_ring': self.emergency_action_ring,
                'equipped_ring': self.equipped_ring,
                'magic_shield_status': self.magic_shield_status
            })


class CharStatusAsync(CharStatus):
    def __init__(self, future_stats: FutureValue[Dict[str, int]],
                 future_eq_status: Dict[str, FutureValue[Any]]):
        self.__future_stats = future_stats
        self.__future_eq_status = future_eq_status

    @property
    def __stats(self) -> Dict[str, int]:
        return self.__future_stats.get()

    K = TypeVar('K')

    def __get_eq_status(self, name: str, default_value: K) -> K:
        return self.__future_eq_status.get(name,
                                           immediate(default_value)).get()

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
