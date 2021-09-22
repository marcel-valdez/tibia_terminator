#!/usr/bin/env python3.8

from marshmallow import fields
from typing import NamedTuple
from tibia_terminator.schemas.common import FactorySchema


class HotkeysConfig(NamedTuple):
    minor_heal: str
    medium_heal: str
    greater_heal: str
    haste: str
    equip_ring: str
    equip_amulet: str
    eat_food: str
    magic_shield: str
    cancel_magic_shield: str
    mana_potion: str
    toggle_emergency_amulet: str
    toggle_emergency_ring: str
    loot: str
    start_emergency: str
    cancel_emergency: str
    up: str
    down: str
    left: str
    right: str
    upper_left: str
    upper_right: str
    lower_left: str
    lower_right: str
    loot_button: str = "right"
    loot_modifier: str = "shift"


class HotkeysConfigSchema(FactorySchema[HotkeysConfig]):
    ctor = HotkeysConfig
    minor_heal = fields.Str(required=True)
    medium_heal = fields.Str(required=True)
    greater_heal = fields.Str(required=True)
    haste = fields.Str(required=True)
    equip_ring = fields.Str(required=True)
    equip_amulet = fields.Str(required=True)
    eat_food = fields.Str(required=True)
    magic_shield = fields.Str(required=True)
    cancel_magic_shield = fields.Str(required=True)
    mana_potion = fields.Str(required=True)
    toggle_emergency_amulet = fields.Str(required=True)
    toggle_emergency_ring = fields.Str(required=True)
    loot = fields.Str(required=True)
    start_emergency = fields.Str(required=True)
    cancel_emergency = fields.Str(required=True)
    up = fields.Str(required=True, default="w")
    down = fields.Str(required=True, default="s")
    left = fields.Str(required=True, default="a")
    right = fields.Str(required=True, default="d")
    upper_left = fields.Str(required=True, default="w")
    upper_right = fields.Str(required=True, default="r")
    lower_left = fields.Str(required=True, default="x")
    lower_right = fields.Str(required=True, default="c")
    loot_button = fields.Str(required=True, default="right")
    loot_modifier = fields.Str(required=False)
