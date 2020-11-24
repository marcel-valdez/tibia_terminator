#!/usr/bin/env python2.7

import argparse
import time

from multiprocessing import Pool

from window_utils import get_tibia_wid
from client_interface import ClientInterface
from memory_reader import MemoryReader
from char_keeper import CharKeeper
from char_reader import CharReader
from char_status import CharStatus
from equipment_reader import EquipmentReader
from char_config import CHAR_CONFIG, HOTKEYS_CONFIG
from app_config import MEM_CONFIG
from logger import set_debug_level

parser = argparse.ArgumentParser(
    description='Tibia terminator CLI parameters.')
parser.add_argument('pid', help='The PID of Tibia')
parser.add_argument('--no_mana',
                    help='Do not automatically recover mana.',
                    action='store_true')
parser.add_argument('--no_hp',
                    help='Do not automatically recover hp.',
                    action='store_true')
parser.add_argument('--no_magic_shield',
                    help='Do not automatically cast magic shield.',
                    action='store_true')
parser.add_argument('--no_speed',
                    help='Do not monitor speed.',
                    action='store_true')
parser.add_argument('--only_monitor',
                    help='Only print stat changes, no action taken',
                    action='store_true')
parser.add_argument('--debug_level',
                    help=('Set the debug level for debug log messages, '
                          'higher values result in more verbose output.'),
                    type=int,
                    default=-1)

PPOOL = None


class TibiaTerminator:
    def __init__(self,
                 tibia_wid,
                 char_keeper,
                 char_reader,
                 equipment_reader,
                 mem_config,
                 enable_mana=True,
                 enable_hp=True,
                 enable_magic_shield=True,
                 enable_speed=True,
                 only_monitor=False):
        self.tibia_wid = tibia_wid
        self.char_keeper = char_keeper
        self.char_reader = char_reader
        self.mem_config = mem_config
        self.equipment_reader = equipment_reader
        self.enable_speed = enable_speed
        self.enable_mana = enable_mana
        self.enable_hp = enable_hp
        self.enable_magic_shield = enable_magic_shield
        self.only_monitor = only_monitor

    def monitor_char(self):
        # TODO: Rather than hardcoding these values, implement the init_*
        # methods in char_reader to automatically find these values, the
        # only challenge is that they're likely to change with every Tibia
        # update.
        # We should consider using OCR instead of reading the mana address.
        mana_address = int(self.mem_config['mana_memory_address'], 16)
        hp_address = mana_address - 8
        magic_shield_address = mana_address + 8
        speed_address = int(self.mem_config['speed_memory_address'], 16)
        if self.enable_mana:
            self.char_reader.init_mana_address(mana_address)
        if self.enable_hp:
            self.char_reader.init_hp_address(hp_address)
        if self.enable_speed:
            self.char_reader.init_speed_address(speed_address)
        if self.enable_magic_shield:
            self.char_reader.init_magic_shield_address(magic_shield_address)

        prev_stats = {'mana': -1, 'hp': -1, 'speed': -1}
        self.equipment_reader.open()
        try:
            while True:
                stats = self.char_reader.get_stats()
                # 20-30 ms
                is_amulet_slot_empty = self.equipment_reader.is_amulet_empty()
                # 20-30 ms
                is_ring_slot_empty = self.equipment_reader.is_ring_empty()
                magic_shield_status = \
                    self.equipment_reader.get_magic_shield_status()
                self.handle_stats(
                    stats,
                    prev_stats,
                    is_amulet_slot_empty,
                    is_ring_slot_empty,
                    magic_shield_status)
                # Sleep 60 ms
                time.sleep(0.06)
        finally:
            self.equipment_reader.close()

    def handle_stats(self, stats, prev_stats,
                     is_amulet_slot_empty,
                     is_ring_slot_empty,
                     magic_shield_status):
        mana = stats['mana']
        hp = stats['hp']
        speed = stats['speed']
        magic_shield_level = stats['magic_shield']
        char_status = CharStatus(
            hp, speed, mana, magic_shield_level, is_amulet_slot_empty,
            is_ring_slot_empty, magic_shield_status)
        # Note that we have to handle the mana change always, even if
        # it hasn't actually changed, because a command to heal or drink mana
        # or haste could be ignored if the character is exhausted, therefore
        # we have to spam the action until the effect takes place.
        if self.enable_mana:
            self.char_keeper.handle_mana_change(char_status)

        prev_mana = prev_stats['mana']
        if mana != prev_mana:
            prev_stats['mana'] = mana
            print_async("Mana: {}".format(str(mana)))

        if self.enable_hp:
            self.char_keeper.handle_hp_change(char_status)

        prev_hp = prev_stats['hp']
        if hp != prev_hp:
            prev_stats['hp'] = hp
            print_async("HP: {}".format(str(hp)))

        if self.enable_speed:
            self.char_keeper.handle_speed_change(char_status)

        prev_speed = prev_stats['speed']
        if speed != prev_speed:
            prev_stats['speed'] = speed
            print_async("Speed: {}".format(str(speed)))

        self.char_keeper.handle_equipment(char_status)


def fprint(fargs):
    if PPOOL is None:
        print(fargs)
    else:
        PPOOL.apply_async(fprint, tuple(fargs))


def print_async(*pargs):
    if PPOOL is None:
        print(pargs)
    else:
        PPOOL.apply_async(fprint, tuple(pargs))


def main(pid, enable_mana, enable_hp, enable_magic_shield, enable_speed,
         only_monitor):
    if pid is None or pid == "":
        raise Exception("PID is required, you may use psgrep -a -l bin/Tibia "
                        "to find the process id")
    mem_config = MEM_CONFIG[str(pid)]
    tibia_wid = get_tibia_wid(pid)
    client = ClientInterface(tibia_wid,
                             HOTKEYS_CONFIG,
                             only_monitor=only_monitor)
    char_keeper = CharKeeper(client, CHAR_CONFIG)
    char_reader = CharReader(MemoryReader(pid, print_async))
    eq_reader = EquipmentReader()
    tibia_terminator = TibiaTerminator(tibia_wid,
                                       char_keeper,
                                       char_reader,
                                       eq_reader,
                                       mem_config,
                                       enable_mana=enable_mana,
                                       enable_hp=enable_hp,
                                       enable_magic_shield=enable_magic_shield,
                                       enable_speed=enable_speed,
                                       only_monitor=only_monitor)
    tibia_terminator.monitor_char()


if __name__ == "__main__":
    args = parser.parse_args()
    PPOOL = Pool(processes=3)
    set_debug_level(args.debug_level)
    main(args.pid,
         enable_mana=not args.no_mana,
         enable_hp=not args.no_hp,
         enable_magic_shield=not args.no_magic_shield,
         enable_speed=not args.no_speed,
         only_monitor=args.only_monitor)
