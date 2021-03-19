#!/usr/bin/env python3.8

import argparse
import os
import sys

from tibia_terminator.reader.window_utils import ScreenReader

parser = argparse.ArgumentParser(
    description='Reads equipment status for the Tibia window')
parser.add_argument('--check_specs',
                    help='Checks the color specs for the different menus.',
                    action='store_true')
parser.add_argument('--check_menu',
                    help=('Returns exit code 0 if it is empty, 1 otherwise.\n'
                          'Options: empty, depot_box_open'),
                    type=str,
                    default=None)
parser.add_argument('tibia_wid', help='Window id of the tibia client.')


def get_debug_level():
    level = os.environ.get('DEBUG_LEVEL')
    if level is not None and isinstance(level, str) and level.isdigit():
        return int(level)
    else:
        return -1


def debug(msg, debug_level=0):
    if get_debug_level() >= debug_level:
        print(msg)


class Coords():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Coords) and \
            other.x == self.x and other.y == self.y

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return "(%s,%s)" % (self.x, self.y)


def xy(x, y):
    return Coords(x, y)


MENU_SPECS = {
    "depot_box_open": {
        xy(1752, 501): "8F4F16",
        xy(1882, 503): "404040",
        xy(1767, 503): "444444",
        xy(1772, 503): "909090",
        xy(1777, 503): "909090",
        xy(1782, 503): "313131",
    },
    "empty": {
        xy(1752, 501): "444445",
        xy(1882, 503): "474847",
        xy(1767, 503): "464647",
        xy(1772, 503): "464647",
        xy(1777, 503): "4a4a4b",
        xy(1782, 503): "4c4b4b",
    }
}


class MenuReader(ScreenReader):
    def is_menu(self, tibia_wid, name):
        color_spec = MENU_SPECS[name]
        actual_pixel_colors = map(
            lambda coord: self.get_pixel_color_slow(tibia_wid, coord.x, coord.y
                                                    ), color_spec.keys())

        expected_pixel_colors = color_spec.values()
        for i in range(len(actual_pixel_colors)):
            if actual_pixel_colors[i].lower(
            ) != expected_pixel_colors[i].lower():
                debug(
                    '%s (%s) is not equal to %s' %
                    (actual_pixel_colors[i], i, expected_pixel_colors[i]), 1)
                return False
        return True

    def is_depot_box_open(self, tibia_wid):
        return self.is_menu(tibia_wid, 'depot_box_open')


def check_specs(wid):
    reader = MenuReader()
    print("(x,y): <pixel color> (spec color)")
    for name in MENU_SPECS.keys():
        print(name + " spec.")
        for coords in MENU_SPECS[name].keys():
            print("(%s,%s): %s (%s)" %
                  (coords.x, coords.y,
                   reader.get_pixel_color_slow(
                       wid, coords.x, coords.y), MENU_SPECS[name][coords]))


def check_menu(wid, name):
    reader = MenuReader()
    return reader.is_menu(wid, name)


def main(args):
    if args.check_specs is True:
        check_specs(args.tibia_wid)

    if args.check_menu is not None:
        if check_menu(args.tibia_wid, args.check_menu):
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main(parser.parse_args())
