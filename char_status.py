"""Knows the character's status."""


from typing import Dict
from color_spec import (AmuletName, RingName)


class CharStatus:
    def __init__(self, hp: int, speed: int, mana: int, magic_shield_level: int,
      equipment_status: Dict):
        self.hp = hp
        self.speed = speed
        self.mana = mana
        self.magic_shield_level = magic_shield_level
        self.emergency_action_amulet = equipment_status['emergency_action_amulet']
        self.equipped_amulet = equipment_status['equipped_amulet']
        self.emergency_action_ring = equipment_status['emergency_action_ring']
        self.equipped_ring = equipment_status['equipped_ring']
        self.is_amulet_slot_empty = self.equipped_amulet == AmuletName.EMPTY
        self.is_ring_slot_empty = self.equipped_ring == RingName.EMPTY
        self.magic_shield_status = equipment_status['magic_shield_status']
