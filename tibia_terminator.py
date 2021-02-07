#!/usr/bin/env python3.8

import argparse
import time
import curses
import sys

from multiprocessing import Pool

from window_utils import get_tibia_wid
from client_interface import ClientInterface
from memory_reader38 import MemoryReader38 as MemoryReader
from char_keeper import CharKeeper
from char_reader38 import CharReader38 as CharReader
from char_status import CharStatus
from equipment_reader import EquipmentReader
from char_config import CHAR_CONFIGS, HOTKEYS_CONFIG
from app_config import MEM_CONFIG
from logger import set_debug_level
from looter import Looter

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
SPACE_KEYCODE = 263
ENTER_KEYCODE = 10
ESCAPE_KEY = 27

TITLE_ROW = 0
MAIN_OPTIONS_ROW = TITLE_ROW + 1
ERRORS_ROW = MAIN_OPTIONS_ROW + 1

MANA_ROW = ERRORS_ROW + 1
HP_ROW = MANA_ROW + 1
SPEED_ROW = HP_ROW + 1
MAGIC_SHIELD_ROW = SPEED_ROW + 1

CONFIG_SELECTION_ROW = ERRORS_ROW + 2
CONFIG_SELECTION_TITLE = "Type the number of the char config to load: "

class AppStates:
    PAUSED = "__PAUSED__"
    RUNNING = "__RUNNING__"
    CONFIG_SELECTION = "__CONFIG_SELECTION__"
    EXIT = "__EXIT__"

PAUSE_KEYCODE = SPACE_KEYCODE
RESUME_KEYCODE = SPACE_KEYCODE
CONFIG_SELECTION_KEYCODE = ENTER_KEYCODE
EXIT_KEYCODE = ESCAPE_KEY



class TibiaTerminator:
    def __init__(self,
                 tibia_wid,
                 char_keeper,
                 char_reader,
                 equipment_reader,
                 mem_config,
                 char_configs,
                 cliwin,
                 looter,
                 enable_mana=True,
                 enable_hp=True,
                 enable_magic_shield=True,
                 enable_speed=True,
                 only_monitor=False):
        self.tibia_wid = tibia_wid
        self.char_keeper = char_keeper
        self.char_reader = char_reader
        self.mem_config = mem_config
        self.char_configs = char_configs
        self.cliwin = cliwin
        self.equipment_reader = equipment_reader
        self.looter = looter
        self.enable_speed = enable_speed
        self.enable_mana = enable_mana
        self.enable_hp = enable_hp
        self.enable_magic_shield = enable_magic_shield
        self.only_monitor = only_monitor
        self.initial_pause = True
        self.app_state = None
        self.selected_config_name = char_configs[0]["name"]

    def monitor_char(self):
        # TODO: Rather than hardcoding these values, implement the init_*
        # methods in char_reader to automatically find these values, the
        # only challenge is that they're likely to change with every Tibia
        # update.
        # We should consider using OCR instead of reading the mana address.

        if self.enable_mana:
            mana_address = int(self.mem_config['mana_memory_address'], 16)
        else:
            mana_address = None

        if self.enable_hp and self.mem_config['hp_memory_address'] is not None:
            hp_address = int(self.mem_config['hp_memory_address'], 16)
        else:
            hp_address = None

        if self.enable_speed:
            speed_address = int(self.mem_config['speed_memory_address'], 16)
        else:
            speed_address = None

        if self.mem_config['magic_shield_memory_address'] is not None:
            magic_shield_address = int(
                self.mem_config['magic_shield_memory_address'], 16)
        else:
            magic_shield_address = None

        if self.enable_mana:
            self.char_reader.init_mana_address(mana_address)
            self.char_reader.init_max_mana_address()
        if self.enable_hp:
            self.char_reader.init_hp_address(hp_address)
            self.char_reader.init_max_hp_address()
        if self.enable_speed:
            self.char_reader.init_speed_address(speed_address)
        if self.enable_magic_shield:
            self.char_reader.init_magic_shield_address(magic_shield_address)

        self.prev_stats = {'mana': -1, 'hp': -1, 'speed': -1, 'magic_shield': -1}
        self.equipment_reader.open()
        self.cliwin.nodelay(True)
        self.cliwin.idlok(True)
        self.cliwin.leaveok(True)
        self.cliwin.refresh()

        self.app_state = AppStates.PAUSED
        self.winprint("[Space]: Resume, [Esc]: Exit, [Enter]: Config selection.", MAIN_OPTIONS_ROW)

        try:
            while True:
                title = "Tibia Terminator. WID: " + str(self.tibia_wid) + " Active config: " + self.selected_config_name
                self.winprint(title, TITLE_ROW)
                start = time.time() * 1000
                keycode = self.cliwin.getch()
                self.enter_next_app_state(keycode)
                if self.app_state == AppStates.EXIT:
                    self.handle_exit_state()
                elif self.app_state == AppStates.PAUSED:
                    self.handle_paused_state()
                elif self.app_state == AppStates.RUNNING:
                    self.handle_running_state()
                elif self.app_state == AppStates.CONFIG_SELECTION:
                    self.handle_config_selection_state()

                end = time.time() * 1000
                elapsed = end - start
                # Loop every 100 ms
                if elapsed < 100:
                    time.sleep((100 - elapsed) / 1000)
        finally:
            self.looter.unhook_hotkey()
            self.equipment_reader.close()

    def handle_exit_state(self):
        """Exits the program based on user input."""
        sys.exit(0)


    def enter_next_app_state(self, keycode):
        next_state = self.app_state
        if keycode == EXIT_KEYCODE:
            next_state = AppStates.EXIT

        if self.app_state == AppStates.RUNNING:
            if keycode == PAUSE_KEYCODE:
                next_state = AppStates.PAUSED

        if self.app_state == AppStates.PAUSED:
            if keycode == RESUME_KEYCODE:
                next_state = AppStates.RUNNING

        if self.app_state == AppStates.CONFIG_SELECTION:
            if keycode == CONFIG_SELECTION_KEYCODE:
                next_state = AppStates.PAUSED
        elif keycode == CONFIG_SELECTION_KEYCODE:
            next_state = AppStates.CONFIG_SELECTION

        if self.app_state != next_state:
            if self.app_state == AppStates.RUNNING:
                self.exit_running_state()
            if self.app_state == AppStates.PAUSED:
                self.exit_paused_state()
            if self.app_state == AppStates.CONFIG_SELECTION:
                self.exit_config_selection_state()

            if next_state == AppStates.RUNNING:
                self.enter_running_state()
            if next_state == AppStates.PAUSED:
                self.enter_paused_state()
            if next_state == AppStates.CONFIG_SELECTION:
                self.enter_config_selection_state()

        self.app_state = next_state

    def enter_running_state(self):
        self.looter.hook_hotkey()
        self.winprint("[Space]: Pause, [Esc]: Exit, [Enter]: Config selection.", MAIN_OPTIONS_ROW)

    def handle_running_state(self):
        stats = self.char_reader.get_stats()
        # 20-30 ms
        is_amulet_slot_empty = self.equipment_reader.is_amulet_empty()
        # 20-30 ms
        is_ring_slot_empty = self.equipment_reader.is_ring_empty()
        magic_shield_status = \
            self.equipment_reader.get_magic_shield_status()
        self.handle_stats(
            stats,
            self.prev_stats,
            is_amulet_slot_empty,
            is_ring_slot_empty,
            magic_shield_status)

    def exit_running_state(self):
        pass

    def enter_paused_state(self):
        self.looter.unhook_hotkey()
        self.winprint("[Space]: Resume, [Esc]: Exit, [Enter]: Config selection.", MAIN_OPTIONS_ROW)

    def exit_paused_state(self):
        pass

    def handle_paused_state(self):
        pass

    def enter_config_selection_state(self):
        self.winprint("[Esc]: Exit, [Enter]: Back to paused state.", MAIN_OPTIONS_ROW)
        self.winprint(CONFIG_SELECTION_TITLE, CONFIG_SELECTION_ROW)
        self.cliwin.clrtobot()
        self.cliwin.nodelay(False)

    def exit_config_selection_state(self):
        self.cliwin.clear()
        self.cliwin.refresh()
        self.cliwin.nodelay(True)

    def handle_config_selection_state(self):
        i = 0
        total_char_configs = len(self.char_configs)
        for char_config in self.char_configs:
            row = CONFIG_SELECTION_ROW + i + 1
            self.cliwin.move(row, 0)
            self.cliwin.clrtoeol()
            self.cliwin.insstr(str(i) + ': ' + char_config["name"])
            i += 1

        number_str = ''
        getting_number = True
        input_col = len(CONFIG_SELECTION_TITLE)
        col = input_col
        while getting_number:
            keycode = self.cliwin.getch(CONFIG_SELECTION_ROW, col)
            if keycode >= 48 and keycode <= 57:
                number_str += str(keycode - 48)
                self.cliwin.insstr(str(keycode - 48))
                col += 1
            elif keycode == ENTER_KEYCODE:
                if number_str == '':
                    self.exit_config_selection_state()
                    self.enter_paused_state()
                    self.app_state = AppStates.PAUSED
                    break
                elif not number_str.isdigit():
                    self.winprint("Only numbers allowed.", ERRORS_ROW)
                    col = input_col
                    self.cliwin.move(CONFIG_SELECTION_ROW, col)
                    self.cliwin.clrtoeol()
                    number_str = ''
                else:
                    selection = int(number_str)
                    if selection >= total_char_configs:
                        self.winprint("Selection index {} is invalid.".format(number_str), ERRORS_ROW)
                        col = input_col
                        self.cliwin.move(CONFIG_SELECTION_ROW, input_col)
                        self.cliwin.clrtoeol()
                        number_str = ''
                    else:
                        self.selected_config_name = self.char_configs[selection]["name"]
                        self.char_keeper.change_char_config(selection)
                        self.exit_config_selection_state()
                        self.enter_paused_state()
                        self.app_state = AppStates.PAUSED
                        break
            elif keycode == EXIT_KEYCODE:
                self.handle_exit_state()
            elif keycode == curses.KEY_BACKSPACE:
                if len(number_str) > 0:
                    self.cliwin.delch(CONFIG_SELECTION_ROW, col - 1)
                    number_str = number_str[:len(number_str) - 1]
                    col -= 1


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
            self.winprint("Mana: {}".format(str(mana)), MANA_ROW)

        if self.enable_hp:
            self.char_keeper.handle_hp_change(char_status)

        prev_hp = prev_stats['hp']
        if hp != prev_hp:
            prev_stats['hp'] = hp
            self.winprint("HP: {}".format(str(hp)), HP_ROW)

        if self.enable_speed:
            self.char_keeper.handle_speed_change(char_status)

        prev_speed = prev_stats['speed']
        if speed != prev_speed:
            prev_stats['speed'] = speed
            self.winprint("Speed: {}".format(str(speed)), SPEED_ROW)

        prev_magic_shield_level = prev_stats['magic_shield']
        if magic_shield_level != prev_magic_shield_level:
            prev_stats['magic_shield'] = magic_shield_level
            self.winprint("Magic Shield: {}".format(str(magic_shield_level)), MAGIC_SHIELD_ROW)
        self.char_keeper.handle_equipment(char_status)

    def winprint(self, msg, row=0, col=0, end='\n'):
        self.cliwin.addstr(row, col, msg + end)


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


def main(cliwin, pid, enable_mana, enable_hp, enable_magic_shield, enable_speed,
         only_monitor):
    if pid is None or pid == "":
        raise Exception("PID is required, you may use psgrep -a -l bin/Tibia "
                        "to find the process id")
    mem_config = MEM_CONFIG[str(pid)]
    tibia_wid = get_tibia_wid(pid)
    client = ClientInterface(tibia_wid,
                             HOTKEYS_CONFIG,
                             cliwin,
                             only_monitor=only_monitor)
    char_keeper = CharKeeper(client, CHAR_CONFIGS)
    char_reader = CharReader(MemoryReader(pid, print_async))
    eq_reader = EquipmentReader()
    looter = Looter(HOTKEYS_CONFIG)
    tibia_terminator = TibiaTerminator(tibia_wid,
                                       char_keeper,
                                       char_reader,
                                       eq_reader,
                                       mem_config,
                                       CHAR_CONFIGS,
                                       cliwin,
                                       looter,
                                       enable_mana=enable_mana,
                                       enable_hp=enable_hp,
                                       enable_magic_shield=enable_magic_shield,
                                       enable_speed=enable_speed,
                                       only_monitor=only_monitor)
    tibia_terminator.monitor_char()


if __name__ == "__main__":
    args = parser.parse_args()
#    PPOOL = Pool(processes=3)
    set_debug_level(args.debug_level)
    curses.wrapper(main,
                   args.pid,
                   enable_mana=not args.no_mana,
                   enable_hp=not args.no_hp,
                   enable_magic_shield=not args.no_magic_shield,
                   enable_speed=not args.no_speed,
                   only_monitor=args.only_monitor)
