#!/usr/bin/env python3.8

import argparse
import sys
import time

from typing import Tuple, Dict, Any, Callable

from common.lazy_evaluator import immediate, FutureValue, TaskLoop
from reader.color_spec import (spec, AMULET_REPOSITORY, RING_REPOSITORY,
                               ItemName, AmuletName, RingName, PixelColor)
from reader.window_utils import (ScreenReader, matches_screen_slow)

parser = argparse.ArgumentParser(
    description='Reads equipment status for the Tibia window')

parser.add_argument('--equipment_status',
                    help='Prints all of the equipment status.',
                    action='store_true')
wid_group = parser.add_argument_group()
wid_group.add_argument('tibia_wid', help='Window id of the tibia client.')
wid_group_options = wid_group.add_mutually_exclusive_group()
wid_group_options.add_argument(
    '--check_specs',
    help='Checks the color specs for the different equipment.',
    action='store_true')
wid_group_options.add_argument(
    '--check_slot_empty',
    help=('Returns exit code 0 if it is empty, 1 otherwise.\n'
          'Options: ring, amulet'),
    type=str,
    default=None)
wid_group_options.add_argument('--magic_shield_status',
                               help='Prints the magic shield status.',
                               action='store_true')


class MagicShieldStatus:
    RECENTLY_CAST = 'recently_cast'
    OFF_COOLDOWN = 'off_cooldown'
    ON_COOLDOWN = 'on_cooldown'


# Playable area set at Y: 696 (698 on laptop) with 2 cols on left and 2 cols
# on right.
ACTION_BAR_SQUARE_LEN = 36
# 10th action bar item right to left, 2 columns on the left, 2 columns on the
# right.
EMERGENCY_ACTION_BAR_AMULET_CENTER_X = 1178
EMERGENCY_ACTION_BAR_CENTER_Y = 719
EMERGENCY_ACTION_BAR_AMULET_COORDS = [
    # upper pixel
    (EMERGENCY_ACTION_BAR_AMULET_CENTER_X, EMERGENCY_ACTION_BAR_CENTER_Y - 10),
    # lower pixel
    (EMERGENCY_ACTION_BAR_AMULET_CENTER_X, EMERGENCY_ACTION_BAR_CENTER_Y + 10),
    # left pixel
    (EMERGENCY_ACTION_BAR_AMULET_CENTER_X - 10, EMERGENCY_ACTION_BAR_CENTER_Y),
    # right pixel
    (EMERGENCY_ACTION_BAR_AMULET_CENTER_X + 10, EMERGENCY_ACTION_BAR_CENTER_Y)
]

EQUIPPED_AMULET_COORDS = [
    # upper pixel
    (1768, 259),
    # lower pixel
    (1768, 272),
    # left pixel
    (1758, 261),
    # right pixel
    (1779, 261)
]

EMERGENCY_ACTION_BAR_RING_CENTER_X = 1215
EMERGENCY_ACTION_BAR_RING_CENTER_Y = 722
EMERGENCY_ACTION_BAR_RING_COORDS = [
    # upper pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X, EMERGENCY_ACTION_BAR_RING_CENTER_Y - 3
     ),
    # lower pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X, EMERGENCY_ACTION_BAR_RING_CENTER_Y + 3
     ),
    # left pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X - 3, EMERGENCY_ACTION_BAR_RING_CENTER_Y
     ),
    # right pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X + 3, EMERGENCY_ACTION_BAR_RING_CENTER_Y
     ),
]

EQUIPPED_RING_COORDS = [
    # upper pixel
    (1768, 333),
    # lower pixel
    (1768, 338),
    # left pixel
    (1765, 337),
    # right pixel
    (1770, 337)
]

MAGIC_SHIELD_SPEC = {
    MagicShieldStatus.RECENTLY_CAST: [
        "3730A",
    ],
    MagicShieldStatus.OFF_COOLDOWN: [
        "B9A022",
    ]
}

MAGIC_SHIELD_COORDS = [(1285, 760)]


class EquipmentStatus():
    @property
    def emergency_action_amulet(self):
        return self['emergency_action_amulet']

    @property
    def equipped_amulet(self):
        return self['equipped_amulet']

    @property
    def emergency_action_ring(self):
        return self['emergency_action_ring']

    @property
    def equipped_ring(self):
        return self['equipped_ring']

    @property
    def magic_shield_status(self):
        return self['magic_shield_status']

    def __str__(self):
        return (
            "{\n"
            f"  emergency_action_amulet: {self['emergency_action_amulet']}\n"
            f"  equipped_amulet: {self['equipped_amulet']}\n"
            f"  emergency_action_ring: {self['emergency_action_ring']}\n"
            f"  equipped_ring: {self['equipped_ring']}\n"
            f"  magic_shield_status: {self['magic_shield_status']}\n"
            "}\n")


class DictEquipmentStatus(dict, EquipmentStatus):
    pass


class FutureEquipmentStatus(EquipmentStatus):
    def __init__(self, future_values: Dict[str, FutureValue[Any]]):
        self.future_values = future_values

    def __getitem__(self, key: str) -> Any:
        return self.future_values[key].get()

    def get(self, key: str, default: Any) -> FutureValue[Any]:
        return self.future_values.get(key, immediate(default))


NOOP: Callable[[str], None] = lambda x: None


class EquipmentReader(ScreenReader):
    def __init__(self):
        super().__init__()
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

    def _compare_screen_coords(self, coords: Tuple[int, int],
                               color_spec: Tuple[str, ...]):
        return ScreenReader.matches_screen(self, coords, color_spec)

    def matches_screen(self, coords, specs):
        if type(specs) == list or type(specs) == tuple:
            for animation_spec in specs:
                if self._compare_screen_coords(coords, animation_spec.colors):
                    return True
            return False
        else:
            return self._compare_screen_coords(coords, specs.colors)

    def get_equipment_status(
        self,
        emergency_action_amulet_cb: Callable[[str], None] = NOOP,
        emergency_action_ring_cb: Callable[[str], None] = NOOP,
        equipped_ring_cb: Callable[[str], None] = NOOP,
        equipped_amulet_cb: Callable[[str], None] = NOOP,
        magic_shield_status_cb: Callable[[str],
                                         None] = NOOP) -> EquipmentStatus:
        return FutureEquipmentStatus({
            'equipped_amulet':
            self.task_loop.add_future(
                self.get_equipped_amulet_name, equipped_amulet_cb,
                lambda e: equipped_amulet_cb('ERROR, check logs')),
            'equipped_ring':
            self.task_loop.add_future(
                self.get_equipped_ring_name, equipped_ring_cb,
                lambda e: equipped_ring_cb('ERROR, check logs')),
            'magic_shield_status':
            self.task_loop.add_future(
                self.get_magic_shield_status, magic_shield_status_cb,
                lambda e: magic_shield_status_cb('ERROR, check logs')),
            'emergency_action_amulet':
            self.task_loop.add_future(
                self.get_emergency_action_bar_amulet_name,
                emergency_action_amulet_cb,
                lambda e: emergency_action_amulet_cb('ERROR, check logs')),
            'emergency_action_ring':
            self.task_loop.add_future(
                self.get_emergency_action_bar_ring_name,
                emergency_action_ring_cb,
                lambda e: emergency_action_ring_cb('ERROR, check logs')),
        })

    def get_emergency_action_bar_amulet_name(self) -> AmuletName:
        color_spec = spec(*self.get_pixels(EMERGENCY_ACTION_BAR_AMULET_COORDS))
        return AMULET_REPOSITORY.get_action_name(color_spec)

    def get_equipped_amulet_name(self) -> AmuletName:
        color_spec = spec(*self.get_pixels(EQUIPPED_AMULET_COORDS))
        return AMULET_REPOSITORY.get_equipment_name(color_spec)

    def get_emergency_action_bar_ring_name(self) -> RingName:
        color_spec = spec(*self.get_pixels(EMERGENCY_ACTION_BAR_RING_COORDS))
        return RING_REPOSITORY.get_action_name(color_spec)

    def get_equipped_ring_name(self) -> RingName:
        color_spec = spec(*self.get_pixels(EQUIPPED_RING_COORDS))
        return RING_REPOSITORY.get_equipment_name(color_spec)

    def is_emergency_action_bar_amulet(self, name: ItemName):
        amulet = AMULET_REPOSITORY.get(name)
        return self.matches_screen(EMERGENCY_ACTION_BAR_AMULET_COORDS,
                                   amulet.action_color_specs)

    def is_emergency_action_bar_ring(self, name: ItemName):
        ring = RING_REPOSITORY.get(name)
        return self.matches_screen(EMERGENCY_ACTION_BAR_RING_COORDS,
                                   ring.action_color_specs)

    def is_amulet(self, name: ItemName):
        spec = AMULET_REPOSITORY.get(name).eq_color_specs
        return self.matches_screen(EQUIPPED_AMULET_COORDS, spec)

    def is_amulet_empty(self):
        return self.is_amulet(AmuletName.EMPTY)

    def is_ring(self, name: ItemName):
        spec = RING_REPOSITORY.get(name).eq_color_specs
        return self.matches_screen(EQUIPPED_RING_COORDS, spec)

    def is_ring_empty(self):
        return self.is_ring(RingName.EMPTY)

    def get_magic_shield_status(self) -> str:
        for name in MAGIC_SHIELD_SPEC:
            specs = []
            if isinstance(MAGIC_SHIELD_SPEC[name][0], list):
                specs = [spec(*_spec) for _spec in MAGIC_SHIELD_SPEC[name]]
            else:
                specs = spec(*MAGIC_SHIELD_SPEC[name])

            if self.matches_screen(MAGIC_SHIELD_COORDS, specs):
                return name
        # There are only 3 possible states: recently cast, off cooldown and
        # on cooldown.
        return MagicShieldStatus.ON_COOLDOWN


class EquipmentReaderSlow(EquipmentReader):
    def __init__(self, wid):
        self.wid = wid

    def get_pixels(self, coords: Tuple[int, int]):
        return self.get_pixels_slow(self.wid, coords)

    def _compare_screen_coords(self, coords: Tuple[int, int],
                               color_spec: Tuple[PixelColor, ...]):
        colors = list(map(lambda c: str(c), color_spec))
        return matches_screen_slow(self.wid, coords, colors)


def time_perf(title, fn):
    start = time.time() * 1000
    value = fn()
    end = time.time() * 1000
    elapsed = end - start
    print(title)
    print(f"  Result: {value}")
    print(f"  Elapsed time: {elapsed} ms")


def check_specs():
    eq_reader = EquipmentReader()
    eq_reader.open()
    try:
        print("###############\n"
              "Amulet action bar color spec\n"
              "###############\n")
        for (x, y) in EMERGENCY_ACTION_BAR_AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in AMULET_REPOSITORY.name_to_item.keys():

            def fn():
                return eq_reader.is_emergency_action_bar_amulet(name)

            time_perf(f"\nis_emergency_action_bar_amulet({name})", fn)

        def emergency_action_bar_amulet_name_fn():
            return eq_reader.get_emergency_action_bar_amulet_name()

        time_perf("\nget_emergency_action_bar_amulet_name",
                  emergency_action_bar_amulet_name_fn)

        print("\n###############\n"
              "Action bar ring color spec\n"
              "###############\n")
        for (x, y) in EMERGENCY_ACTION_BAR_RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in RING_REPOSITORY.name_to_item.keys():

            def is_action_ring():
                return eq_reader.is_emergency_action_bar_ring(name)

            time_perf(f"\nis_emergency_action_bar_ring({name})",
                      is_action_ring)

        def emergency_action_bar_ring_name_fn():
            return eq_reader.get_emergency_action_bar_ring_name()

        time_perf("\nget_emergency_action_bar_ring_name",
                  emergency_action_bar_ring_name_fn)

        print("\n###############\n" "Amulet color spec\n" "###############\n")
        for (x, y) in EQUIPPED_AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in AMULET_REPOSITORY.name_to_item.keys():

            def is_amulet():
                return eq_reader.is_amulet(name)

            time_perf(f"\nis_amulet('{name}')", is_amulet)

        def equipped_amulet_name_fn():
            return eq_reader.get_equipped_amulet_name()

        time_perf("\nget_equipped_amulet_name()", equipped_amulet_name_fn)

        print("\n###############\n" "Ring color spec\n" "###############\n")
        for (x, y) in EQUIPPED_RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in RING_REPOSITORY.name_to_item.keys():

            def is_ring():
                return eq_reader.is_ring(name)

            time_perf(f"\nis_ring('{name}')", is_ring)

        def equipped_ring_name_fn():
            return eq_reader.get_equipped_ring_name()

        time_perf("\nget_equipped_ring_name()", equipped_ring_name_fn)

        print("\n###############\n" "Magic shield spec\n" "###############\n")
        print(eq_reader.get_pixel_color(*MAGIC_SHIELD_COORDS[0]))

        def magic_shield_fn():
            return eq_reader.get_magic_shield_status()

        time_perf('\nget_magic_shield_status()', magic_shield_fn)
    finally:
        eq_reader.close()


def check_slot_empty(tibia_wid, slot):
    eq_reader = EquipmentReaderSlow(tibia_wid)
    if slot == 'ring':
        return eq_reader.is_ring_empty()
    elif slot == 'amulet':
        return eq_reader.is_amulet_empty()
    else:
        raise Exception('Unknown slot: {}'.format(slot))


def check_magic_shield_status(tibia_wid):
    eq_reader = EquipmentReaderSlow(tibia_wid)
    print(eq_reader.get_magic_shield_status())


def check_equipment_status(tibia_wid):
    eq_reader = EquipmentReader()
    eq_reader.open()

    def read():
        return f'{eq_reader.get_equipment_status()}'

    try:
        time_perf('check_equipment_status', read)
    finally:
        eq_reader.close()


def main(args):
    if args.check_specs is True:
        check_specs()
    elif args.check_slot_empty is not None:
        if check_slot_empty(args.tibia_wid, args.check_slot_empty):
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.magic_shield_status:
        check_magic_shield_status(args.tibia_wid)
    elif args.equipment_status:
        check_equipment_status(args.tibia_wid)


if __name__ == '__main__':
    main(parser.parse_args())
