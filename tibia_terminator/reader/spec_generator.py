#!/usr/bin/env python3.8

import json
import time
import sys

from typing import NamedTuple, Callable, List, Optional
from tibia_terminator.schemas.reader.interface_config_schema import (
    TibiaWindowSpec,
    TibiaWindowSpecSchema,
    EquipmentCoords,
    ItemEntry,
    ItemColors,
    ItemRepositorySpec,
)
from tibia_terminator.schemas.common import to_dict
from tibia_terminator.reader.window_utils import get_tibia_wid
from tibia_terminator.reader.equipment_reader import EquipmentReader


def read_equipment_colors(getter_fn: Callable[[], ItemColors]) -> List[ItemColors]:
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
    ring_name: Optional[str],
    amulet_name: Optional[str],
    is_emergency: bool,
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
            print(
                "Reading amulet colors, this will take 5 seconds...",
                file=sys.stderr
            )
            equipped_amulet_colors = read_equipment_colors(
                eq_reader.read_equipped_amulet_colors
            )
            if is_emergency:
                action_amulet_colors = read_equipment_colors(
                    eq_reader.read_action_bar_emergency_amulet_colors
                )
            else:
                action_amulet_colors = read_equipment_colors(
                    eq_reader.read_action_bar_amulet_colors
                )
            amulets = [
                ItemEntry(
                    name=amulet_name,
                    equipped_colors=equipped_amulet_colors,
                    action_bar_colors=action_amulet_colors,
                )
            ]

        if ring_name:
            print(
                "Reading ring colors, this will take 5 seconds...",
                file=sys.stderr
            )
            equipped_ring_colors = read_equipment_colors(
                eq_reader.read_equipped_ring_colors
            )
            if is_emergency:
                action_ring_colors = read_equipment_colors(
                    eq_reader.read_action_bar_emergency_ring_colors
                )
            else:
                action_ring_colors = read_equipment_colors(
                    eq_reader.read_action_bar_ring_colors
                )
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


def print_repository_spec(spec: ItemRepositorySpec, config_path: str) -> None:
    if len(spec.amulets) > 0:
        print(
            f"// Copy-paste this into item_repository > amulets in {config_path}",
            file=sys.stderr
        )
        json.dump(to_dict(spec.amulets[0]), fp=sys.stdout, indent=2)
        print("")

    if len(spec.rings) > 0:
        print(
            f"// Copy-paste this into item_repository > rings in {config_path}",
            file=sys.stderr
        )
        json.dump(to_dict(spec.rings[0]), fp=sys.stdout, indent=2)
        print("")


def print_item_spec(
    tibia_pid: int,
    tibia_window_config_path: str,
    ring_name: Optional[str],
    amulet_name: Optional[str],
    is_emergency: bool,
) -> None:
    tibia_wid = int(get_tibia_wid(tibia_pid))
    schema = TibiaWindowSpecSchema()
    tibia_window_spec = schema.loadf(tibia_window_config_path)
    repository_spec = generate_repository_spec(
        tibia_wid, tibia_window_spec, ring_name, amulet_name, is_emergency
    )
    print_repository_spec(repository_spec, tibia_window_config_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        (
            "Script used to generate item color specs to add to your "
            "item_repository field in the tibia window config file"
        )
    )
    parser.add_argument("--tibia_window_config_file", type=str, required=True)
    parser.add_argument("--tibia_pid", type=int, required=True)
    parser.add_argument("--ring_name", type=str, required=False)
    parser.add_argument("--amulet_name", type=str, required=False)
    parser.add_argument("--is_emergency", action="store_true", required=False)

    def main():
        args = parser.parse_args()
        if not args.ring_name and not args.amulet_name:
            parser.exit(
                status=1,
                message=("One or both of ring_name or amulet_name must be"
                         "specified.")
            )

        print_item_spec(
            args.tibia_pid,
            args.tibia_window_config_file,
            args.ring_name,
            args.amulet_name,
            args.is_emergency
        )

    main()
