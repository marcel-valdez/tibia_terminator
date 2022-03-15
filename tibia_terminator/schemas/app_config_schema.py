#!/usr/bin/env python3.8

from typing import (Optional, List, Union, Dict, Any, NamedTuple)

from marshmallow import fields, pre_load
from tibia_terminator.schemas.cli import main
from tibia_terminator.schemas.common import (FactorySchema)


class AppConfig(NamedTuple):
    # Always required
    pid: int
    # Always required
    mana_memory_address: Optional[str] = None
    # Required for hunting
    speed_memory_address: Optional[str] = None
    # Required to make runes, not required for hunting.
    soul_points_memory_address: Optional[str] = None
    # The HP memory address can be reliably calculated based on the
    # mana memory address.
    # Not required, since it can be calculated.
    hp_memory_address: Optional[str] = None
    # from the addresses that match max to min values of magic shield, the
    # one that keeps track of current shield points is the one in the middle
    # that has another address matching +2 positions ahead of it.
    magic_shield_memory_address: Optional[str] = None
    max_mana_address: Optional[str] = None
    max_hp_address: Optional[str] = None


class AppConfigs(NamedTuple):
    default_pid: Optional[int] = None
    configs: List[AppConfig] = []

    def __getitem__(self, key: Union[int, str]) -> AppConfig:
        if isinstance(key, str):
            if not key.isnumeric():
                raise KeyError("Only numbers or numbers as strings allowed.")
            else:
                key = int(key)

        if not isinstance(key, int):
            raise KeyError("Only numbers or numbers as strings allowed.")

        return next((c for c in self.configs if c.pid == key), None)


def _validate_hex(hex_number: Optional[str] = None) -> bool:
    if hex_number is None:
        return True

    try:
        int(hex_number, 16)
        return True
    except ValueError:
        return False


class AppConfigSchema(FactorySchema[AppConfig]):
    # Always required
    ctor = AppConfig
    pid = fields.Int(required=True)
    mana_memory_address = fields.Str(allow_none=True, validate=_validate_hex)
    speed_memory_address = fields.Str(allow_none=True, validate=_validate_hex)
    soul_points_memory_address = fields.Str(allow_none=True, validate=_validate_hex)
    hp_memory_address = fields.Str(allow_none=True, validate=_validate_hex)
    magic_shield_memory_address = fields.Str(allow_none=True, validate=_validate_hex)
    max_mana_address = fields.Str(allow_none=True, validate=_validate_hex)
    max_hp_address = fields.Str(allow_none=True, validate=_validate_hex)

    @pre_load
    def clean_addresses(self, data, **kwargs) -> Dict[str, Any]:
        copy = data.copy()
        for key, value in data.items():
            if key.endswith("_address"):
                if value is not None and value.startswith("0x"):
                    copy[key] = value[2:]
        return copy


class AppConfigsSchema(FactorySchema[AppConfigs]):
    ctor = AppConfigs
    default_pid = fields.Int(required=False)
    configs = fields.List(fields.Nested(AppConfigSchema))


if __name__ == "__main__":
    main(AppConfigsSchema())
