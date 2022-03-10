#!/usr/bin/env python3.8


from typing import NamedTuple, Optional

from marshmallow import fields, validate
from tibia_terminator.schemas.common import FactorySchema, Direction
from tibia_terminator.schemas.cli import main


class DragMacroConfig(NamedTuple):
    hotkey: str
    direction: Direction
    distance: int
    duration_ms: Optional[int] = 100
    btn: Optional[str] = "left"
    throttle_ms: Optional[int] = 50


class DragMacroConfigSchema(FactorySchema[DragMacroConfig]):
    ctor = DragMacroConfig
    hotkey = fields.Str(required=True)
    direction = fields.Function(
        str,
        Direction.from_str,
        required=True,
        validate=validate.OneOf(list(Direction.values())),
    )
    distance = fields.Int(required=True, default=0.1, allow_none=False)
    duration_ms = fields.Int(required=False, default=100)
    btn = fields.Str(
        required=False, allow_none=False, validate=validate.OneOf(["left", "right"])
    )
    throttle_ms = fields.Int(required=False, default=50)


if __name__ == "__main__":
    main(DragMacroConfigSchema())
