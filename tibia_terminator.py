#!/usr/bin/env python3.8

import argparse
import time
import curses
import sys


from window_utils import get_tibia_wid
from client_interface import (ClientInterface, CommandProcessor)
from memory_reader38 import MemoryReader38 as MemoryReader
from char_keeper import CharKeeper
from char_reader38 import CharReader38 as CharReader
from char_status import CharStatus
from equipment_reader import (EquipmentReader, AmuletName, RingName,
                              MagicShieldStatus)
from char_config import CHAR_CONFIGS, HOTKEYS_CONFIG
from app_config import MEM_CONFIG
from logger import (set_debug_level, StatsLogger, StatsEntry, LogEntry)
from loot_macro import LootMacro
from view_renderer import (ViewRenderer, PausedView,
                           RunView, ConfigSelectionView)

# - If you get the error:
#     Xlib.error.DisplayConnectionError: Can't connect to display ":0": b'No protocol specified\n'
#   Then disable access control to the display by running this command:
#     xhost +
#
# -  Note that this program needs to be executed as superuser in order to
#    access program memory pages.

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

SPACE_KEYCODE_A = 263
SPACE_KEYCODE_B = 32
ENTER_KEYCODE = 10
ESCAPE_KEY = 27
LOOP_FREQ_MS = 100

RUNNING_STATE_MAIN_OPTIONS_MSG = "[Space]: Pause, [Esc]: Exit, [Enter]: Config selection."
PAUSED_STATE_MAIN_OPTIONS_MSG = "[Space]: Resume, [Esc]: Exit, [Enter]: Config selection."
CONFIG_SELECTION_MAIN_OPTIONS_MSG = "[Esc]: Exit, [Enter]: Back to paused state."
CONFIG_SELECTION_TITLE = "Type the number of the char config to load: "


class AppStates:
    PAUSED = "__PAUSED__"
    RUNNING = "__RUNNING__"
    CONFIG_SELECTION = "__CONFIG_SELECTION__"
    EXIT = "__EXIT__"


PAUSE_KEYCODES = [SPACE_KEYCODE_A, SPACE_KEYCODE_B]
RESUME_KEYCODES = [SPACE_KEYCODE_A, SPACE_KEYCODE_B]
CONFIG_SELECTION_KEYCODE = ENTER_KEYCODE
EXIT_KEYCODE = ESCAPE_KEY


class TibiaTerminator:
    def __init__(self,
                 tibia_wid,
                 char_keeper: CharKeeper,
                 char_reader: CharReader,
                 equipment_reader: EquipmentReader,
                 mem_config,
                 char_configs,
                 cliwin,
                 loot_macro: LootMacro,
                 stats_logger: StatsLogger,
                 view_renderer: ViewRenderer,
                 cmd_processor: CommandProcessor,
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
        self.loot_macro = loot_macro
        self.stats_logger = stats_logger
        self.view_renderer = view_renderer
        self.cmd_processor = cmd_processor
        self.enable_speed = enable_speed
        self.enable_mana = enable_mana
        self.enable_hp = enable_hp
        self.enable_magic_shield = enable_magic_shield
        self.only_monitor = only_monitor
        self.app_state = None
        self.selected_config_name = char_configs[0]["name"]
        self.view = None

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

        self.equipment_reader.open()
        self.view_renderer.start()
        self.cmd_processor.start()
        try:
            self.app_state = AppStates.PAUSED
            self.enter_paused_state()
            while self.app_state != AppStates.EXIT:
                start = time.time() * 1000

                keycode = self.cliwin.getch()
                self.enter_next_app_state(keycode)
                if self.app_state == AppStates.EXIT:
                    self.handle_exit_state()
                    break
                elif self.app_state == AppStates.PAUSED:
                    self.handle_paused_state()
                elif self.app_state == AppStates.RUNNING:
                    self.handle_running_state()
                elif self.app_state == AppStates.CONFIG_SELECTION:
                    self.handle_config_selection_state()

                end = time.time() * 1000
                # Throttle loop frequency
                loop_wait_ms = LOOP_FREQ_MS - (end - start)
                if loop_wait_ms > 0:
                    time.sleep(loop_wait_ms / 1000)
        finally:
            self.loot_macro.unhook_hotkey()
            self.char_keeper.unhook_macros()
            self.equipment_reader.close()
            self.view_renderer.stop()
            self.cmd_processor.stop()

    def handle_exit_state(self):
        """Exits the program based on user input."""
        pass

    def enter_next_app_state(self, keycode):
        next_state = self.app_state
        if keycode == EXIT_KEYCODE:
            next_state = AppStates.EXIT

        if self.app_state == AppStates.RUNNING:
            if keycode in PAUSE_KEYCODES:
                next_state = AppStates.PAUSED

        if self.app_state == AppStates.PAUSED:
            if keycode in RESUME_KEYCODES:
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
        self.loot_macro.hook_hotkey()
        self.char_keeper.hook_macros()
        self.view = RunView()
        self.view.title = self.gen_title()
        self.view.main_options = RUNNING_STATE_MAIN_OPTIONS_MSG
        self.stats_logger.run_view = self.view
        self.view_renderer.change_views(self.view)

    def handle_running_state(self):
        stats = self.char_reader.get_stats()
        # 1-5 ms
        emergency_amulet_action_bar_name = \
            self.equipment_reader.get_emergency_action_bar_amulet_name()
        # 1-5 ms
        emergency_ring_action_bar_name = \
            self.equipment_reader.get_emergency_action_bar_ring_name()
        # 1-5 ms
        equipped_amulet_name = self.equipment_reader.get_equipped_amulet_name()
        # 1-5 ms
        equipped_ring_name = self.equipment_reader.get_equipped_ring_name()
        # 1-5 ms
        magic_shield_status = \
            self.equipment_reader.get_magic_shield_status()
        equipment_status = {
            'emergency_action_amulet': emergency_amulet_action_bar_name,
            'equipped_amulet': equipped_amulet_name,
            'emergency_action_ring': emergency_ring_action_bar_name,
            'equipped_ring': equipped_ring_name,
            'magic_shield_status': magic_shield_status
        }

        char_status = CharStatus(
            mana=stats['mana'],
            hp=stats['hp'],
            speed=stats['speed'],
            magic_shield_level=stats['magic_shield'],
            equipment_status=equipment_status)
        self.handle_char_status(char_status)
        self.view.set_char_status(char_status)

    def exit_running_state(self):
        self.stats_logger.run_view = None
        pass

    def enter_paused_state(self):
        self.loot_macro.unhook_hotkey()
        self.char_keeper.unhook_macros()
        self.view = PausedView()
        self.view.title = self.gen_title()
        self.view.main_options = PAUSED_STATE_MAIN_OPTIONS_MSG
        self.view_renderer.change_views(self.view)

    def exit_paused_state(self):
        pass

    def handle_paused_state(self):
        pass

    def config_input_cb(self, view: ConfigSelectionView, keycode):
        if keycode >= 48 and keycode <= 57:
            view.user_input += str(keycode - 48)
        elif keycode == ENTER_KEYCODE:
            if view.user_input == '':
                self.exit_config_selection_state()
                self.enter_paused_state()
                self.app_state = AppStates.PAUSED
            else:
                selection = int(view.user_input)
                if selection >= len(self.char_configs):
                    view.error = f"Selection index {view.user_input} is invalid."
                    view.signal_error()
                    view.user_input = ''
                else:
                    self.selected_config_name = self.char_configs[selection]["name"]
                    self.char_keeper.change_char_config(selection)
                    self.exit_config_selection_state()
                    self.enter_paused_state()
                    self.app_state = AppStates.PAUSED
        elif keycode == EXIT_KEYCODE:
            self.app_state = AppStates.EXIT
        elif keycode == curses.KEY_BACKSPACE:
            if len(view.user_input) > 0:
                view.user_input = view.user_input[:len(view.user_input) - 1]
        else:
            view.signal_error()

    def enter_config_selection_state(self):
        config_names = list(map(lambda c: c['name'], self.char_configs))
        self.view = ConfigSelectionView(config_names, self.config_input_cb)
        self.view.title = self.gen_title()
        self.view.main_options = CONFIG_SELECTION_MAIN_OPTIONS_MSG
        self.view_renderer.change_views(self.view)

    def exit_config_selection_state(self):
        pass

    def handle_config_selection_state(self):
        while self.app_state == AppStates.CONFIG_SELECTION:
            # temporarily override state transitions
            time.sleep(0.01)

    def handle_char_status(self, char_status: CharStatus):
        # Note that we have to handle the mana change always, even if
        # it hasn't actually changed, because a command to heal or drink mana
        # or haste could be ignored if the character is exhausted, therefore
        # we have to spam the action until the effect takes place.
        if self.enable_hp:
            self.char_keeper.handle_hp_change(char_status)

        if self.enable_mana:
            self.char_keeper.handle_mana_change(char_status)

        self.char_keeper.handle_equipment(char_status)

        if self.enable_speed:
            self.char_keeper.handle_speed_change(char_status)

    def gen_title(self):
        return "Tibia Terminator. WID: " + str(self.tibia_wid) + " Active config: " + self.selected_config_name


def main(cliwin, pid, enable_mana, enable_hp, enable_magic_shield, enable_speed,
         only_monitor):
    if pid is None or pid == "":
        raise Exception("PID is required, you may use psgrep -a -l bin/Tibia "
                        "to find the process id")
    mem_config = MEM_CONFIG[str(pid)]
    tibia_wid = get_tibia_wid(pid)
    stats_logger = StatsLogger()

    def print_async(msg):
        stats_logger.log_action(2, msg)
    view_renderer = ViewRenderer(cliwin)
    cmd_processor = CommandProcessor(tibia_wid, stats_logger, only_monitor)
    client = ClientInterface(HOTKEYS_CONFIG,
                             logger=stats_logger,
                             cmd_processor=cmd_processor)
    char_keeper = CharKeeper(client, CHAR_CONFIGS, HOTKEYS_CONFIG)
    char_reader = CharReader(MemoryReader(pid, print_async))
    eq_reader = EquipmentReader()
    loot_macro = LootMacro(HOTKEYS_CONFIG)
    tibia_terminator = TibiaTerminator(tibia_wid,
                                       char_keeper,
                                       char_reader,
                                       eq_reader,
                                       mem_config,
                                       CHAR_CONFIGS,
                                       cliwin,
                                       looter,
                                       stats_logger,
                                       view_renderer,
                                       cmd_processor,
                                       enable_mana=enable_mana,
                                       enable_hp=enable_hp,
                                       enable_magic_shield=enable_magic_shield,
                                       enable_speed=enable_speed,
                                       only_monitor=only_monitor)
    tibia_terminator.monitor_char()


if __name__ == "__main__":
    args = parser.parse_args()
    set_debug_level(args.debug_level)
    curses.wrapper(main,
                   args.pid,
                   enable_mana=not args.no_mana,
                   enable_hp=not args.no_hp,
                   enable_magic_shield=not args.no_magic_shield,
                   enable_speed=not args.no_speed,
                   only_monitor=args.only_monitor)
