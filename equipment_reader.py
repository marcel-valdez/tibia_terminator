#!/usr/bin/env python3.8


import argparse
import sys
import time
from window_utils import (ScreenReader, matches_screen_slow)
from color_spec import (spec, AMULET_REPOSITORY,
                        RING_REPOSITORY, ItemName, AmuletName, RingName)


parser = argparse.ArgumentParser(
    description='Reads equipment status for the Tibia window')
parser.add_argument('--check_specs',
                    help='Checks the color specs for the different equipment.',
                    action='store_true')
parser.add_argument('--check_slot_empty',
                    help=('Returns exit code 0 if it is empty, 1 otherwise.\n'
                          'Options: ring, amulet'),
                    type=str,
                    default=None)
parser.add_argument('--magic_shield_status',
                    help='Prints the magic shield status.',
                    action='store_true')
parser.add_argument('tibia_wid',
                    help='Window id of the tibia client.')


class MagicShieldStatus:
    RECENTLY_CAST = 'recently_cast'
    OFF_COOLDOWN = 'off_cooldown'
    ON_COOLDOWN = 'on_cooldown'


# Playable area set at Y: 696 with 2 cols on left and 2 cols on right
ACTION_BAR_SQUARE_LEN = 36
# 10th action bar item right to left, 2 columns on the left, 2 columns on the right
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
    (EMERGENCY_ACTION_BAR_RING_CENTER_X,
     EMERGENCY_ACTION_BAR_RING_CENTER_Y - 3),
    # lower pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X,
     EMERGENCY_ACTION_BAR_RING_CENTER_Y + 3),
    # left pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X - 3,
     EMERGENCY_ACTION_BAR_RING_CENTER_Y),
    # right pixel
    (EMERGENCY_ACTION_BAR_RING_CENTER_X + 3,
     EMERGENCY_ACTION_BAR_RING_CENTER_Y),
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

MAGIC_SHIELD_COORDS = [
    (1285, 760)
]


class EquipmentReader(ScreenReader):

    def matches_screen(self, coords, specs):
        if type(specs) == list or type(specs) == tuple:
            for animation_spec in specs:
                if ScreenReader.matches_screen(self, coords, animation_spec.colors):
                    return True
            return False
        else:
            return ScreenReader.matches_screen(self, coords, specs.colors)

    def get_emergency_action_bar_amulet_name(self):
        color_spec = spec(*self.get_pixels(EMERGENCY_ACTION_BAR_AMULET_COORDS))
        return AMULET_REPOSITORY.get_action_name(color_spec)

    def get_equipped_amulet_name(self):
        color_spec = spec(*self.get_pixels(EQUIPPED_AMULET_COORDS))
        return AMULET_REPOSITORY.get_equipment_name(color_spec)

    def get_emergency_action_bar_ring_name(self):
        color_spec = spec(*self.get_pixels(EMERGENCY_ACTION_BAR_RING_COORDS))
        return RING_REPOSITORY.get_action_name(color_spec)

    def get_equipped_ring_name(self):
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

    def get_magic_shield_status(self):
        for name in MAGIC_SHIELD_SPEC:
            if self.matches_screen(MAGIC_SHIELD_COORDS,
                                   spec(*MAGIC_SHIELD_SPEC[name])):
                return name
        # There are only 3 possible states: recently cast, off cooldown and
        # on cooldown.
        return MagicShieldStatus.ON_COOLDOWN


class EquipmentReaderSlow():
    def __init__(self, wid):
        self.wid = wid

    def is_amulet(self, name: ItemName):
        spec = AMULET_REPOSITORY.get(name).eq_color_specs
        return matches_screen_slow(self.wid, EQUIPPED_AMULET_COORDS, spec)

    def is_amulet_empty(self):
        return self.is_amulet(AmuletName.EMPTY)

    def is_ring(self, name: ItemName):
        spec = RING_REPOSITORY.get(name).eq_color_specs
        return matches_screen_slow(self.wid, EQUIPPED_RING_COORDS, spec)

    def is_ring_empty(self):
        return self.is_ring(RingName.EMPTY)

    def get_magic_shield_status(self):
        for name in MAGIC_SHIELD_SPEC:
            if matches_screen_slow(self.wid,
                                   MAGIC_SHIELD_COORDS,
                                   MAGIC_SHIELD_SPEC[name]):
                return name
        # There are only 3 possible states: recently cast, off cooldown and
        # on cooldown.
        return MagicShieldStatus.ON_COOLDOWN


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
            def fn():
                return eq_reader.is_emergency_action_bar_ring(name)
            time_perf(f"\nis_emergency_action_bar_ring({name})", fn)

        def emergency_action_bar_ring_name_fn():
            return eq_reader.get_emergency_action_bar_ring_name()

        time_perf("\nget_emergency_action_bar_ring_name",
                  emergency_action_bar_ring_name_fn)

        print("\n###############\n"
              "Amulet color spec\n"
              "###############\n")
        for (x, y) in EQUIPPED_AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in AMULET_REPOSITORY.name_to_item.keys():
            def fn():
                return eq_reader.is_amulet(name)
            time_perf(f"\nis_amulet('{name}')", fn)

        def equipped_amulet_name_fn():
            return eq_reader.get_equipped_amulet_name()
        time_perf("\nget_equipped_amulet_name()", equipped_amulet_name_fn)

        print("\n###############\n"
              "Ring color spec\n"
              "###############\n")
        for (x, y) in EQUIPPED_RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in RING_REPOSITORY.name_to_item.keys():
            def fn():
                return eq_reader.is_ring(name)
            time_perf(f"\nis_ring('{name}')", fn)

        def equipped_ring_name_fn():
            return eq_reader.get_equipped_ring_name()
        time_perf("\nget_equipped_ring_name()", equipped_ring_name_fn)

        print("\n###############\n"
              "Magic shield spec\n"
              "###############\n")
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


def main(args):
    if args.check_specs is True:
        check_specs()

    if args.check_slot_empty is not None:
        if check_slot_empty(args.tibia_wid, args.check_slot_empty):
            sys.exit(0)
        else:
            sys.exit(1)

    if args.magic_shield_status:
        check_magic_shield_status(args.tibia_wid)


if __name__ == '__main__':
    main(parser.parse_args())
