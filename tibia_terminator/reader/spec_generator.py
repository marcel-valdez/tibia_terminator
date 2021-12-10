#!/usr/bin/env python3.8

import json
import time
import sys

from typing import Callable, List, Optional, Dict, Any
from tibia_terminator.schemas.reader.interface_config_schema import (
    TibiaWindowSpec,
    TibiaWindowSpecSchema,
    ItemEntry,
    ItemColors,
    ItemRepositorySpec,
)
from tibia_terminator.schemas.common import to_dict
from tibia_terminator.reader.window_utils import get_tibia_wid
from tibia_terminator.reader.equipment_reader import EquipmentReader


def read_equipment_colors(
        getter_fn: Callable[[], ItemColors]) -> List[ItemColors]:
    start = time.time()  # seconds
    now = start
    result = []
    # Poll colors for 2.5 seconds with a frequency for 100 ms
    while (now - start) < 2.5:
        colors = getter_fn()
        if colors not in result:
            result.append(colors)
        time.sleep(25 / 1000)  # 25 ms -> 100 samples will be attempted
        now = time.time()
    return result


def generate_repository_spec(
    tibia_wid: int,
    tibia_window_spec: TibiaWindowSpec,
    equipment_type: str,
    ring_name: Optional[str] = None,
    amulet_name: Optional[str] = None,
) -> ItemRepositorySpec:
    eq_reader = EquipmentReader(tibia_wid, tibia_window_spec)
    eq_reader.open()
    try:
        equipped_ring_colors = None
        equipped_amulet_colors = None
        action_amulet_colors = None
        action_ring_colors = None
        rings = []
        amulets = []
        if amulet_name:
            print("Reading amulet colors, this will take 5 seconds...",
                  file=sys.stderr)
            equipped_amulet_colors = read_equipment_colors(
                eq_reader.read_equipped_amulet_colors)
            if equipment_type == "emergency":
                action_amulet_colors = read_equipment_colors(
                    eq_reader.read_action_bar_emergency_amulet_colors)
            elif equipment_type == "tank":
                action_amulet_colors = read_equipment_colors(
                    eq_reader.read_action_bar_tank_amulet_colors)
            else:
                action_amulet_colors = read_equipment_colors(
                    eq_reader.read_action_bar_normal_amulet_colors)
            amulets = [
                ItemEntry(
                    name=amulet_name,
                    equipped_colors=equipped_amulet_colors,
                    action_bar_colors=action_amulet_colors,
                )
            ]

        if ring_name:
            print("Reading ring colors, this will take 5 seconds...",
                  file=sys.stderr)
            equipped_ring_colors = read_equipment_colors(
                eq_reader.read_equipped_ring_colors)
            if equipment_type == "emergency":
                action_ring_colors = read_equipment_colors(
                    eq_reader.read_action_bar_emergency_ring_colors)
            elif equipment_type == "tank":
                action_ring_colors = read_equipment_colors(
                    eq_reader.read_action_bar_tank_ring_colors)
            else:
                action_ring_colors = read_equipment_colors(
                    eq_reader.read_action_bar_normal_ring_colors)
            rings = [
                ItemEntry(
                    name=ring_name,
                    equipped_colors=equipped_ring_colors,
                    action_bar_colors=action_ring_colors,
                )
            ]

        return ItemRepositorySpec(
            amulets=amulets,
            rings=rings,
        )
    finally:
        eq_reader.close()


def to_terminal_rgb(rgb: str) -> str:
    clean_rgb = rgb
    if len(rgb) == 4:
        clean_rgb += "00"
    if len(rgb) == 3:
        clean_rgb = rgb[0] * 2 + rgb[1] * 2 + rgb[2] * 2

    red = str(int(clean_rgb[0:2], 16))
    green = str(int(clean_rgb[2:4], 16))
    blue = str(int(clean_rgb[4:6], 16))

    return "\033[38;2;{R};{G};{B}m{COLOR}\033[0;00m".format(R=red,
                                                            G=green,
                                                            B=blue,
                                                            COLOR=rgb)


def replace_colors(colors: ItemColors) -> ItemColors:
    return ItemColors(
        north=to_terminal_rgb(colors.north),
        south=to_terminal_rgb(colors.south),
        left=to_terminal_rgb(colors.left),
        right=to_terminal_rgb(colors.right),
    )


def replace_all_colors(all_colors: List[ItemColors]) -> List[ItemColors]:
    result = []
    for colors in all_colors:
        result.append(replace_colors(colors))
    return result


def replace_item_colors(item: ItemEntry) -> ItemEntry:
    return ItemEntry(
        name=item.name,
        equipped_colors=replace_all_colors(item.equipped_colors),
        action_bar_colors=replace_all_colors(item.action_bar_colors),
    )


def print_dict(obj: Dict[str, Any], indent=0, key=""):
    prefix = f'"{key}": ' if key else ""
    if isinstance(obj, list):
        print((" " * indent) + f"{prefix}[")
        for entry in obj:
            print_dict(entry, indent + 2)
        print((" " * indent) + "],")
    elif isinstance(obj, dict):
        print((" " * indent) + f"{prefix}{{")
        for entry_key in obj:
            print_dict(obj[entry_key], indent + 2, entry_key)
        print((" " * indent) + "},")
    elif isinstance(obj, tuple):
        print((" " * indent) + f"{prefix}(")
        for entry in obj:
            print_dict(entry, indent + 2)
        print((" " * indent) + "),")
    elif isinstance(obj, str):
        print((" " * indent) + f'{prefix}"{obj}",')
    elif obj is None:
        print((" " * indent) + f"{prefix}null,")
    else:
        print((" " * indent) + f"{prefix}{str(obj)},")


def print_repository_spec(spec: ItemRepositorySpec, config_path: str,
                          colored_output: bool) -> None:
    if len(spec.amulets) > 0:
        print(
            f"// Copy-paste this into item_repository > amulets in {config_path}",
            file=sys.stderr,
        )
        amulet = spec.amulets[0]
        if colored_output:
            amulet = replace_item_colors(amulet)
        print_dict(to_dict(amulet))
        print("")

    if len(spec.rings) > 0:
        print(
            f"// Copy-paste this into item_repository > rings in {config_path}",
            file=sys.stderr,
        )
        ring = spec.rings[0]
        if colored_output:
            ring = replace_item_colors(ring)
        print_dict(to_dict(ring))
        print("")


def print_item_spec(
    tibia_pid: int,
    tibia_window_config_path: str,
    equipment_type: str,
    colored_output: bool,
    ring_name: Optional[str],
    amulet_name: Optional[str],
) -> None:
    tibia_wid = int(get_tibia_wid(tibia_pid, 0))
    schema = TibiaWindowSpecSchema()
    tibia_window_spec = schema.loadf(tibia_window_config_path)
    repository_spec = generate_repository_spec(tibia_wid, tibia_window_spec,
                                               equipment_type, ring_name,
                                               amulet_name)
    print_repository_spec(repository_spec, tibia_window_config_path,
                          colored_output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        ("Script used to generate item color specs to add to your "
         "item_repository field in the tibia window config file"))
    parser.add_argument(
        "--tibia_window_config_file",
        "--config",
        type=str,
        required=True,
        help="File path to the JSON Tibia window config file")
    parser.add_argument(
        "--tibia_pid",
        "--pid",
        "-p",
        type=int,
        required=True,
        help="PID of the Tibia client.")
    parser.add_argument(
        "--ring_name",
        "--rn",
        type=str,
        required=False,
        help="Name to use for the generated ring color profile.")
    parser.add_argument(
        "--amulet_name",
        "--an",
        type=str,
        required=False,
        help="Name to use for the generated amulet color profile.")
    parser.add_argument(
        "--colored_output",
        "--color",
        "-c",
        action="store_true",
        required=False,
        default=False,
        help=(
            "Enables colored output for each of the item colors so that you "
            "can compare the identified colors against what you'd expect from "
            "the item"))
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        choices=["normal", "emergency", "tank"],
        default="normal",
        help="The action bar slot associated to the item.")

    def main():
        args = parser.parse_args()
        if not args.ring_name and not args.amulet_name:
            parser.exit(
                status=1,
                message=(
                    "One or both of ring_name or amulet_name must be specified."
                ),
            )

        print_item_spec(
            tibia_pid=args.tibia_pid,
            tibia_window_config_path=args.tibia_window_config_file,
            ring_name=args.ring_name,
            colored_output=args.colored_output,
            amulet_name=args.amulet_name,
            equipment_type=args.type,
        )

    main()
