#!/usr/bin/env python3.8
import argparse
import os
import sys

from tibia_terminator.schemas.common import FactorySchema

def main(schema: FactorySchema,config_file: str) -> None:
    if not os.path.exists(config_file):
        sys.stderr.writelines([f"File {config_file} does not exist."])
        sys.exit(1)

        spec: FactorySchema = schema.loadf(config_file)
        print(spec)
        sys.stderr.writelines(["Successfully parsed the config file."])
        sys.exit(0)

def parse_args(schema: FactorySchema):
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
    main(args.config_file)

