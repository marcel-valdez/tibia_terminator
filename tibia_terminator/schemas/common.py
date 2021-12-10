#!/usr/bin/env python3.8

import os
from string import Formatter
from uuid import uuid1

from typing import TypeVar, Generic, Callable, Dict, Any, NamedTuple, Optional

import commentjson as json

from marshmallow import Schema, fields, ValidationError, post_load, pre_load

T = TypeVar("T")


class ResolvableMixin():
    __RESOLVE_CONTEXT_KEY = uuid1()

    @property
    def resolve_context(self) -> Any:
        if self.context.get(ResolvableMixin.__RESOLVE_CONTEXT_KEY) is None:
            self.context[ResolvableMixin.__RESOLVE_CONTEXT_KEY] = []
        return self.context[ResolvableMixin.__RESOLVE_CONTEXT_KEY]

    @pre_load
    def push_context(self, data, **kwargs):
        self.resolve_context.append(data)
        return data

    @post_load
    def pop_context(self, data, **kwargs):
        context = self.context[ResolvableMixin.__RESOLVE_CONTEXT_KEY]
        del context[len(context) - 1]
        return data

    def gen_full_context(self):
        # what if context is a list?
        ctx = {}
        for context in reversed(self.resolve_context):
            ctx.update(context)
        return ctx


class FactorySchema(Generic[T], Schema, ResolvableMixin):
    def __init__(self,
                 ctor: Callable[[Dict[str, Any]], T] = None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if ctor is not None:
            self.ctor = ctor

    @post_load
    def make(self, data, **kwargs) -> T:
        return self.ctor(**data)

    def loadf(self, path: str) -> T:
        if not os.path.isfile(path):
            raise Exception(f"Path {path} does not exist.")
        try:
            with open(path, 'r', encoding="utf-8") as file:
                return self.load(json.load(file))
        except Exception as e:
            raise Exception(f"Error while loading: {path}") from e


FORMATTER = Formatter()

K = TypeVar("K")


class ResolvableField(Generic[K], fields.Field, ResolvableMixin):

    def __init__(self, cast_fn: Callable[[str], K], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cast_fn = cast_fn

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return str(value)

    def resolve_str(self, value: str, context: Dict[str, Any]) -> str:
        value = eval(f'f"{value}"', {}, context)
        has_refs = any(
            tup[1] for tup in FORMATTER.parse(value) if tup[1] is not None
        )
        if has_refs:
            return self.resolve_str(value, context)

        return value

    def resolve_t(
            self, value_str: str, ref_str: str, field_name: str
    ) -> Optional[K]:
        value_str = value_str.strip()
        if self.cast_fn is not str and value_str == "None":
            if not self.allow_none:
                raise ValidationError(f"Field {field_name} can't be null, but "
                                      f"{ref_str} resolves to null.")
            return None

        return self.cast_fn(value_str)

    def _deserialize(self, value, attr, data, **kwargs):
        self.push_context(data)
        try:
            if value is None:
                if not self.allow_none:
                    raise ValidationError("Field {attr} cannot be null.")
                return value

            if not isinstance(value, str):
                return value

            value_str = self.resolve_str(value, self.gen_full_context())
            resolved_value = self.resolve_t(value_str, value, attr)
            data[attr] = resolved_value
            return resolved_value
        except TypeError as e:
            raise TypeError(f"Type error while deserializing {value} for field {attr}", e)
        finally:
            self.pop_context(data)


def isnamedtupleinstance(x):
    _type = type(x)
    bases = _type.__bases__
    if len(bases) != 1 or bases[0] != tuple:
        return False

    _fields = getattr(_type, '_fields', None)
    if not isinstance(_fields, tuple):
        return False

    return all(type(i) == str for i in _fields)


def to_dict(obj: NamedTuple) -> Any:
    if isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_dict(value) for value in obj]
    if isnamedtupleinstance(obj):
        return {key: to_dict(value) for key, value in obj._asdict().items()}
    if isinstance(obj, tuple):
        return tuple(to_dict(value) for value in obj)

    return obj
