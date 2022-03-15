#!/usr/bin/env python3.8

from marshmallow import fields
from typing import Optional, NamedTuple
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

    toggle_tank_amulet: Optional[str] = None
    toggle_tank_ring: Optional[str] = None
    start_tank_mode: Optional[str] = None
    cancel_tank_mode: Optional[str] = None

    potion_minor_heal: Optional[str] = None
    potion_medium_heal: Optional[str] = None
    potion_greater_heal: Optional[str] = None
    loot_modifier: Optional[str] = None


class HotkeysConfigSchema(FactorySchema[HotkeysConfig]):
    ctor = HotkeysConfig
    minor_heal = fields.Str(required=True)
    medium_heal = fields.Str(required=True)
    greater_heal = fields.Str(required=True)
    potion_minor_heal = fields.Str(required=False, allow_none=True)
    potion_medium_heal = fields.Str(required=False, allow_none=True)
    potion_greater_heal = fields.Str(required=False, allow_none=True)
    haste = fields.Str(required=True)
    equip_ring = fields.Str(required=True)
    equip_amulet = fields.Str(required=True)
    eat_food = fields.Str(required=True)
    magic_shield = fields.Str(required=True)
    cancel_magic_shield = fields.Str(required=True)
    mana_potion = fields.Str(required=True)

    toggle_emergency_amulet = fields.Str(required=True)
    toggle_emergency_ring = fields.Str(required=True)
    start_emergency = fields.Str(required=True)
    cancel_emergency = fields.Str(required=True)

    toggle_tank_amulet = fields.Str(required=False, allow_none=True)
    toggle_tank_ring = fields.Str(required=False, allow_none=True)
    start_tank_mode = fields.Str(required=False, allow_none=True)
    cancel_tank_mode = fields.Str(required=False, allow_none=True)

    loot = fields.Str(required=True)

    up = fields.Str(required=True, default="w")
    down = fields.Str(required=True, default="s")
    left = fields.Str(required=True, default="a")
    right = fields.Str(required=True, default="d")
    upper_left = fields.Str(required=True, default="w")
    upper_right = fields.Str(required=True, default="r")
    lower_left = fields.Str(required=True, default="x")
    lower_right = fields.Str(required=True, default="c")
    loot_button = fields.Str(required=True, default="right")
    loot_modifier = fields.Str(required=False, default=None, allow_none=True)
