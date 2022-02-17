#!/usr/bin/env python3.8

import argparse
import os
import sys

from tibia_terminator.schemas.common import FactorySchema


def load_file(schema: FactorySchema, config_file: str) -> None:
    if not os.path.exists(config_file):
        sys.stderr.writelines([f"File {config_file} does not exist."])
        sys.exit(1)

    spec = schema.loadf(config_file)
    print(spec)
    sys.stderr.writelines(["Successfully parsed the config file."])
    sys.exit(0)


def main(schema: FactorySchema):
    parser = argparse.ArgumentParser(
        f"{type(schema)} Test",
        description=f"Use this to validate JSON config definitions of {type(schema)}."
    )
    parser.add_argument(
        "config_file",
        help="The file path to the JSON file to parse",
        type=str
    )
    args = parser.parse_args()
    load_file(schema, args.config_file)
