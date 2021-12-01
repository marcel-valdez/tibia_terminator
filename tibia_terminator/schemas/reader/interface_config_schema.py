#!/usr/bin/env python3.8

from marshmallow import fields
from typing import Optional, NamedTuple, List, Union, Dict, Any
from tibia_terminator.schemas.common import FactorySchema
from tibia_terminator.schemas.reader.common import Coord, CoordSchema

# POPOs

class MagicShieldSpec(NamedTuple):
    coord: Coord
    recently_cast_color: List[str]
    off_cooldown_color: List[str]


class ActionBarSpec(NamedTuple):
    square_len: int
    amulet_center: Coord
    ring_center: Coord
    emergency_amulet_center: Coord
    emergency_ring_center: Coord
    magic_shield: MagicShieldSpec


class EquipmentCoords(NamedTuple):
    north: Coord
    south: Coord
    left: Coord
    right: Coord


class ItemColors(NamedTuple):
    north: str
    south: str
    left: str
    right: str


class ItemEntry(NamedTuple):
    name: str
    equipped_colors: List[ItemColors]
    action_bar_colors: List[ItemColors]

class ItemRepositorySpec(NamedTuple):
    rings: List[ItemEntry]
    amulets: List[ItemEntry]


class CharEquipmentCoords(NamedTuple):
    amulet: EquipmentCoords
    ring: EquipmentCoords


class TibiaWindowSpec(NamedTuple):
    action_bar: ActionBarSpec
    char_equipment: CharEquipmentCoords
    item_repository: ItemRepositorySpec


# marshmallow spec

class MagicShieldSpecSchema(FactorySchema[MagicShieldSpec]):
    ctor = MagicShieldSpec
    coord = fields.Nested(CoordSchema, required=True)
    recently_cast_color = fields.List(fields.Str(), required=True)
    off_cooldown_color = fields.List(fields.Str(), required=True)


class ItemColorsSchema(FactorySchema[ItemColors]):
    ctor = ItemColors
    north = fields.Str(required=True)
    south = fields.Str(required=True)
    left = fields.Str(required=True)
    right = fields.Str(required=True)


class ItemEntrySchema(FactorySchema[ItemEntry]):
    ctor = ItemEntry
    name = fields.Str(required=True)
    equipped_colors = fields.List(fields.Nested(ItemColorsSchema), required=True)
    action_bar_colors = fields.List(fields.Nested(ItemColorsSchema), required=True)


class ActionBarSpecSchema(FactorySchema[ActionBarSpec]):
    ctor = ActionBarSpec
    square_len = fields.Int(required=True)
    amulet_center = fields.Nested(CoordSchema, required=True)
    ring_center = fields.Nested(CoordSchema, required=True)
    emergency_amulet_center = fields.Nested(CoordSchema, required=True)
    emergency_ring_center = fields.Nested(CoordSchema, required=True)
    magic_shield = fields.Nested(MagicShieldSpecSchema, required=True)


class EquipmentCoordsSchema(FactorySchema[EquipmentCoords]):
    ctor = EquipmentCoords
    north = fields.Nested(CoordSchema, required=True)
    south = fields.Nested(CoordSchema, required=True)
    left = fields.Nested(CoordSchema, required=True)
    right = fields.Nested(CoordSchema, required=True)


class CharEquipmentCoordsSchema(FactorySchema[CharEquipmentCoords]):
    ctor = CharEquipmentCoords
    amulet = fields.Nested(EquipmentCoordsSchema, required=True)
    ring = fields.Nested(EquipmentCoordsSchema, required=True)


class ItemRepositorySpecSchema(FactorySchema[ItemRepositorySpec]):
    ctor = ItemRepositorySpec
    rings = fields.List(fields.Nested(ItemEntrySchema), required=True)
    amulets = fields.List(fields.Nested(ItemEntrySchema), required=True)


class TibiaWindowSpecSchema(FactorySchema[TibiaWindowSpec]):
    ctor = TibiaWindowSpec
    action_bar = fields.Nested(ActionBarSpecSchema, required=True)
    char_equipment = fields.Nested(CharEquipmentCoordsSchema, required=True)
    item_repository = fields.Nested(ItemRepositorySpecSchema, required=True)


if __name__ == "__main__":
    from tibia_terminator.schemas.cli import parse_args

    parse_args(TibiaWindowSpecSchema())
