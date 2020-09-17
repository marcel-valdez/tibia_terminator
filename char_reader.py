#!/usr/bin/env python2.7

from logger import debug

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


class CharReader():
    def __init__(self, memory_reader):
        self.memory_reader = memory_reader
        self.mana_address = None
        self.hp_address = None
        self.speed_address = None

    def get_stats(self):
        self.memory_reader.open()
        try:
            stats = {'mana': 99999, 'hp': 99999, 'speed': 999}
            if self.mana_address is not None:
                stats['mana'] = self.memory_reader.read_address(
                    self.mana_address, 4)
            if self.hp_address is not None:
                stats['hp'] = self.memory_reader.read_address(
                    self.hp_address, 4)
            if self.speed_address is not None:
                stats['speed'] = self.memory_reader.read_address(
                    self.speed_address, 2)
        finally:
            self.memory_reader.close()
        return stats

    def init_mana_address(self, override_value=None):
        if override_value is not None:
            self.mana_address = override_value
        elif self.mana_address is None:
            print("Searching mana value address...")
            # TODO: This is wrong, we shouldn't need the previous mana
            # memory address, scanmem is able to tell what the memory ranges are.
            mana_range = self.memory_reader.get_range(PREV_MANA_MEMORY_ADDRESS)
            self.mana_address = self.memory_reader.find_value_address(
                mana_range, MANA_OFFSET_AMOUNT, MANA_HARDCODED_OFFSET_VALUE,
                MANA_HARDCODED_OFFSET_VALUE_SIZE)
            if self.mana_address is None:
                raise Exception("Could not find the mana memory address. The "
                                "hardcoded offset is stale.")

        print("Mana memory address is - " + str(self.mana_address) + " (" +
              hex(self.mana_address) + ")")

    def init_hp_address(self, override_value=None):
        if override_value is not None:
            self.hp_address = override_value
        elif self.hp_address is None:
            if self.mana_address is None:
                self.init_mana_address()
                self.hp_address = self.mana_address - 8
                self.mana_address = None
            else:
                self.hp_address = self.mana_address - 8

        print("HP memory address is - " + str(self.hp_address) + " (" +
              hex(self.hp_address) + ")")

    def init_speed_address(self, override_value=None):
        if override_value is not None:
            self.speed_address = override_value
        elif self.speed_address is None:
            # TODO: Implement automated mechanism
            raise Exception("Could not find the speed memory address. The "
                            "hardcoded offset is stale.")

        print("Speed memory address is - " + str(self.speed_address) + " (" +
              hex(self.speed_address) + ")")
