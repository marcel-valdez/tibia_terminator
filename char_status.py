"""Knows the character's status."""


from equipment_reader import (AmuletName, RingName)


class CharStatus:
    def __init__(self, hp, speed, mana, magic_shield_level, equipment_status):
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
