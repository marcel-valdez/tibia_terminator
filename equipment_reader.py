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
    EMPTY = 'empty.amulet'
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
    EMPTY = 'empty.ring'
    # might ring
    MIGHT = 'might'


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

EMERGENCY_ACTION_BAR_AMULET_SPEC = {
    AmuletName.SSA: [
        # upper pixel
        "b9935f",
        # lower pixel
        "3c3c3c",
        # left pixel
        "444444",
        # right pixel
        "454545"
    ],
    AmuletName.STA: [
        "4d170",
        "1ad552",
        "d421d",
        "93215"
    ],
    AmuletName.LEVIATHAN: [
        "b4e2f0",
        "032c1",
        "444444",
        "454545"
    ],
    AmuletName.SHOCK: [
        [
            "61719",
            "404040",
            "89d27",
            "54312"
        ],
        [
            "59515",
            "404040",
            "6f519",
            "5d616"
        ],
        [
            "68a1f",
            "404040",
            "7da24",
            "5e719"
        ],
        [
            "57311",
            "404040",
            "7b81c",
            "5c514"
        ]
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
        "252626",
        # lower pixel
        "b8b8b8",
        # left pixel
        "252626",
        # right pixel
        "232424"
    ],
    AmuletName.STA: [
        "252626",
        "1b42c",
        "252626",
        "a3f19"
    ],
    AmuletName.LEVIATHAN: [
        "252626",
        "262627",
        "252626",
        "232424"
    ],
    AmuletName.SHOCK: [
        [
            "252626",
            "60719",
            "91d28",
            "232424"
        ],
        [
            "252626",
            "6891a",
            "7e61b",
            "232424"
        ],
        [
            "252626",
            "5a517",
            "87b26",
            "232424"
        ],
        [
            "252626",
            "60719",
            "91d28",
            "232424"
        ]
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

EMERGENCY_ACTION_BAR_RING_SPEC = {
    "might": [
        # upper pixel
        "9b8132",
        # lower pixel
        "d1af44",
        # left pixel
        "faed75",
        # right pixel
        "d5b246"
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
        "252625",
        "272728",
        "d1ae43",
        "927b34",
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

    def matches_screen(self, coords, specs):
        if type(specs[0]) == list:
            for animation_spec in specs:
                if ScreenReader.matches_screen(self, coords, animation_spec):
                    return True
            return False
        else:
            return ScreenReader.matches_screen(self, coords, specs)

    def pixels_match(self, specs, pixels):
        if type(specs[0]) == list:
            for animation_spec in specs:
                if ScreenReader.pixels_match(self, animation_spec, pixels):
                    return True
            return False
        else:
            return ScreenReader.pixels_match(self, specs, pixels)

    def get_matching_name(self, coords, specs, default_value):
        pixels = self.get_pixels(coords)
        for name in specs:
            if self.pixels_match(specs[name], pixels):
                return name
        return default_value

    def get_emergency_action_bar_amulet_name(self):
        return self.get_matching_name(EMERGENCY_ACTION_BAR_AMULET_COORDS,
                                      EMERGENCY_ACTION_BAR_AMULET_SPEC,
                                      AmuletName.UNKNOWN)

    def get_equipped_amulet_name(self):
        return self.get_matching_name(AMULET_COORDS,
                                      AMULET_SPEC,
                                      AmuletName.UNKNOWN)

    def get_emergency_action_bar_ring_name(self):
        return self.get_matching_name(EMERGENCY_ACTION_BAR_RING_COORDS,
                                      EMERGENCY_ACTION_BAR_RING_SPEC,
                                      RingName.UNKNOWN)

    def get_equipped_ring_name(self):
        return self.get_matching_name(RING_COORDS,
                                      RING_SPEC,
                                      RingName.UNKNOWN)

    def is_emergency_action_bar_amulet(self, name):
        return self.matches_screen(EMERGENCY_ACTION_BAR_AMULET_COORDS,
                                   EMERGENCY_ACTION_BAR_AMULET_SPEC[name])

    def is_emergency_action_bar_ring(self, name):
        return self.matches_screen(EMERGENCY_ACTION_BAR_RING_COORDS,
                                   EMERGENCY_ACTION_BAR_RING_SPEC[name])

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
        for (x, y) in EMERGENCY_ACTION_BAR_AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in EMERGENCY_ACTION_BAR_AMULET_SPEC:
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

        for name in EMERGENCY_ACTION_BAR_RING_SPEC:
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
