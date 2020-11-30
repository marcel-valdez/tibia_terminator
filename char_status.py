"""Knows the character's status."""


class CharStatus:
    def __init__(self, hp, speed, mana, magic_shield_level,
                 is_amulet_slot_empty=False, is_ring_slot_empty=False,
                 magic_shield_status=None):
        self.hp = hp
        self.speed = speed
        self.mana = mana
        self.magic_shield_level = magic_shield_level
        self.is_amulet_slot_empty = is_amulet_slot_empty
        self.is_ring_slot_empty = is_ring_slot_empty
        self.magic_shield_status = magic_shield_status
