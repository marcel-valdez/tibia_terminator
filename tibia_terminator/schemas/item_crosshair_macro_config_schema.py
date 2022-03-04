#!/usr/bin/env python3.8


from enum import Enum
from typing import NamedTuple, Dict, Optional

from marshmallow import fields, ValidationError
from tibia_terminator.schemas.common import FactorySchema, Direction
from tibia_terminator.schemas.cli import main


DEFAULT_ITEM_CROSSHAIR_THROTTLE_MS = 250


class MacroAction(Enum):
    CLICK = 1
    CLICK_BEHIND = 2

    @staticmethod
    def from_str(name: str):
        if name is None:
            raise ValidationError("macro action name cannot be null")

        name_map = MacroAction.__members__
        action = name_map.get(name.upper(), None)
        if action is None:
            raise ValidationError(
                f"Unknown macro action: {name}. " f"Valid values are: {name_map.keys()}"
            )
        return action

    def __str__(self):
        return self.name.lower()


class ItemCrosshairMacroConfig(NamedTuple):
    hotkey: str
    action: MacroAction = MacroAction.CLICK
    throttle_ms: int = DEFAULT_ITEM_CROSSHAIR_THROTTLE_MS
    direction_map: Optional[Dict[str, Direction]] = None


class ItemCrosshairMacroConfigSchema(FactorySchema[ItemCrosshairMacroConfig]):
    ctor = ItemCrosshairMacroConfig
    hotkey = fields.Str(required=True)
    action = fields.Function(
        str, MacroAction.from_str, default=MacroAction.CLICK, required=False
    )
    throttle_ms = fields.Int(
        required=False, default=DEFAULT_ITEM_CROSSHAIR_THROTTLE_MS, allow_none=False
    )
    direction_map = fields.Dict(
        keys=fields.Str(),
        values=fields.Function(str, Direction.from_str),
        required=False,
    )


if __name__ == "__main__":
    main(ItemCrosshairMacroConfigSchema())
