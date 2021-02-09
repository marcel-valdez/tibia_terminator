#!/usr/bin/env python3.8


import argparse
import sys
import time
from window_utils import (ScreenReader, matches_screen_slow)


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


class AmuletName:
    UNKNOWN = 'unknown'
    EMPTY = 'empty'
    # stone skin amuelt
    SSA = 'ssa'
    # sacred tree amulet
    STA = 'sta'
    # bonfire amulet
    BONFIRE = 'bonfire'
    # leviathan's amulet
    LEVIATHAN = 'leviathan'
    # shockwave amulet
    SHOCK = 'shockwave'
    # gill necklace
    GILL = 'gill'
    # glacier amulet
    GLACIER = 'glacier'
    # terra amulet
    TERRA = 'terra'
    # magma amulet
    MAGMA = 'magma'
    # lightning pendant
    LIGHTNING = 'lightning'
    # necklace of the deep
    DEEP = 'deep'
    # prismatic necklace
    PRISM = 'prism'


class RingName:
    UNKNOWN = 'unknown'
    EMPTY = 'empty'
    # might ring
    MIGHT = 'might'

# Playable area set at Y: 696 with 2 cols on left and 2 cols on right

ACTION_BAR_AMULET_COORDS = [
    # upper pixel
    (2, 1),
    # lower pixel
    (2, 3),
    # left pixel
    (1, 2),
    # right pixel
    (3, 2)
]

ACTION_BAR_AMULET_SPEC = {
    AmuletName.SSA: [
        # upper pixel
        "111111",
        # lower pixel
        "111111",
        # left pixel
        "111111",
        # right pixel
        "111111"
    ]
}

AMULET_SPEC = {
    AmuletName.EMPTY: [
        "3d3f42",
        "434648",
        "252626",
        "232424",
    ],
    AmuletName.SSA: [
        # upper pixel
        "000000",
        # lower pixel
        "000000",
        # left pixel
        "000000",
        # right pixel
        "000000"
    ]
}

AMULET_COORDS = [
    # upper pixel
    (1768, 259),
    # lower pixel
    (1768, 272),
    # left pixel
    (1758, 261),
    # right pixel
    (1779, 261)
]

ACTION_BAR_RING_COORDS = [
    # upper pixel
    (2, 1),
    # lower pixel
    (2, 3),
    # left pixel
    (1, 2),
    # right pixel
    (3, 2)
]

ACTION_BAR_RING_SPEC = {
    "might": [
        # upper pixel
        "111111",
        # lower pixel
        "111111",
        # left pixel
        "111111",
        # right pixel
        "111111"
    ]
}

RING_SPEC = {
    RingName.EMPTY: [
        "252625",
        "36393c",
        "2e2e2f",
        "3d4042",
    ],
    RingName.MIGHT: [
        "000000",
        "000000",
        "000000",
        "000000",
    ]
}

RING_COORDS = [
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

    def get_matching_name(self, coords, specs, default_value):
        pixels = self.get_pixels(coords)
        for name in specs:
            if self.pixels_match(specs[name], pixels):
                return name

        return default_value

    def get_action_bar_amulet_name(self):
        return self.get_matching_name(ACTION_BAR_AMULET_COORDS,
                                      ACTION_BAR_AMULET_SPEC,
                                      AmuletName.UNKNOWN)

    def get_equipped_amulet_name(self):
        return self.get_matching_name(AMULET_COORDS,
                                      AMULET_SPEC,
                                      AmuletName.UNKNOWN)

    def get_action_bar_ring_name(self):
        return self.get_matching_name(ACTION_BAR_RING_COORDS,
                                      ACTION_BAR_RING_SPEC,
                                      RingName.UNKNOWN)

    def get_equipped_ring_name(self):
        return self.get_matching_name(RING_COORDS,
                                      RING_SPEC,
                                      RingName.UNKNOWN)

    def is_action_bar_amulet(self, name):
        return self.matches_screen(ACTION_BAR_AMULET_COORDS,
                                   ACTION_BAR_AMULET_SPEC[name])

    def is_action_bar_ring(self, name):
        return self.matches_screen(ACTION_BAR_RING_COORDS,
                                   ACTION_BAR_RING_SPEC[name])

    def is_amulet(self, name):
        return self.matches_screen(AMULET_COORDS, AMULET_SPEC[name])

    def is_amulet_empty(self):
        return self.is_amulet('empty')

    def is_ring(self, name):
        return self.matches_screen(RING_COORDS, RING_SPEC[name])

    def is_ring_empty(self):
        return self.is_ring('empty')

    def get_magic_shield_status(self):
        for name in MAGIC_SHIELD_SPEC:
            if self.matches_screen(MAGIC_SHIELD_COORDS,
                                   MAGIC_SHIELD_SPEC[name]):
                return name
        # There are only 3 possible states: recently cast, off cooldown and
        # on cooldown.
        return MagicShieldStatus.ON_COOLDOWN


class EquipmentReaderSlow():
    def __init__(self, wid):
        self.wid = wid

    def is_amulet(self, name):
        return matches_screen_slow(self.wid, AMULET_COORDS, AMULET_SPEC[name])

    def is_amulet_empty(self):
        return self.is_amulet('empty')

    def is_ring(self, name):
        return matches_screen_slow(self.wid, RING_COORDS, RING_SPEC[name])

    def is_ring_empty(self):
        return self.is_ring('empty')

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
        for (x, y) in ACTION_BAR_AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in ACTION_BAR_AMULET_SPEC:
            def fn():
                return eq_reader.is_action_bar_amulet(name)
            time_perf(f"\nis_action_bar_amulet({name})", fn)

        def action_bar_amulet_name_fn():
            return eq_reader.get_action_bar_amulet_name()

        time_perf("\nget_action_bar_amulet_name", action_bar_amulet_name_fn)

        print("\n###############\n"
              "Action bar ring color spec\n"
              "###############\n")
        for (x, y) in ACTION_BAR_RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in ACTION_BAR_RING_SPEC:
            def fn():
                return eq_reader.is_action_bar_ring(name)
            time_perf(f"\nis_action_bar_ring({name})", fn)

        def action_bar_ring_name_fn():
            return eq_reader.get_action_bar_ring_name()

        time_perf("\nget_action_bar_ring_name", action_bar_ring_name_fn)

        print("\n###############\n"
              "Amulet color spec\n"
              "###############\n")
        for (x, y) in AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in AMULET_SPEC:
            def fn():
                return eq_reader.is_amulet(name)
            time_perf(f"\nis_amulet('{name}')", fn)

        def equipped_amulet_name_fn():
            return eq_reader.get_equipped_amulet_name()
        time_perf("\nget_equipped_amulet_name()", equipped_amulet_name_fn)

        print("\n###############\n"
              "Ring color spec\n"
              "###############\n")
        for (x, y) in RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in RING_SPEC:
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
