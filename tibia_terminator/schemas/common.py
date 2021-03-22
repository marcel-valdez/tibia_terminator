#!/usr/bin/env python3.8

import commentjson as json
import os

from marshmallow import Schema
from typing import TypeVar, Generic


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
