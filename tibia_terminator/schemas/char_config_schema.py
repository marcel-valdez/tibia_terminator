#!/usr/bin/env python3.8

from copy import deepcopy
from marshmallow import fields, pre_load, ValidationError
from typing import (Optional, NamedTuple, List, Dict, Any, TypeVar)
from tibia_terminator.schemas.common import FactorySchema, ResolvableField
from tibia_terminator.schemas.directional_macro_config_schema import (
    DirectionalMacroConfig, DirectionalMacroConfigSchema)


class ItemCrosshairMacroConfig(NamedTuple):
    hotkey: str


T = TypeVar("T")


class ItemCrosshairMacroConfigSchema(FactorySchema[ItemCrosshairMacroConfig]):
    ctor = ItemCrosshairMacroConfig
    hotkey = fields.Str(required=True)


class BattleConfig(NamedTuple):
    config_name: str
    hasted_speed: int
    heal_at_missing: int
    downtime_heal_at_missing: int
    mana_hi: int
    mana_lo: int
    critical_mana: int
    downtime_mana: int
    minor_heal: int
    medium_heal: int
    greater_heal: int
    emergency_hp_threshold: int
    base: str = None
    hidden: bool = False
    should_equip_amulet: bool = True
    should_equip_ring: bool = True
    should_eat_food: bool = True
    item_crosshair_macros: List[ItemCrosshairMacroConfig] = []
    directional_macros: List[DirectionalMacroConfig] = []
    magic_shield_type: Optional[str] = "emergency"
    magic_shield_threshold: Optional[int] = None


class BattleConfigSchema(FactorySchema[BattleConfig]):
    ctor = BattleConfig
    config_name = fields.Str(required=True)
    hidden = fields.Boolean(required=False, default=False)
    hasted_speed = ResolvableField(int, required=True)
    heal_at_missing = ResolvableField(int, required=True)
    downtime_heal_at_missing = ResolvableField(int, required=True)
    mana_hi = ResolvableField(int, required=True)
    mana_lo = ResolvableField(int, required=True)
    critical_mana = ResolvableField(int, required=True)
    downtime_mana = ResolvableField(int, required=True)
    minor_heal = ResolvableField(int, required=True)
    medium_heal = ResolvableField(int, required=True)
    greater_heal = ResolvableField(int, required=True)
    base = fields.Str(required=False)
    should_equip_amulet = fields.Boolean(default=True, required=False)
    should_equip_ring = fields.Boolean(default=True, required=False)
    should_eat_food = fields.Boolean(default=True, required=False)
    magic_shield_type = fields.Str(default="emergency", required=False)
    magic_shield_threshold = ResolvableField(int, required=False)
    emergency_hp_threshold = ResolvableField(int, required=True)
    item_crosshair_macros = fields.List(
        fields.Nested(ItemCrosshairMacroConfigSchema),
        required=False,
        default=[])
    directional_macros = fields.List(
        fields.Nested(DirectionalMacroConfigSchema),
        required=False,
        default=[])


class CharConfig(NamedTuple):
    char_name: str
    total_hp: int
    total_mana: int
    base_speed: int
    hasted_speed: int
    strong_hasted_speed: int
    battle_configs: List[BattleConfig]


class CharConfigSchema(FactorySchema[CharConfig]):
    ctor = CharConfig
    char_name = fields.Str(required=True)
    total_hp = fields.Int(required=True)
    total_mana = fields.Int(required=True)
    base_speed = fields.Int(required=True)
    hasted_speed = fields.Int(required=True)
    strong_hasted_speed = fields.Int(required=True)
    battle_configs = fields.List(fields.Nested(BattleConfigSchema), default=[])

    def gen_battle_config_map(
            self,
            battle_configs: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        result = {}
        for config in battle_configs:
            config_name = config.get('config_name', None)
            if config_name is None:
                raise ValidationError("Battle config is missing a config_name")
            if config_name in result:
                raise ValidationError(
                    f"Duplicate battle config name {config_name}")
            result[config_name] = config
        return result

    def expand_inheritance(
            self, battle_configs_map: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        expanded_configs = []
        for (key, config) in battle_configs_map.items():
            expanded_config = {}
            base_key = config.get('base', None)
            if base_key is None:
                expanded_config = config.copy()
            else:
                base_config = battle_configs_map.get(base_key, None)
                if base_config is None:
                    raise ValidationError(
                        f"Unknown base battle config {base_key}")
                expanded_config = {**base_config, **config}
            expanded_configs.append(expanded_config)
        return expanded_configs

    @pre_load
    def apply_inheritance(self, data: Dict[str, Any],
                          **kwargs) -> Dict[str, Any]:
        battle_configs = self.gen_battle_config_map(
            data.get('battle_configs', []))
        expanded_battle_configs = self.expand_inheritance(battle_configs)
        data['battle_configs'] = expanded_battle_configs
        return data
