#!/usr/bin/env python3.8

import os
import time
import curses
import sys

from argparse import ArgumentParser, Namespace
from collections import deque
from typing import List, Iterable, NamedTuple, Optional, Any, Union

from tibia_terminator.char_configs.char_config_loader import load_configs
from tibia_terminator.schemas.reader.interface_config_schema import (
    TibiaWindowSpec,
    TibiaWindowSpecSchema,
)
from tibia_terminator.schemas.hotkeys_config_schema import (
    HotkeysConfigSchema,
    HotkeysConfig,
)
from tibia_terminator.schemas.char_config_schema import BattleConfig, CharConfig
from tibia_terminator.schemas.app_config_schema import AppConfigsSchema, AppConfig
from tibia_terminator.common.char_status import CharStatus, CharStatusAsync
from tibia_terminator.common.logger import set_debug_level, StatsLogger
from tibia_terminator.interface.client_interface import (
    ClientInterface,
    CommandProcessor,
)
from tibia_terminator.interface.keystroke_sender import (
    XdotoolProcess,
    XdotoolKeystrokeSender,
)
from tibia_terminator.interface.macro.loot_macro import LootMacro
from tibia_terminator.keeper.char_keeper import CharKeeper
from tibia_terminator.reader.char_reader38 import CharReader38 as CharReader
from tibia_terminator.reader.equipment_reader import EquipmentReader
from tibia_terminator.reader.memory_reader38 import MemoryReader38 as MemoryReader
from tibia_terminator.reader.window_utils import get_tibia_wid, get_window_geometry
from tibia_terminator.view.view_renderer import (
    ViewRenderer,
    PausedView,
    RunView,
    ConfigSelectionView,
)
from tibia_terminator.schemas.app_status_schema import (
    AppStatus,
    AppState,
    AppStatusSchema,
)

# - If you get the error:
#     Xlib.error.DisplayConnectionError: Can't connect to display ":0": b'No protocol specified\n'
#   Then disable access control to the display by running this command:
#     xhost +
#
# -  Note that this program needs to be executed as superuser in order to
#    access program memory pages.


def build_parser(
        src_parser: Optional[ArgumentParser] = None) -> ArgumentParser:
    parser = src_parser or ArgumentParser(description="Tibia terminator")
    parser.add_argument("pid", help="The PID of Tibia")
    parser.add_argument("--no_mana",
                        help="Do not automatically recover mana.",
                        action="store_true")
    parser.add_argument("--no_hp",
                        help="Do not automatically recover hp.",
                        action="store_true")
    parser.add_argument(
        "--no_magic_shield",
        help="Do not automatically cast magic shield.",
        action="store_true",
    )
    parser.add_argument("--no_speed",
                        help="Do not monitor speed.",
                        action="store_true")
    parser.add_argument(
        "--only_monitor",
        help="Only print stat changes, no action taken",
        action="store_true",
    )
    parser.add_argument("--app_config_path",
                        help="Path to memory configuration vnalues",
                        required=True)
    parser.add_argument(
        "--char_configs_path",
        help=("Path to the char configs directory, where the "
              ".charconfig files are stored."),
        required=True,
    )
    parser.add_argument(
        "--debug_level",
        help=("Set the debug level for debug log messages, "
              "higher values result in more verbose output."),
        type=int,
        default=-1,
    )
    parser.add_argument(
        "--x_offset",
        help=
        ("X value offset for the Tibia window. This is useful for dual monitor"
         " setups, wher you have the Tibia window on the right screen."
         "e.g. If you have 1920x1080 setup, and Tibia is on the monitor to the"
         " right, then this value should be 1920"),
        type=int,
        default=0,
        required=False,
    )
    parser.add_argument(
        "--tibia_window_config_path",
        help=(
            "File with the configuration for the tibia window interface. See:"
            "char_configs/tibia_window_config.json for an example"),
        type=str,
        required=True,
    )
    return parser


SPACE_KEYCODE_A = 263
SPACE_KEYCODE_B = 32
ENTER_KEYCODE = 10
ESCAPE_KEY = 27
LOOP_FREQ_MS = 50
AVG_LOOP_TIME_SAMPLE_SIZE = 50

RUNNING_STATE_MAIN_OPTIONS_MSG = (
    "[Space]: Pause, [Esc]: Exit, [Enter]: Config selection.")
PAUSED_STATE_MAIN_OPTIONS_MSG = (
    "[Space]: Resume, [Esc]: Exit, [Enter]: Config selection.")
CONFIG_SELECTION_MAIN_OPTIONS_MSG = "[Esc]: Exit, [Enter]: Back to paused state."
CONFIG_SELECTION_TITLE = "Type the number of the char config to load: "


class CharConfigMenuEntry(NamedTuple):
    name: str
    char_config: CharConfig
    battle_config: BattleConfig


PAUSE_KEYCODES = [SPACE_KEYCODE_A, SPACE_KEYCODE_B]
RESUME_KEYCODES = [SPACE_KEYCODE_A, SPACE_KEYCODE_B]
CONFIG_SELECTION_KEYCODE = ENTER_KEYCODE
EXIT_KEYCODE = ESCAPE_KEY
DEFAULT_APP_STATUS_FILE = "./app_status.json"


class TibiaTerminator:
    def __init__(
        self,
        tibia_wid,
        char_keeper: CharKeeper,
        char_reader: CharReader,
        equipment_reader: EquipmentReader,
        app_config: AppConfig,
        char_configs: List[CharConfig],
        cliwin,
        loot_macro: LootMacro,
        stats_logger: StatsLogger,
        view_renderer: ViewRenderer,
        cmd_processor: CommandProcessor,
        app_status_file: str = DEFAULT_APP_STATUS_FILE,
        enable_mana: bool = True,
        enable_hp: bool = True,
        enable_magic_shield: bool = True,
        enable_speed: bool = True,
        only_monitor: bool = False,
    ):
        self.tibia_wid = tibia_wid
        self.char_keeper = char_keeper
        self.char_reader = char_reader
        self.app_config = app_config
        self.char_config_entries = list(self.gen_config_entries(char_configs))
        self.cliwin = cliwin
        self.equipment_reader = equipment_reader
        self.loot_macro = loot_macro
        self.stats_logger = stats_logger
        self.view_renderer = view_renderer
        self.cmd_processor = cmd_processor

        # TODO: This should be a separate init function
        self.app_status_file = app_status_file
        app_status = self.load_app_status()
        self.app_state = app_status.state or AppState.CONFIG_SELECTION
        self.selected_config_name = (app_status.selected_config_name
                                     or self.char_config_entries[0].name)
        if not self.load_config(self.selected_config_name):
            self.selected_config_name = self.char_config_entries[0].name

        self.enable_speed = enable_speed
        self.enable_mana = enable_mana
        self.enable_hp = enable_hp
        self.enable_magic_shield = enable_magic_shield
        self.only_monitor = only_monitor
        self.view: Union[
            RunView, PausedView, ConfigSelectionView
        ] = None  # type: ignore
        self.loop_times = deque([0], AVG_LOOP_TIME_SAMPLE_SIZE)
        self.loop_times_sum = 0
        self.avg_loop_time_ms = 0

    def load_config(self, config_name: str) -> bool:
        for config in self.char_config_entries:
            if config.name == config_name:
                self.char_keeper.load_char_config(config.char_config,
                                                  config.battle_config)
                return True
        return False

    def load_app_status(self) -> AppStatus:
        if (os.path.isfile(self.app_status_file)
                and os.path.getsize(self.app_status_file) > 0):
            app_status_schema = AppStatusSchema()
            return app_status_schema.loadf(self.app_status_file)

        return AppStatus(
            state=AppState.CONFIG_SELECTION,
            selected_config_name=self.char_config_entries[0].name,
        )

    def write_app_status(self):
        app_status_schema = AppStatusSchema()
        app_status = AppStatus(state=self.app_state,
                               selected_config_name=self.selected_config_name)
        with open(self.app_status_file, "w", encoding="utf-8") as f:
            f.write(app_status_schema.dumps(app_status))

    def monitor_char(self):
        # TODO: Rather than hardcoding these values, implement the init_*
        # methods in char_reader to automatically find these values, the
        # only challenge is that they're likely to change with every Tibia
        # update.
        # We should consider using OCR instead of reading the mana address.

        if self.enable_mana:
            mana_address = int(self.app_config.mana_memory_address, 16)
        else:
            mana_address = None

        if self.enable_hp and self.app_config.hp_memory_address is not None:
            hp_address = int(self.app_config.hp_memory_address, 16)
        else:
            hp_address = None

        if self.enable_speed:
            speed_address = int(self.app_config.speed_memory_address, 16)
        else:
            speed_address = None

        if self.app_config.magic_shield_memory_address is not None:
            magic_shield_address = int(
                self.app_config.magic_shield_memory_address, 16)
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
            # Always enter paused state first
            self.enter_paused_state()
            if self.app_state is not None and self.app_state is not AppState.PAUSED:
                # load the pre-configured value
                initial_state = self.app_state
                self.app_state = AppState.PAUSED
                self.enter_next_app_state(initial_state)

            while self.app_state != AppState.EXIT:
                start_ms = time.time() * 1000
                keycode = self.cliwin.getch()
                next_state = self.get_next_app_state(keycode)
                self.enter_next_app_state(next_state)
                if self.app_state == AppState.EXIT:
                    self.handle_exit_state()
                    break
                if self.app_state == AppState.PAUSED:
                    self.handle_paused_state()
                elif self.app_state == AppState.RUNNING:
                    self.handle_running_state(self.view)
                elif self.app_state == AppState.CONFIG_SELECTION:
                    self.handle_config_selection_state()

                end_ms = time.time() * 1000
                # Throttle loop frequency
                loop_wait_ms = LOOP_FREQ_MS - (end_ms - start_ms)
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

    def get_next_app_state(self, keycode: int) -> AppState:
        if keycode == EXIT_KEYCODE:
            return AppState.EXIT

        if self.app_state == AppState.RUNNING:
            if keycode in PAUSE_KEYCODES:
                return AppState.PAUSED

        if self.app_state == AppState.PAUSED:
            if keycode in RESUME_KEYCODES:
                return AppState.RUNNING

        if self.app_state == AppState.CONFIG_SELECTION:
            if keycode == CONFIG_SELECTION_KEYCODE:
                return AppState.PAUSED
        elif keycode == CONFIG_SELECTION_KEYCODE:
            return AppState.CONFIG_SELECTION
        # No state change
        return self.app_state

    def enter_next_app_state(self, next_state: AppState) -> bool:
        if self.app_state == next_state:
            return False

        if self.app_state == AppState.RUNNING:
            self.exit_running_state()
        if self.app_state == AppState.PAUSED:
            self.exit_paused_state()
        if self.app_state == AppState.CONFIG_SELECTION:
            self.exit_config_selection_state()

        if next_state == AppState.RUNNING:
            self.enter_running_state()
        elif next_state == AppState.PAUSED:
            self.enter_paused_state()
        elif next_state == AppState.CONFIG_SELECTION:
            self.enter_config_selection_state()

        self.app_state = next_state
        if self.app_state != AppState.EXIT:
            self.write_app_status()
        return True

    def enter_running_state(self):
        self.loot_macro.hook_hotkey()
        self.char_keeper.hook_macros()
        self.view = RunView()
        self.view.title = self.gen_title()
        self.view.main_options = RUNNING_STATE_MAIN_OPTIONS_MSG
        self.stats_logger.run_view = self.view
        self.view_renderer.change_views(self.view)

    def gen_char_status(self, view: RunView) -> CharStatus:
        return CharStatusAsync(
            self.char_reader.get_stats(),
            self.equipment_reader.get_equipment_status(
                emergency_action_amulet_cb=view.
                set_emergency_action_amulet,
                emergency_action_ring_cb=view.set_emergency_action_ring,
                tank_action_amulet_cb=view.set_tank_action_amulet,
                tank_action_ring_cb=view.set_tank_action_ring,
                equipped_amulet_cb=view.set_equipped_amulet,
                equipped_ring_cb=view.set_equipped_ring,
                magic_shield_status_cb=view.set_magic_shield_status,
                normal_action_amulet_cb=view.set_normal_action_amulet,
                normal_action_ring_cb=view.set_normal_action_ring,
            ),
        )

    def handle_running_state(self, view: RunView):
        start_ms = int(time.time() * 1000)
        char_status = self.gen_char_status(view)
        self.char_keeper.handle_char_status(char_status)
        self.equipment_reader.cancel_pending_futures()
        # implicitly waits for all FutureValue objects, since it
        # tries to fetch all values in order to print to screen
        view.set_char_stats(char_status)
        is_in_emergency = self.char_keeper.emergency_reporter.is_in_emergency()
        view.emergency_status = "ON" if is_in_emergency else "OFF"
        is_tank_mode_on = self.char_keeper.tank_mode_reporter.is_tank_mode_on()
        view.tank_mode_status = "ON" if is_tank_mode_on else "OFF"
        end_ms = int(time.time() * 1000)
        self.add_elapsed_loop_time(view, end_ms - start_ms)

    def add_elapsed_loop_time(self, view: RunView, elapsed_ms: int):
        self.loop_times_sum += elapsed_ms - self.loop_times[0]
        self.loop_times.append(elapsed_ms)
        self.avg_loop_time_ms = int(self.loop_times_sum / len(self.loop_times))
        view.set_debug_line(
            f"Avg loop time: {self.avg_loop_time_ms} ms")

    def exit_running_state(self):
        self.stats_logger.run_view = None

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

    def config_input_cb(self, view: ConfigSelectionView, keycode: int):
        if 48 <= keycode <= 57:
            view.user_input += str(keycode - 48)
        elif keycode == ENTER_KEYCODE:
            if view.user_input == "":
                self.enter_next_app_state(AppState.PAUSED)
            else:
                selection = int(view.user_input)
                if selection >= len(self.char_config_entries):
                    view.error = f"Selection index {view.user_input} is invalid."
                    view.signal_error()
                    view.user_input = ""
                else:
                    selected = self.char_config_entries[selection]
                    self.selected_config_name = selected.name
                    self.char_keeper.load_char_config(selected.char_config,
                                                      selected.battle_config)
                    self.enter_next_app_state(AppState.PAUSED)
        elif keycode == EXIT_KEYCODE:
            self.app_state = AppState.EXIT
        elif keycode == curses.KEY_BACKSPACE:
            if len(view.user_input) > 0:
                view.user_input = view.user_input[:len(view.user_input) - 1]
        else:
            view.signal_error()

    def gen_config_entries(
            self,
            char_configs: List[CharConfig]) -> Iterable[CharConfigMenuEntry]:
        for char_config in char_configs:
            for battle_config in char_config.battle_configs:
                if not battle_config.hidden:
                    name = f"{char_config.char_name}.{battle_config.config_name}"
                    yield CharConfigMenuEntry(name, char_config, battle_config)

    def enter_config_selection_state(self):
        config_names = list(map(lambda c: c.name, self.char_config_entries))
        self.view = ConfigSelectionView(config_names, self.config_input_cb)
        self.view.title = self.gen_title()
        self.view.main_options = CONFIG_SELECTION_MAIN_OPTIONS_MSG
        self.view_renderer.change_views(self.view)

    def exit_config_selection_state(self):
        self.write_app_status()

    def handle_config_selection_state(self):
        while self.app_state == AppState.CONFIG_SELECTION:
            # temporarily override state transitions
            time.sleep(0.01)

    def gen_title(self):
        return ("Tibia Terminator. WID: " + str(self.tibia_wid) +
                " Active config: " + self.selected_config_name)


def curses_main(
    cliwin,
    pid,
    app_config: AppConfig,
    char_configs: List[CharConfig],
    tibia_window_spec: TibiaWindowSpec,
    hotkeys_config: HotkeysConfig,
    enable_mana: bool,
    enable_hp: bool,
    enable_magic_shield: bool,
    enable_speed: bool,
    only_monitor: bool,
    x_offset: int = 0,
):
    tibia_wid = get_tibia_wid(pid)
    window_geometry = get_window_geometry(tibia_wid)
    x_offset = x_offset or window_geometry.x
    stats_logger = StatsLogger()

    def print_async(obj: Any) -> None:
        stats_logger.log_action(2, str(obj))

    view_renderer = ViewRenderer(cliwin)
    cmd_processor = CommandProcessor(tibia_wid, stats_logger, only_monitor)
    xdotool_proc = XdotoolProcess()
    xdotool_proc.start()
    try:
        client = ClientInterface(
            hotkeys_config,
            logger=stats_logger,
            cmd_processor=cmd_processor,
            keystroke_sender=XdotoolKeystrokeSender(xdotool_proc, tibia_wid),
        )
        char_keeper = CharKeeper(client, char_configs[0],
                                 char_configs[0].battle_configs[0],
                                 hotkeys_config)
        char_reader = CharReader(MemoryReader(pid, print_async))
        eq_reader = EquipmentReader(tibia_wid=int(tibia_wid),
                                    tibia_window_spec=tibia_window_spec)
        loot_macro = LootMacro(client, hotkeys_config, x_offset)
        tibia_terminator = TibiaTerminator(
            tibia_wid,
            char_keeper,
            char_reader,
            eq_reader,
            app_config,
            char_configs,
            cliwin,
            loot_macro,
            stats_logger,
            view_renderer,
            cmd_processor,
            enable_mana=enable_mana,
            enable_hp=enable_hp,
            enable_magic_shield=enable_magic_shield,
            enable_speed=enable_speed,
            only_monitor=only_monitor,
        )
        tibia_terminator.monitor_char()
    finally:
        xdotool_proc.stop()


def main(args: Namespace):
    set_debug_level(args.debug_level)
    if args.debug_level > 1:
        print(args)

    if not args.pid:
        raise Exception("PID is required, you may use psgrep -a -l bin/Tibia "
                        "to find the process id")
    app_configs_schema = AppConfigsSchema()
    app_configs = app_configs_schema.loadf(args.app_config_path)
    app_config = app_configs[str(args.pid)]
    if not app_configs[str(args.pid)]:
        raise Exception(
            f"App config for PID: {args.pid} not configured. Available"
            f" PIDs: {[c.pid for c in app_configs]}")
    hotkeys_config = HotkeysConfigSchema().loadf(
        os.path.join(args.char_configs_path, "hotkeys_config.json"))
    char_configs = list(load_configs(args.char_configs_path))
    if len(char_configs) == 0:
        raise Exception(
            f"No .charconfig files found in {args.char_configs_path}")
    tibia_window_spec_schema = TibiaWindowSpecSchema()
    tibia_window_spec = tibia_window_spec_schema.loadf(
        args.tibia_window_config_path)

    curses.wrapper(
        curses_main,
        args.pid,
        app_config,
        char_configs,
        tibia_window_spec,
        hotkeys_config,
        enable_mana=not args.no_mana,
        enable_hp=not args.no_hp,
        enable_magic_shield=not args.no_magic_shield,
        enable_speed=not args.no_speed,
        only_monitor=args.only_monitor,
        x_offset=args.x_offset,
    )


if __name__ == "__main__":
    main_parser = build_parser()
    parsed_args = main_parser.parse_args(sys.argv)
    main(parsed_args)
