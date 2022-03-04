#!/usr/bin/env python3.8

import argparse

from collections import OrderedDict
from typing import Optional, NamedTuple, List, Dict, Any, Mapping
from marshmallow import fields, pre_load, ValidationError, validate
from tibia_terminator.schemas.item_crosshair_macro_config_schema import (
    ItemCrosshairMacroConfig,
    ItemCrosshairMacroConfigSchema,
)
from tibia_terminator.schemas.drag_macro_config_schema import (
    DragMacroConfig,
    DragMacroConfigSchema
)
from tibia_terminator.schemas.common import FactorySchema, ResolvableField
from tibia_terminator.schemas.directional_macro_config_schema import (
    DirectionalMacroConfig,
    DirectionalMacroConfigSchema,
)
from tibia_terminator.schemas.cli import main


class BattleConfig(NamedTuple):
    config_name: str

    hasted_speed: int

    downtime_mana: int
    mana_hi: int
    mana_lo: int
    critical_mana: int

    heal_at_missing: int
    downtime_heal_at_missing: int
    minor_heal: int
    medium_heal: int
    greater_heal: int
    emergency_hp_threshold: int

    base: Optional[str] = None
    hidden: bool = False

    potion_hp_hi: Optional[int] = None
    potion_hp_lo: Optional[int] = None
    potion_hp_critical: Optional[int] = None

    should_eat_food: bool = True
    should_equip_amulet: bool = True
    should_equip_ring: bool = True

    magic_shield_type: Optional[str] = "emergency"
    magic_shield_threshold: Optional[int] = None

    item_crosshair_macros: Optional[List[ItemCrosshairMacroConfig]] = []
    directional_macros: Optional[List[DirectionalMacroConfig]] = []
    drag_macros: Optional[List[DragMacroConfig]] = []
    equip_amulet_secs: Optional[int] = 1
    equip_ring_secs: Optional[int] = 1


class BattleConfigSchema(FactorySchema[BattleConfig]):
    ctor = BattleConfig
    base = fields.Str(required=False)
    config_name = fields.Str(required=True)
    hidden = fields.Boolean(required=False, default=False)
    vocation = fields.Str(required=False)

    hasted_speed = ResolvableField(float, required=True)
    should_eat_food = fields.Boolean(default=True, required=False)

    downtime_mana = ResolvableField(float, required=True)
    mana_hi = ResolvableField(float, required=True)
    mana_lo = ResolvableField(float, required=True)
    critical_mana = ResolvableField(float, required=True)

    downtime_heal_at_missing = ResolvableField(float, required=True)
    heal_at_missing = ResolvableField(float, required=True)
    minor_heal = ResolvableField(float, required=True)
    medium_heal = ResolvableField(float, required=True)
    greater_heal = ResolvableField(float, required=True)
    potion_hp_hi = ResolvableField(float, required=False)
    potion_hp_lo = ResolvableField(float, required=False)
    potion_hp_critical = ResolvableField(float, required=False)

    should_equip_amulet = fields.Boolean(default=True, required=False)
    should_equip_ring = fields.Boolean(default=True, required=False)

    magic_shield_type = fields.Str(default="emergency",
                                   required=False,
                                   allow_none=True)
    magic_shield_threshold = ResolvableField(float, required=False)
    emergency_hp_threshold = ResolvableField(float, required=True)
    item_crosshair_macros = fields.List(
        fields.Nested(ItemCrosshairMacroConfigSchema),
        required=False,
        default=[])
    drag_macros = fields.List(
        fields.Nested(DragMacroConfigSchema),
        required=False,
        default=[])
    directional_macros = fields.List(
        fields.Nested(DirectionalMacroConfigSchema),
        required=False,
        default=[])


class CharConfig(NamedTuple):
    char_name: str
    vocation: str
    total_hp: int
    total_mana: int
    base_speed: int
    hasted_speed: int
    strong_hasted_speed: int
    battle_configs: List[BattleConfig]


class CharConfigSchema(FactorySchema[CharConfig]):
    ctor = CharConfig
    char_name = fields.Str(required=True)
    vocation = fields.Str(required=True,
                          validate=validate.OneOf(["mage", "knight"]))
    total_hp = fields.Int(required=True)
    total_mana = fields.Int(required=True)
    base_speed = fields.Int(required=True)
    hasted_speed = fields.Int(required=True)
    strong_hasted_speed = fields.Int(required=True)
    battle_configs = fields.List(fields.Nested(BattleConfigSchema), default=[])

    def gen_battle_config_map(
            self,
            battle_configs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        result = OrderedDict()
        for config in battle_configs:
            config_name = config.get("config_name", None)
            if config_name is None:
                raise ValidationError("Battle config is missing a config_name")
            if config_name in result:
                raise ValidationError(
                    f"Duplicate battle config name {config_name}")
            result[config_name] = config
        return result

    def expand_inheritance_recursively(
        self, config: Mapping[str, Optional[Any]],
        configs_map: Mapping[str, Optional[Mapping[str,
                                                   Any]]]) -> Dict[str, Any]:
        expanded_config: Mapping[str, Optional[Any]] = {}
        base_config: Mapping[str, Optional[Any]] = config
        while True:
            expanded_config = {**base_config, **expanded_config}
            base_key = base_config.get("base", None)
            if base_key is None:
                break

            maybe_base_config = configs_map.get(base_key, None)
            if maybe_base_config is None:
                raise ValidationError(f"Unknown base battle config {base_key}")
            base_config = maybe_base_config
        # keep the original name
        expanded_config["config_name"] = config["config_name"]
        # don't inherit hidden
        if "hidden" in config:
            expanded_config["hidden"] = config["hidden"]
        elif "hidden" in expanded_config:
            expanded_config.pop("hidden")
        # don't inherit base
        if "base" in config:
            expanded_config["base"] = config["base"]
        elif "base" in expanded_config:
            expanded_config.pop("base")
        return expanded_config

    def expand_inheritance(
            self, battle_configs_map: Dict[str,
                                           Dict[str,
                                                Any]]) -> List[Dict[str, Any]]:
        expanded_configs = []
        for (_, config) in battle_configs_map.items():
            expanded_config = self.expand_inheritance_recursively(
                config, battle_configs_map)
            expanded_configs.append(expanded_config)
        return expanded_configs

    @pre_load
    def apply_inheritance(self, data: Dict[str, Any],
                          **kwargs) -> Dict[str, Any]:
        battle_configs = self.gen_battle_config_map(
            data.get("battle_configs", []))
        expanded_battle_configs = self.expand_inheritance(battle_configs)
        data["battle_configs"] = expanded_battle_configs
        return data


if __name__ == "__main__":
    main(CharConfigSchema())
