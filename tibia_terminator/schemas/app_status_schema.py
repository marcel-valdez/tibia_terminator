#!/usr/bin/env python3.8

from enum import Enum

from marshmallow import fields, EXCLUDE, ValidationError
from typing import Optional, NamedTuple
from tibia_terminator.schemas.common import FactorySchema


class AppState(Enum):
    PAUSED = 1
    RUNNING = 2
    CONFIG_SELECTION = 3
    EXIT = 4

    @staticmethod
    def from_str(name: str) -> 'AppState':
        if name is None:
            raise ValidationError("App State cannot be null or empty")

        name_map = AppState.__members__
        app_state = name_map.get(name.upper(), None)
        if app_state is None:
            raise ValidationError(f"Unknown App State: {name}. "
                                  f"Valid values are: {name_map.keys()}")
        return app_state

    def __str__(self):
        return self.name.lower()


class AppStatus(NamedTuple):
    selected_config_name: Optional[str] = ""
    state: Optional[AppState] = AppState.CONFIG_SELECTION

    @staticmethod
    def serialize_state(status: 'AppStatus') -> str:
        return status.state.__str__()


class AppStatusSchema(FactorySchema[AppStatus]):
    class Meta:
        unknown = EXCLUDE


    ctor = AppStatus
    selected_config_name = fields.Str(required=False)
    state = fields.Function(
        serialize=AppStatus.serialize_state,
        deserialize=AppState.from_str,
        default=AppState.CONFIG_SELECTION,
        required=False
    )
