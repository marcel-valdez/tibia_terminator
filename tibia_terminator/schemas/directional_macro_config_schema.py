#!/usr/bin/env python3.8

from marshmallow import fields
from typing import NamedTuple, List, Tuple
from tibia_terminator.schemas.common import FactorySchema


class DirectionalMacroConfig(NamedTuple):
    spell_key_rotation: List[str]
    rotation_threshold_secs: int
    direction_pairs: List[Tuple[str, str]]


class DirectionalMacroConfigSchema(FactorySchema[DirectionalMacroConfig]):
    ctor = DirectionalMacroConfig
    spell_key_rotation = fields.List(fields.Str(), required=True)
    rotation_threshold_secs = fields.Int(default=3600)
    direction_pairs = fields.List(fields.Tuple((fields.Str(required=True),
                                                fields.Str(required=False,
                                                           allow_none=True,
                                                           default=None))),
                                  required=True)
