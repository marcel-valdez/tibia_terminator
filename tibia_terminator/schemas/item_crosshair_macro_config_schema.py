from enum import Enum

from marshmallow import fields, ValidationError
from typing import NamedTuple, Dict
from tibia_terminator.schemas.common import FactorySchema


class Direction(Enum):
    LEFT = 1
    UPPER_LEFT = 2
    LOWER_LEFT = 3
    RIGHT = 4
    UPPER_RIGHT = 5
    LOWER_RIGHT = 6
    UP = 7
    DOWN = 8

    @staticmethod
    def from_str(name: str):
        if name is None:
            raise ValidationError("direction name cannot be null")

        name_map = Direction.__members__
        direction = name_map.get(name.upper(), None)
        if direction is None:
            raise ValidationError(
                f"Unknown direction: {name}. " f"Valid values are: {name_map.keys()}"
            )
        return direction

    def __str__(self):
        return self.name.lower()


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
    throttle_ms: int = 250
    direction_map: Dict[str, Direction] = None


class ItemCrosshairMacroConfigSchema(FactorySchema[ItemCrosshairMacroConfig]):
    ctor = ItemCrosshairMacroConfig
    hotkey = fields.Str(required=True)
    action = fields.Function(
        str, MacroAction.from_str, default=MacroAction.CLICK, required=False
    )
    throttle_ms = fields.Int(required=False, default=250, allow_none=False)
    direction_map = fields.Dict(
        keys=fields.Str(),
        values=fields.Function(str, Direction.from_str),
        required=False,
    )
