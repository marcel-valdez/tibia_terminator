#!/usr/bin/env python2.7


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

# Playable area set at Y: 696 with 2 cols on left and 2 cols on right

AMULET_SPEC = {
    "empty": [
        "3d3f42",
        "434648",
        "252626",
        "232424",
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

RING_SPEC = {
    "empty": [
        "252625",
        "36393c",
        "2e2e2f",
        "3d4042",
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
            if self.matches_screen(MAGIC_SHIELD_COORDS, MAGIC_SHIELD_SPEC[name]):
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


def check_specs():
    eq_reader = EquipmentReader()
    eq_reader.open()
    try:
        print("Amulet color spec")
        for (x, y) in AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        print("Ring color spec")
        for (x, y) in RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        print("Magic shield spec")
        print(eq_reader.get_pixel_color(*MAGIC_SHIELD_COORDS[0]))

        for name in AMULET_SPEC:
            start_ms = time.time() * 1000
            is_amulet_ = eq_reader.is_amulet(name)
            end_ms = time.time() * 1000
            print("is_amulet('" + name + "'): " + str(is_amulet_))
            print("Elapsed time: " + str(end_ms - start_ms) + " ms")

        for name in RING_SPEC:
            start_ms = time.time() * 1000
            is_ring_ = eq_reader.is_ring(name)
            end_ms = time.time() * 1000
            print("is_ring('" + name + "'): " + str(is_ring_))
            print("Elapsed time: " + str(end_ms - start_ms) + " ms")

        start_ms = time.time() * 1000
        magic_shield_status = eq_reader.get_magic_shield_status()
        end_ms = time.time() * 1000
        print("get_magic_shield_status(): " + str(magic_shield_status))
        print("Elapsed time: " + str(end_ms - start_ms) + " ms")
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
