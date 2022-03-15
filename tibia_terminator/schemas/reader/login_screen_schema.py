#!/usr/bin/env python3.8

from typing import NamedTuple
from marshmallow import fields
from tibia_terminator.schemas.common import FactorySchema
from tibia_terminator.schemas.reader.common import CoordColor, CoordColorSchema, Coord, CoordSchema


class LoginScreenSpec(NamedTuple):
    north: CoordColor
    south: CoordColor
    left: CoordColor
    right: CoordColor
    email_field: Coord
    password_field: Coord
    login_btn: Coord
    char_list_ok_btn: Coord


class LoginScreenSpecSchema(FactorySchema[LoginScreenSpec]):
    ctor = LoginScreenSpec
    north = fields.Nested(CoordColorSchema, required=True, allow_none=False)
    south = fields.Nested(CoordColorSchema, required=True, allow_none=False)
    left = fields.Nested(CoordColorSchema, required=True, allow_none=False)
    right = fields.Nested(CoordColorSchema, required=True, allow_none=False)
    email_field = fields.Nested(CoordSchema, required=True, allow_none=False)
    password_field = fields.Nested(CoordSchema, required=True, allow_none=False)
    login_btn = fields.Nested(CoordSchema, required=True, allow_none=False)
    char_list_ok_btn = fields.Nested(CoordSchema, required=True, allow_none=False)


if __name__ == "__main__":
    from tibia_terminator.schemas.cli import main
    main(LoginScreenSpecSchema())

