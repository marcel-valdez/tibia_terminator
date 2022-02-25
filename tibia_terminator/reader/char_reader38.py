#!/usr/bin/env python3.8

import argparse

from typing import Dict

from tibia_terminator.schemas.app_config_schema import AppConfigsSchema
from tibia_terminator.common.lazy_evaluator import future, FutureValue
from tibia_terminator.reader.memory_reader38 import MemoryReader38 as MemoryReader

PREV_MANA_MEMORY_ADDRESS = "41e18e0"  # [I32 I16 ]
# common value
SPEED_HARDCODED_OFFSET_VALUE = ("187c810100000000")
SPEED_HARDCODED_OFFSET_VALUE_SIZE = len(SPEED_HARDCODED_OFFSET_VALUE) / 2
# 88 (0x58)
SPEED_OFFSET_AMOUNT = 88

MANA_HARDCODED_OFFSET_VALUE = ("824994C7F27F00002E0070006E006700"
                               "A0000000000000006100000000000000")
MANA_HARDCODED_OFFSET_VALUE_SIZE = len(MANA_HARDCODED_OFFSET_VALUE) / 2
MANA_OFFSET_AMOUNT = 23040

parser = argparse.ArgumentParser(
    description=('Fetch the character stats in BASH evaluatable format.\n'
                 'The result will be in the format: \n'
                 'HP=###;MANA=###;SPEED=###;SOUL_POINTS=###'))
parser.add_argument('--mana_address',
                    help='Memory address for the mana value.',
                    type=str,
                    default=None)
parser.add_argument(
    '--hp_address',
    help=('Memory address for the HP value. This value '
          'can be calculated based on the mana memory address.'),
    type=str,
    default=None)
parser.add_argument('--speed_address',
                    help='Memory address for the speed value.',
                    type=str,
                    default=None)
parser.add_argument('--soul_points_address',
                    help='Memory address for the speed value.',
                    type=str,
                    default=None)
parser.add_argument('--magic_shield_address',
                    help='Memory address for magic shield level value.',
                    type=str,
                    default=None)
parser.add_argument('--max_hp_address',
                    help='Memory address for magic shield level value.',
                    type=str,
                    default=None)
parser.add_argument('--max_mana_address',
                    help='Memory address for magic shield level value.',
                    type=str,
                    default=None)
parser.add_argument('--pid', help='The PID of Tibia', type=int, default=None)
parser.add_argument('--app_config_path',
                    help='Path to memory addresses',
                    type=str,
                    required=True)
parser.add_argument('--verbose',
                    help='Show verbose output.',
                    action='store_true',
                    default=False)


class CharReader38():
    def __init__(self, memory_reader, verbose=True):
        self.memory_reader = memory_reader
        self.mana_address = None
        self.hp_address = None
        self.speed_address = None
        self.magic_shield_address = None
        self.soul_points_address = None
        self.max_hp_address = None
        self.max_mana_address = None
        self.verbose = verbose

    def __fetch_stats(self):
        stats = {
            'mana': 99999,
            'hp': 99999,
            'speed': 999,
            'soul_points': 0,
            'magic_shield': 9999
        }
        self.memory_reader.open()
        try:
            if self.mana_address is not None:
                stats['mana'] = self.memory_reader.read_address(
                    self.mana_address, 4)
            if self.hp_address is not None:
                stats['hp'] = self.memory_reader.read_address(
                    self.hp_address, 4)
            if self.magic_shield_address is not None:
                stats['magic_shield'] = self.memory_reader.read_address(
                    self.magic_shield_address, 2)
            if self.speed_address is not None:
                stats['speed'] = self.memory_reader.read_address(
                    self.speed_address, 2)
            if self.soul_points_address is not None:
                stats['soul_points'] = self.memory_reader.read_address(
                    self.soul_points_address, 4)
        finally:
            self.memory_reader.close()
        return stats

    def get_stats(self) -> FutureValue[Dict[str, int]]:
        return future(self.__fetch_stats)

    def get_max_hp(self):
        if self.max_hp_address is None:
            return 99999
        self.memory_reader.open()
        try:
            return self.memory_reader.read_address(self.max_hp_address, 4)
        finally:
            self.memory_reader.close()

    def get_max_mana(self):
        if self.max_mana_address is None:
            return 99999
        self.memory_reader.open()
        try:
            return self.memory_reader.read_address(self.max_mana_address, 4)
        finally:
            self.memory_reader.close()

    def init_mana_address(self, override_value=None):
        if override_value is not None:
            self.mana_address = override_value
        elif self.mana_address is None:
            if self.verbose:
                print("Searching mana value address...")
            # TODO: This is wrong, we shouldn't need the previous mana
            # memory address, scanmem is able to tell what the memory ranges
            # are.
            mana_range = self.memory_reader.get_range(PREV_MANA_MEMORY_ADDRESS)
            self.mana_address = self.memory_reader.find_value_address(
                mana_range, MANA_OFFSET_AMOUNT, MANA_HARDCODED_OFFSET_VALUE,
                MANA_HARDCODED_OFFSET_VALUE_SIZE)
            if self.mana_address is None:
                raise Exception("Could not find the mana memory address. The "
                                "hardcoded offset is stale.")

        if self.verbose:
            print("Mana memory address is - {} ({})".format(
                str(self.mana_address), hex(self.mana_address)))

    def init_max_mana_address(self, override_value=None):
        if override_value is not None:
            self.max_mana_address = override_value
        elif self.max_mana_address is None:
            if self.mana_address is not None:
                self.max_mana_address = self.mana_address + 4
            else:
                # TODO: Implement automated mechanism
                raise Exception("Could not find the max mana memory address. "
                                "The hardcoded offset is stale.")

        if self.verbose:
            print("Max mana address is - {} ({})".format(
                str(self.max_mana_address), hex(self.max_mana_address)))

    def init_hp_address(self, override_value=None):
        if override_value is not None:
            self.hp_address = override_value
        elif self.hp_address is None and self.mana_address is not None:
            self.hp_address = self.mana_address - 8
        else:
            raise Exception("No mana address value provided.")

        if self.verbose:
            print("HP memory address is - {} ({})".format(
                str(self.hp_address), hex(self.hp_address)))

    def init_max_hp_address(self, override_value=None):
        if override_value is not None:
            self.max_hp_address = override_value
        elif self.max_hp_address is None:
            if self.mana_address is not None:
                self.max_hp_address = self.mana_address - 4
            else:
                # TODO: Implement automated mechanism
                raise Exception("Could not find the max HP memory address. "
                                "The hardcoded offset is stale.")

        if self.verbose:
            print("Max HP address is - {} ({})".format(
                str(self.max_hp_address), hex(self.max_hp_address)))

    def init_speed_address(self, override_value=None):
        if override_value is not None:
            self.speed_address = override_value
        elif self.speed_address is None:
            # TODO: Implement automated mechanism
            raise Exception("Could not find the speed memory address. The "
                            "hardcoded offset is stale.")

        if self.verbose:
            print("Speed memory address is - {} ({})".format(
                str(self.speed_address), hex(self.speed_address)))

    def init_magic_shield_address(self, override_value=None):
        if override_value is not None:
            self.magic_shield_address = override_value
        elif (self.magic_shield_address is None
              and self.speed_address is not None):
            self.magic_shield_address = self.speed_address + 204
        else:
            # TODO: Implement automated mechanism
            raise Exception("No magic shield memory address provided.")

        if self.verbose:
            print("Magic shield memory address is - {} ({})".format(
                str(self.magic_shield_address),
                hex(self.magic_shield_address)))

    def init_soul_points_address(self, override_value=None):
        if override_value is not None:
            self.soul_points_address = override_value
        elif self.soul_points_address is None:
            # TODO: Implement automated mechanism
            raise Exception("Could not find the soul points memory address. "
                            "The hardcoded offset is stale.")

        if self.verbose:
            print("Soul points memory address is - {} ({})".format(
                str(self.soul_points_address), hex(self.soul_points_address)))


def main(pid,
         mana_address=None,
         hp_address=None,
         magic_shield_address=None,
         speed_address=None,
         soul_points_address=None,
         max_hp_address=None,
         max_mana_address=None,
         verbose=False):
    memory_reader = MemoryReader(pid)
    reader = CharReader38(memory_reader, verbose=verbose)
    if mana_address is not None:
        reader.init_mana_address(int(mana_address, 16))
        reader.init_max_mana_address()
        reader.init_hp_address()
        reader.init_max_hp_address()
    if hp_address is not None:
        reader.init_hp_address(int(hp_address, 16))
    if speed_address is not None:
        reader.init_speed_address(int(speed_address, 16))
        reader.init_magic_shield_address()
    if soul_points_address is not None:
        reader.init_soul_points_address(int(soul_points_address, 16))
    if magic_shield_address is not None:
        reader.init_magic_shield_address(int(magic_shield_address, 16))
    if max_hp_address is not None:
        reader.init_max_hp_address(int(max_hp_address, 16))
    if max_mana_address is not None:
        reader.init_max_mana_address(int(max_mana_address, 16))

    stats = reader.get_stats().get()
    print(f"HP={stats['hp']};MANA={stats['mana']};SPEED={stats['speed']};"
          f"SOUL_POINTS={stats['soul_points']};"
          f"MAGIC_SHIELD={stats['magic_shield']};"
          f"MAX_MANA={reader.get_max_mana()};MAX_HP={reader.get_max_hp()}")


if __name__ == "__main__":
    args = parser.parse_args()
    app_config_schema = AppConfigsSchema()
    configs = app_config_schema.loadf(args.app_config_path)
    pid = args.pid or configs.default_pid
    config = configs[pid]
    main(pid, args.mana_address
         or config.mana_memory_address, args.hp_address
         or config.hp_memory_address, args.magic_shield_address
         or config.magic_shield_memory_address, args.speed_address
         or config.speed_memory_address, args.soul_points_address
         or config.soul_points_memory_address, args.max_hp_address
         or config.max_hp_address, args.max_mana_address
         or config.max_mana_address, args.verbose)
