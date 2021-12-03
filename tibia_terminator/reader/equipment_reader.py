#!/usr/bin/env python3.8

import sys
import time

from typing import Tuple, Dict, Any, Callable, Iterable, List, Union

from tibia_terminator.common.lazy_evaluator import (
    immediate, FutureValue, TaskLoop
)
from tibia_terminator.reader.color_spec import (
    ItemName,
    AmuletName,
    RingName,
)
from tibia_terminator.reader.window_utils import ScreenReader
from tibia_terminator.schemas.reader.common import Coord
from tibia_terminator.reader.item_repository_container import (
    ItemRepositoryContainer
)
from tibia_terminator.schemas.reader.interface_config_schema import (
    TibiaWindowSpec,
    EquipmentCoords,
    ItemEntry,
    ItemColors,
)


XY = Tuple[int, int]


class MagicShieldStatus:
    RECENTLY_CAST = "recently_cast"
    OFF_COOLDOWN = "off_cooldown"
    ON_COOLDOWN = "on_cooldown"


UNKNOWN_ITEM = ItemEntry(
    name="unknown",
    equipped_colors=ItemColors("FFF", "FFF", "FFF", "FFF"),
    action_bar_colors=ItemColors("FFF", "FFF", "FFF", "FFF"),
)


class EquipmentStatus(dict):
    @property
    def emergency_action_amulet(self):
        return self["emergency_action_amulet"]

    @property
    def equipped_amulet(self):
        return self["equipped_amulet"]

    @property
    def emergency_action_ring(self):
        return self["emergency_action_ring"]

    @property
    def equipped_ring(self):
        return self["equipped_ring"]

    @property
    def magic_shield_status(self):
        return self["magic_shield_status"]

    def __str__(self):
        return (
            "{\n"
            f"  emergency_action_amulet: {self['emergency_action_amulet']}\n"
            f"  equipped_amulet: {self['equipped_amulet']}\n"
            f"  emergency_action_ring: {self['emergency_action_ring']}\n"
            f"  equipped_ring: {self['equipped_ring']}\n"
            f"  magic_shield_status: {self['magic_shield_status']}\n"
            "}\n"
        )


class FutureEquipmentStatus(EquipmentStatus):
    def __init__(self, future_values: Dict[str, FutureValue[Any]]):
        self.future_values = future_values

    def __getitem__(self, key: str) -> Any:
        return self.future_values[key].get()

    def get(self, key: str, default: Any) -> FutureValue[Any]:
        return self.future_values.get(key, immediate(default))


NOOP: Callable[[str], None] = lambda x: None


class EquipmentReader(ScreenReader):
    def __init__(
        self,
        tibia_wid: int,
        tibia_window_spec: TibiaWindowSpec
    ):
        super().__init__(tibia_wid=tibia_wid)
        self.tibia_window_spec = tibia_window_spec
        self.item_repository = ItemRepositoryContainer(
            tibia_window_spec.item_repository
        )
        self.task_loop = TaskLoop()

    def open(self):
        super().open()
        self.task_loop.start()

    def stop(self):
        super().close()
        self.task_loop.stop()

    def cancel_pending_futures(self):
        """Cancels pending future values for equipment status"""
        self.task_loop.cancel_pending_tasks()

    def get_equipment_status(
        self,
        emergency_action_amulet_cb: Callable[[str], None] = NOOP,
        emergency_action_ring_cb: Callable[[str], None] = NOOP,
        equipped_ring_cb: Callable[[str], None] = NOOP,
        equipped_amulet_cb: Callable[[str], None] = NOOP,
        magic_shield_status_cb: Callable[[str], None] = NOOP,
    ) -> EquipmentStatus:
        return FutureEquipmentStatus(
            {
                "equipped_amulet": self.task_loop.add_future(
                    self.get_equipped_amulet_name,
                    equipped_amulet_cb,
                    lambda e: equipped_amulet_cb("ERROR, check logs"),
                ),
                "equipped_ring": self.task_loop.add_future(
                    self.get_equipped_ring_name,
                    equipped_ring_cb,
                    lambda e: equipped_ring_cb("ERROR, check logs"),
                ),
                "magic_shield_status": self.task_loop.add_future(
                    self.get_magic_shield_status,
                    magic_shield_status_cb,
                    lambda e: magic_shield_status_cb("ERROR, check logs"),
                ),
                "emergency_action_amulet": self.task_loop.add_future(
                    self.get_emergency_action_bar_amulet_name,
                    emergency_action_amulet_cb,
                    lambda e: emergency_action_amulet_cb("ERROR, check logs"),
                ),
                "emergency_action_ring": self.task_loop.add_future(
                    self.get_emergency_action_bar_ring_name,
                    emergency_action_ring_cb,
                    lambda e: emergency_action_ring_cb("ERROR, check logs"),
                ),
            }
        )

    def read_equipment_colors(self, coords: EquipmentCoords) -> ItemColors:
        return ItemColors(
            north=self.get_coord_color(coords.north),
            south=self.get_coord_color(coords.south),
            left=self.get_coord_color(coords.left),
            right=self.get_coord_color(coords.right),
        )

    def gen_square_coords(self, center: Coord, delta: int) -> EquipmentCoords:
        return EquipmentCoords(
            north=Coord(center.x, center.y - delta),
            south=Coord(center.x, center.y + delta),
            left=Coord(center.x - delta, center.y),
            right=Coord(center.x + delta, center.y),
        )

    def matches_screen_item(
        self, coords: EquipmentCoords, color_specs: List[ItemColors]
    ) -> bool:
        actual_color_spec = self.read_equipment_colors(coords)
        for color_spec in color_specs:
            if actual_color_spec == color_spec:
                return True

        return False

    # start: item lookup methods

    def lookup_ring_by_name(self, name: Union[str, ItemName]) -> ItemEntry:
        return self.item_repository.lookup_ring_by_name(name)

    def lookup_amulet_by_name(self, name: Union[str, ItemName]) -> ItemEntry:
        return self.item_repository.lookup_amulet_by_name(name)

    def lookup_amulet_by_action_bar_colors(
        self, colors: ItemColors
    ) -> ItemEntry:
        return self.item_repository.lookup_amulet_by_action_bar_colors(colors)

    def lookup_ring_by_action_bar_colors(self, colors: ItemColors) -> ItemEntry:
        return self.item_repository.lookup_ring_by_action_bar_colors(colors)

    def lookup_ring_by_equipped_colors(self, colors: ItemColors) -> ItemEntry:
        return self.item_repository.lookup_ring_by_equipped_colors(colors)

    def lookup_amulet_by_equipped_colors(self, colors: ItemColors) -> ItemEntry:
        return self.item_repository.lookup_amulet_by_equipped_colors(colors)

    # end: item lookup methods

    # start: read ring methods
    def read_action_bar_ring_colors(self) -> ItemColors:
        return self.read_equipment_colors(
            self.gen_action_bar_ring_coords(
                self.tibia_window_spec.action_bar.ring_center
            )
        )

    def read_action_bar_amulet_colors(self) -> ItemColors:
        return self.read_equipment_colors(
            self.gen_action_bar_amulet_coords(
                self.tibia_window_spec.action_bar.amulet_center
            )
        )

    def gen_action_bar_ring_coords(self, center: Coord) -> EquipmentCoords:
        return self.gen_square_coords(center, 3)

    def get_emergency_action_bar_ring_name(self) -> str:
        return self.lookup_ring_by_action_bar_colors(
            self.read_action_bar_emergency_ring_colors()
        ).name

    def read_action_bar_emergency_ring_colors(self) -> ItemColors:
        return self.read_equipment_colors(
            self.gen_action_bar_ring_coords(
                self.tibia_window_spec.action_bar.emergency_ring_center
            )
        )

    def read_equipped_ring_colors(self) -> ItemColors:
        return self.read_equipment_colors(self.tibia_window_spec.char_equipment.ring)

    def get_equipped_ring_name(self) -> str:
        return self.lookup_ring_by_equipped_colors(
            self.read_equipped_ring_colors()
        ).name

    def is_emergency_action_bar_ring(self, name: ItemName):
        return self.matches_screen_item(
            self.gen_action_bar_ring_coords(
                self.tibia_window_spec.action_bar.emergency_ring_center
            ),
            self.lookup_ring_by_name(name).action_bar_colors,
        )

    def is_ring(self, name: ItemName) -> bool:
        return self.matches_screen_item(
            self.tibia_window_spec.char_equipment.ring,
            self.lookup_ring_by_name(name).equipped_colors,
        )

    def is_ring_empty(self):
        return self.is_ring(RingName.EMPTY)

    # end: read ring methods

    # start: read amulet methods

    def gen_action_bar_amulet_coords(self, center: Coord) -> EquipmentCoords:
        return self.gen_square_coords(center, 10)

    def read_action_bar_emergency_amulet_colors(self) -> ItemColors:
        return self.read_equipment_colors(
            self.gen_action_bar_amulet_coords(
                self.tibia_window_spec.action_bar.emergency_amulet_center
            )
        )

    def get_emergency_action_bar_amulet_name(self) -> str:
        return self.lookup_amulet_by_action_bar_colors(
            self.read_action_bar_emergency_amulet_colors()
        ).name

    def read_equipped_amulet_colors(self) -> ItemColors:
        return self.read_equipment_colors(self.tibia_window_spec.char_equipment.amulet)

    def get_equipped_amulet_name(self) -> str:
        return self.lookup_amulet_by_equipped_colors(
            self.read_equipped_amulet_colors()
        ).name

    def is_emergency_action_bar_amulet(self, name: ItemName) -> bool:
        return self.matches_screen_item(
            self.gen_action_bar_amulet_coords(
                self.tibia_window_spec.action_bar.emergency_amulet_center
            ),
            self.lookup_amulet_by_name(name).action_bar_colors,
        )

    def is_amulet(self, name: ItemName):
        return self.matches_screen_item(
            self.tibia_window_spec.char_equipment.amulet,
            self.lookup_amulet_by_name(name).equipped_colors,
        )

    def is_amulet_empty(self) -> bool:
        return self.is_amulet(AmuletName.EMPTY)

    # end: read amulet methods

    def get_magic_shield_status(self) -> str:
        magic_shield_spec = self.tibia_window_spec.action_bar.magic_shield
        color_str = self.get_coord_color(magic_shield_spec.coord)
        if color_str in magic_shield_spec.off_cooldown_color:
            return MagicShieldStatus.OFF_COOLDOWN
        if color_str in magic_shield_spec.recently_cast_color:
            return MagicShieldStatus.RECENTLY_CAST

        # There are only 3 possible states: recently cast, off cooldown and
        # on cooldown.
        return MagicShieldStatus.ON_COOLDOWN


if __name__ == "__main__":
    import argparse
    import json

    from tibia_terminator.schemas.reader.interface_config_schema import (
        TibiaWindowSpecSchema,
    )

    parser = argparse.ArgumentParser(
        description="Reads equipment status for the Tibia window"
    )

    parser.add_argument(
        "--equipment_status",
        help="Prints all of the equipment status.",
        action="store_true",
    )
    parser.add_argument(
        "--tibia_window_config_path",
        help="Path to the tibia window config JSON file",
        type=str,
        required=True,
    )
    wid_group = parser.add_argument_group()
    wid_group.add_argument("tibia_wid", help="Window id of the tibia client.", type=int)
    wid_group_options = wid_group.add_mutually_exclusive_group()
    wid_group_options.add_argument(
        "--check_specs",
        help="Checks the color specs for the different equipment.",
        action="store_true",
    )
    wid_group_options.add_argument(
        "--check_slot_empty",
        help=(
            "Returns exit code 0 if it is empty, 1 otherwise.\n" "Options: ring, amulet"
        ),
        type=str,
        default=None,
    )
    wid_group_options.add_argument(
        "--magic_shield_status",
        help="Prints the magic shield status.",
        action="store_true",
    )

    class EquipmentReaderSlow(EquipmentReader):
        def __init__(self, tibia_wid: int, tibia_window_spec: TibiaWindowSpec):
            super().__init__(tibia_wid, tibia_window_spec)

        def get_pixels(self, coords: Iterable[XY]) -> List[str]:
            return self.get_pixels_slow(coords)

    def time_perf(title: str, fn: Callable) -> None:
        start = time.time() * 1000
        value = fn()
        end = time.time() * 1000
        elapsed = end - start
        print(title)
        print(f"  Result: {value}")
        print(f"  Elapsed time: {elapsed} ms")

    def check_specs(tibia_wid: int, tibia_window_spec: TibiaWindowSpec) -> None:
        eq_reader = EquipmentReader(tibia_wid, tibia_window_spec)
        eq_reader.open()
        try:
            print(
                "###############\n" "Action bar amulet color spec\n" "###############\n"
            )
            time_perf(
                "eq_reader.read_action_bar_emergency_amulet_colors",
                eq_reader.read_action_bar_emergency_amulet_colors,
            )
            for amulet in tibia_window_spec.item_repository.amulets:

                def is_action_amulet():
                    return eq_reader.is_emergency_action_bar_amulet(amulet.name)

                time_perf(
                    f"\nis_emergency_action_bar_amulet({amulet.name})", is_action_amulet
                )

            time_perf(
                "\nget_emergency_action_bar_amulet_name",
                eq_reader.get_emergency_action_bar_amulet_name,
            )

            print(
                "\n###############\n" "Action bar ring color spec\n" "###############\n"
            )
            time_perf(
                "\neq_reader.read_action_bar_emergency_ring_colors",
                eq_reader.read_action_bar_emergency_ring_colors,
            )
            for ring in tibia_window_spec.item_repository.rings:

                def is_action_ring() -> bool:
                    return eq_reader.is_emergency_action_bar_ring(ring.name)

                time_perf(
                    f"\nis_emergency_action_bar_ring({ring.name})", is_action_ring
                )

            time_perf(
                "\nget_emergency_action_bar_ring_name",
                eq_reader.get_emergency_action_bar_ring_name,
            )

            print("\n###############\n" "Amulet color spec\n" "###############\n")
            time_perf(
                "eq_reader.read_equipped_amulet_colors",
                eq_reader.read_equipped_amulet_colors,
            )
            for amulet in tibia_window_spec.item_repository.amulets:

                def is_amulet():
                    return eq_reader.is_amulet(amulet.name)

                time_perf(f"\nis_amulet({amulet.name})", is_amulet)

            time_perf("\nget_equipped_amulet_name", eq_reader.get_equipped_amulet_name)

            print("\n###############\n" "Ring color spec\n" "###############\n")
            time_perf(
                "eq_reader.read_equipped_ring_colors",
                eq_reader.read_equipped_ring_colors,
            )
            for ring in tibia_window_spec.item_repository.rings:

                def is_ring():
                    return eq_reader.is_ring(ring.name)

                time_perf(f"\nis_ring({ring.name})", is_ring)

            time_perf("\nget_equipped_ring_name", eq_reader.get_equipped_ring_name)

            print("\n###############\n" "Magic shield spec\n" "###############\n")
            time_perf(
                f"eq_reader.get_coord_color({tibia_window_spec.action_bar.magic_shield.coord})",
                lambda: eq_reader.get_coord_color(
                    tibia_window_spec.action_bar.magic_shield.coord
                ),
            )
            time_perf("\nget_magic_shield_status()", eq_reader.get_magic_shield_status)
        finally:
            eq_reader.close()

    def check_slot_empty(
            tibia_wid: int, tibia_window_spec: TibiaWindowSpec, slot: str
    ) -> bool:
        eq_reader = EquipmentReader(tibia_wid, tibia_window_spec)
        eq_reader.open()
        try:
            if slot == "ring":
                return eq_reader.is_ring_empty()
            if slot == "amulet":
                return eq_reader.is_amulet_empty()
        finally:
            eq_reader.close()

        raise Exception("Unknown slot: {}".format(slot))

    def check_magic_shield_status(tibia_wid: int, tibia_window_spec: TibiaWindowSpec):
        eq_reader = EquipmentReaderSlow(tibia_wid, tibia_window_spec)
        print(eq_reader.get_magic_shield_status())

    def check_equipment_status(tibia_wid: int, tibia_window_spec: TibiaWindowSpec):
        eq_reader = EquipmentReader(tibia_wid, tibia_window_spec)
        eq_reader.open()

        def read():
            return f"{eq_reader.get_equipment_status()}"

        try:
            time_perf("check_equipment_status", read)
        finally:
            eq_reader.close()

    def main(args):
        schema = TibiaWindowSpecSchema()
        spec = schema.loadf(args.tibia_window_config_path)
        if args.check_specs is True:
            check_specs(args.tibia_wid, spec)
        elif args.check_slot_empty is not None:
            if check_slot_empty(args.tibia_wid, spec, args.check_slot_empty):
                sys.exit(0)
            else:
                sys.exit(1)
        elif args.magic_shield_status:
            check_magic_shield_status(args.tibia_wid, spec)
        elif args.equipment_status:
            check_equipment_status(args.tibia_wid, spec)

    main(parser.parse_args())
