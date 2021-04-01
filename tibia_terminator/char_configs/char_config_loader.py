#!/usr/bin/env python3.8

import argparse
import os
import sys

from typing import Iterable
from marshmallow import ValidationError
from tibia_terminator.schemas.char_config_schema import (CharConfigSchema,
                                                         CharConfig)

parser = argparse.ArgumentParser(
    description='Test the character config loader')
parser.add_argument("--dir_path", type=str, required=True)


def load_configs(dir_path: str) -> Iterable[CharConfig]:
    config_files = sorted(fetch_config_files(dir_path))
    return parse_configs(config_files)


def parse_configs(config_files: Iterable[str]) -> Iterable[CharConfig]:
    for config_file in config_files:
        try:
            yield CharConfigSchema().loadf(config_file)
        except ValidationError as e:
            print(f"Error when parsing file {config_file}.\n{e}",
                  file=sys.stderr)
            sys.exit(1)


def fetch_config_files(dir_path: str) -> Iterable[str]:
    for file in os.listdir(dir_path):
        if (os.path.isfile(os.path.join(dir_path, file))
                and file.endswith('.charconfig')):
            yield os.path.join(dir_path, file)


def main(dir_path: str):
    for char_config in load_configs(dir_path):
        print(char_config)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.dir_path)
