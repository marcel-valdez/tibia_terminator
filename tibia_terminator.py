#!/usr/bin/env python2.7

import argparse
import time
import subprocess

from multiprocessing import Pool

from client_interface import ClientInterface
from memory_reader import MemoryReader
from char_keeper import CharKeeper
from char_config import CHAR_CONFIG, HOTKEYS_CONFIG


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('pid', help='The PID of Tibia')
parser.add_argument('--no_mana',
                    help='Do not automatically recover mana.',
                    action='store_true')
parser.add_argument('--no_hp',
                    help='Do not automatically recover hp.',
                    action='store_true')
parser.add_argument('--no_speed',
                    help='Do not monitor speed.',
                    action='store_true')
parser.add_argument('--only_monitor',
                    help='Only print stat changes, no action taken',
                    action='store_true')

PPOOL = None

# This value is obtained by running scanmem on the tibia process
MANA_MEMORY_ADDRESS = "567b7a0"  # [I32 I16 ]
HP_MEMORY_ADDRESS = "567b798"   # [I32 I16 ]
SPEED_MEMORY_ADDRESS = "b051e00"  #


# common value
SPEED_HARDCODED_OFFSET_VALUE = (
    "187c810100000000"
)
SPEED_HARDCODED_OFFSET_VALUE_SIZE = len(SPEED_HARDCODED_OFFSET_VALUE) / 2
# 88 (0x58)
SPEED_OFFSET_AMOUNT = 88

MANA_HARDCODED_OFFSET_VALUE = (
    "824994C7F27F00002E0070006E006700"
    "A0000000000000006100000000000000"
)
MANA_HARDCODED_OFFSET_VALUE_SIZE = len(MANA_HARDCODED_OFFSET_VALUE) / 2
MANA_OFFSET_AMOUNT = 23040


class TibiaTerminator:

    def __init__(self,
                 proc_id,
                 tibia_wid,
                 char_keeper,
                 memory_reader,
                 enable_mana=True,
                 enable_hp=True,
                 enable_speed=True,
                 only_monitor=False):
        # proc_id should be int
        self.__proc_id = proc_id
        self.tibia_wid = tibia_wid
        self.memory_reader = memory_reader
        self.enable_speed = enable_speed
        self.enable_mana = enable_mana
        self.enable_hp = enable_hp
        self.only_monitor = only_monitor
        self.drinking_mana = False

    def monitor_char(self):
        mana_address = None
        hp_address = None
        if self.enable_mana:
            mana_address = int(MANA_MEMORY_ADDRESS, 16)
#            print_async("Searching mana value address...")
#            mana_range = self.get_range(MANA_MEMORY_ADDRESS)
#            mana_address = self.memory_reader.find_value_address(
#                mana_range,
#                MANA_OFFSET_AMOUNT,
#                MANA_HARDCODED_OFFSET_VALUE,
#                MANA_HARDCODED_OFFSET_VALUE_SIZE
#            )
            if mana_address is None:
                raise Exception("Could not find the mana memory address. The "
                                "hardcoded offset is stale.")

            hp_address = mana_address - 8
            print_async(
                "Mana memory address is - " + str(mana_address)
                + " (" + hex(mana_address) + ")"
            )
            print_async(
                "HP memory address is - " + str(hp_address)
                + " (" + hex(hp_address) + ")"
            )

        if self.enable_speed:
            speed_address = int(SPEED_MEMORY_ADDRESS, 16)
#            print_async("Searching speed value address...")
#            speed_range = self.get_range(SPEED_MEMORY_ADDRESS)
#            speed_address = self.memory_reader.find_value_address(
#                speed_range,
#                SPEED_OFFSET_AMOUNT,
#                SPEED_HARDCODED_OFFSET_VALUE,
#                SPEED_HARDCODED_OFFSET_VALUE_SIZE
#            )
            if speed_address is None:
                raise Exception("Could not find the speed memory address. The "
                                "hardcoded offset is stale.")
            print_async(
                "Speed memory address is - " + str(speed_address)
                + " (" + hex(speed_address) + ")"
            )

        prev_stats = {
            'mana': -1,
            'hp': -1,
            'speed': -1
        }
        while True:
            stats = self.get_stats(hp_address, mana_address, speed_address)
            self.handle_stats(stats, prev_stats)
            time.sleep(0.1)

    def get_stats(self, hp_address, mana_address, speed_address):
        stats = {
            'mana': 99999,
            'hp': 99999,
            'speed': 999
        }
        if self.enable_hp:
            stats['hp'] = self.memory_reader.read_address(hp_address, 4)
        if self.enable_mana:
            stats['mana'] = self.memory_reader.read_address(mana_address, 4)
        if self.enable_speed:
            stats['speed'] = self.memory_reader.read_address(speed_address, 2)

        return stats

    def handle_stats(self, stats, prev_stats):
        mana = stats['mana']
        hp = stats['hp']
        speed = stats['speed']
        if self.enable_mana:
            self.char_keeper.handle_mana_change(hp, speed, mana)
            prev_mana = prev_stats['mana']
            if mana != prev_mana:
                prev_stats['mana'] = mana
                print_async("Mana: {}".format(str(mana)))

        if self.enable_hp:
            self.char_keeper.handle_hp_change(hp, speed, mana)
            prev_hp = prev_stats['hp']
            if hp != prev_hp:
                prev_stats['hp'] = hp
                print_async("HP: {}".format(str(hp)))

        if self.enable_speed:
            self.char_keeper.handle_speed_change(hp, speed, mana)
            prev_speed = prev_stats['speed']
            if speed != prev_speed:
                prev_stats['speed'] = speed
                print_async("Speed: {}".format(str(speed)))


def get_tibia_wid():
    wid = subprocess.check_output([
        "/usr/bin/xdotool", "search", "--class", "Tibia"
    ], stderr=subprocess.STDOUT)
    print_async('tibia wid:' + str(wid))
    return wid


def fprint(fargs):
    print(fargs)


def print_async(*pargs):
    if PPOOL is None:
        print(pargs)
    else:
        PPOOL.apply_async(fprint, tuple(pargs))


def main(pid, no_mana, no_hp, no_speed, only_monitor):
    if pid is None or pid == "":
        raise Exception("PID is required, you may use psgrep -a -l bin/Tibia "
                        "to find the process id")
    tibia_wid = get_tibia_wid()
    client = ClientInterface(tibia_wid, HOTKEYS_CONFIG)
    char_keeper = CharKeeper(client, CHAR_CONFIG, print_async)
    memory_reader = MemoryReader(pid, print_async)
    tibia_terminator = TibiaTerminator(pid,
                                       tibia_wid,
                                       char_keeper,
                                       memory_reader,
                                       enable_mana=not no_mana,
                                       enable_hp=not no_hp,
                                       enable_speed=not no_speed,
                                       only_monitor=only_monitor)
    tibia_terminator.monitor_char()


if __name__ == "__main__":
    args = parser.parse_args()
    PPOOL = Pool(processes=3)
    main(args.pid, args.no_mana, args.no_hp, args.no_speed, args.only_monitor)
