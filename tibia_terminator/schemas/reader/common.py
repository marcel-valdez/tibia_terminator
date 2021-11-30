#!/usr/bin/env python3.8

from marshmallow import fields
from typing import Optional, NamedTuple, List, Union, Dict, Any
from tibia_terminator.schemas.common import FactorySchema


class Coord(NamedTuple):
    x: int
    y: int


class CoordColor(NamedTuple):
    coord: Coord
    color: str


class CoordSchema(FactorySchema[Coord]):
    ctor = Coord
    x = fields.Int(required=True)
    y = fields.Int(required=True)


class CoordColorSchema(FactorySchema[CoordColor]):
    ctor = CoordColor
    coord = fields.Nested(CoordSchema, required=True, allow_none=False)
    color = fields.Str(required=True, allow_none=False)


if __name__ == "__main__":
    from tibia_terminator.schemas.cli import parse_args
    parse_args(CoordColorSchema())
