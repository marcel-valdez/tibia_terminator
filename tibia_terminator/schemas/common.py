#!/usr/bin/env python3.8

import commentjson as json
import os
from string import Formatter

from marshmallow import Schema, fields, ValidationError
from typing import TypeVar, Generic, Callable, Dict, Any

T = TypeVar("T")


class FactorySchema(Generic[T], Schema):
    def make(self, data, **kwargs) -> T:
        raise Exception("To be implemented by subclass.")

    def loadf(self, path: str) -> T:
        if not os.path.isfile(path):
            raise Exception(f"Path {path} does not exist.")
        data = None
        with open(path, 'r') as file:
            data = json.load(file)
        return self.load(data)


FORMATTER = Formatter()


class ResolvableField(Generic[T], fields.Field):
    cast_fn: Callable[[str], T]

    def __init__(self, cast_fn: Callable[[str], T], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cast_fn = cast_fn

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return str(value)

    def gen_context(self, data: Dict[str, Any]):
        ctx = self.context or {}
        ctx = {**data, **ctx}
        parent = self.parent
        while parent is not None:
            if parent.context is not None:
                ctx = {**ctx, **parent.context}
            if hasattr(parent, 'parent'):
                parent = parent.parent
            else:
                parent = None
        return {**ctx, **data}

    def resolve_str(self, value: str, data: Dict[str, Any]) -> str:
        ctx = self.gen_context(data)
        value = value.format(**ctx)
        has_refs = any(
            [tup[1] for tup in FORMATTER.parse(value) if tup[1] is not None])
        if has_refs:
            return self.resolve_str(value, data)
        else:
            return value

    def resolve_t(self, value_str: str, ref_str: str, field_name: str) -> T:
        value_str = value_str.strip()
        if self.cast_fn is not str and value_str == "None":
            if not self.allow_none:
                raise ValidationError(f"Field {field_name} can't be null, but "
                                      f"{ref_str} resolves to null.")
            else:
                return None
        else:
            return self.cast_fn(value_str)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            if not self.allow_none:
                raise ValidationError("Field {attr} cannot be null.")
            else:
                return value

        if not isinstance(value, str):
            return value
        else:
            value_str = self.resolve_str(value, data)
            resolved_value = self.resolve_t(value_str, value, attr)
            data[attr] = resolved_value
            return resolved_value
