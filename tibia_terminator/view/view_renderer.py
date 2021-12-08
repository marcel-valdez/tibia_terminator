#!/usr/bin/env python3.8

import argparse
import curses

from queue import Queue
from threading import Thread, Lock
from time import sleep
from typing import List, Any, Callable, Optional

from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.common.logger import get_debug_level

parser = argparse.ArgumentParser(
    description='Maually test the Tibia Terminator renderer.')
parser.add_argument('--layout', help='Options: run, selection.')


class CliScreen():
    def __init__(self, cli):
        self.cli = cli
        self.lines = []

    def clear(self):
        self.lines = []
        self.cli.clear()

    def refresh(self):
        self.cli.refresh()

    def readonly_mode(self):
        self.cli.nodelay(True)
        self.cli.idlok(True)
        self.cli.leaveok(True)

    def input_mode(self):
        self.cli.nodelay(True)
        self.cli.idlok(True)
        self.cli.leaveok(False)

    def getch(self, y, x):
        return self.cli.getch(y, x)

    def __resize(self, lines: List[str], new_len: int):
        while len(lines) < new_len:
            lines.append('')

    def print(self, line: str, row: int, col: int = 0):
        """Efficiently prints the line. It will only print the diff of what was
           previously printed on that particular row."""
        if row >= len(self.lines):
            self.__resize(self.lines, row + 1)

        diff_substr, diff_idx = self.__diff_substr(self.lines[row], line)
        if diff_idx != -1:
            self.lines[row] = line
            self.cli.move(row, diff_idx + col)
            self.cli.clrtoeol()
            self.cli.addstr(row, diff_idx + col, diff_substr)

    def __diff_substr(self, old: str, new: str) -> str:
        diff_idx = self.__diff_index(old, new)
        # they're different
        if diff_idx != -1:
            return new[diff_idx:], diff_idx
        # they're the same
        else:
            return None, -1

    def __diff_index(self, a: str, b: str) -> int:
        if (len(a) == 0 and len(b) != 0) or (len(a) != 0 and len(b) == 0):
            return 0

        i = 0
        while i < len(a) and i < len(b):
            if a[i] != b[i]:
                return i
            i += 1

        if i < len(a) or i < len(b):
            return i
        else:
            return -1


class View():
    TITLE_ROW = 0
    MAIN_OPTIONS_ROW = TITLE_ROW + 1
    ERRORS_ROW = MAIN_OPTIONS_ROW + 1

    def __init__(self):
        self.title = ''
        self.main_options = ''
        self.error = ''

    def render_header(self, cli_screen: CliScreen):
        cli_screen.print(self.title, View.TITLE_ROW)
        cli_screen.print(self.main_options, View.MAIN_OPTIONS_ROW)
        cli_screen.print(self.error, View.ERRORS_ROW)

    def set_modes(self, cli_screen: CliScreen):
        """Called once when the view is being transitioned to. Use this to set the
        required modes in cli_screen."""
        cli_screen.readonly_mode()
        cli_screen.clear()

    def unset_modes(self, cli_screen: CliScreen):
        """Called once when the view is being transitioned to. Use this to unset any
        special/conflicting modes that were set in set_modes."""
        cli_screen.clear()

    def render(self, cli_screen: CliScreen):
        raise Exception("This method needs to be implemented by a subclass.")


class ViewRenderer(Thread):
    def __init__(self, cliwin, cli_screen: CliScreen = None):
        super().__init__(daemon=True)
        self.cli_screen = cli_screen or CliScreen(cliwin)
        self.view: Optional[View] = None
        self.next_view: Optional[View] = None
        self.stopped = False
        self.transition = False
        self.lock = Lock()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            if self.transition:
                with self.lock:
                    self.view = self.next_view
                    self.next_view = None
                    self.transition = False
            self.render()
            # sleep 50 ms
            sleep(0.05)

    def change_views(self, view: View):
        with self.lock:
            self.transition = True
            self.next_view = view
            if self.view:
                self.view.unset_modes(self.cli_screen)
            self.next_view.set_modes(self.cli_screen)

    def render(self):
        if self.view:
            self.view.render(self.cli_screen)


class ConfigSelectionView(View):
    CONFIG_SELECTION_ROW = View.ERRORS_ROW + 1

    def __init__(self, config_options: List[str],
                 input_cb: Callable[[View, int], None]):
        super().__init__()
        self.config_options = config_options
        self.input_cb = input_cb
        self.selection_title = "Type the number of the char config to load: "
        self.user_input = ''
        self.error_count = 0

    def set_modes(self, cli_screen: CliScreen):
        cli_screen.input_mode()
        cli_screen.clear()

    def signal_error(self):
        self.error_count += 1

    def render(self, cli_screen: CliScreen):
        subtitle = self.selection_title + self.user_input
        input_yx = (ConfigSelectionView.CONFIG_SELECTION_ROW, len(subtitle))
        self.render_header(cli_screen)
        self.render_content(cli_screen, subtitle)
        keycode = cli_screen.getch(*input_yx)
        self.input_cb(self, keycode)
        if self.error_count > 0:
            curses.beep()
            self.error_count -= 1
        cli_screen.refresh()

    def render_content(self, cli_screen, subtitle):
        i = 0
        for config in self.config_options:
            cli_screen.print(f"{i}: {config}",
                             ConfigSelectionView.CONFIG_SELECTION_ROW + i + 1)
            i += 1
        cli_screen.print(subtitle, ConfigSelectionView.CONFIG_SELECTION_ROW)


class PausedView(View):
    def __init__(self):
        super().__init__()

    def render(self, cli_screen: CliScreen):
        self.render_header(cli_screen)
        cli_screen.refresh()


class RunView(View):
    MANA_ROW = View.ERRORS_ROW + 1
    HP_ROW = MANA_ROW + 1
    SPEED_ROW = HP_ROW + 1
    MAGIC_SHIELD_ROW = SPEED_ROW + 1
    EMERGENCY_ACTION_AMULET_ROW = MAGIC_SHIELD_ROW + 1
    EMERGENCY_ACTION_RING_ROW = EMERGENCY_ACTION_AMULET_ROW + 1
    EQUIPPED_AMULET_ROW = EMERGENCY_ACTION_RING_ROW + 1
    EQUIPPED_RING_ROW = EQUIPPED_AMULET_ROW + 1
    MAGIC_SHIELD_STATUS_ROW = EQUIPPED_RING_ROW + 1
    EMERGENCY_STATUS_ROW = MAGIC_SHIELD_STATUS_ROW + 1
    DEBUG_ROW_1 = EMERGENCY_STATUS_ROW + 1
    DEBUG_ROW_2 = DEBUG_ROW_1 + 1
    LOG_ROW = DEBUG_ROW_2 + 1
    MAX_LOG_BUFFER = 10

    def __init__(self):
        super().__init__()
        self.title = 'N/A'
        self.mana = 'N/A'
        self.hp = 'N/A'
        self.speed = 'N/A'
        self.magic_shield_level = 'N/A'
        self.emergency_action_amulet = 'N/A'
        self.emergency_action_ring = 'N/A'
        self.equipped_amulet = 'N/A'
        self.equipped_ring = 'N/A'
        self.magic_shield_status = 'N/A'
        self.emergency_status = 'N/A'
        self.debug_line_1 = ''
        self.debug_line_2 = ''
        self.action_log_queue = Queue()
        self.log_entries = []
        self.lock = Lock()

    def add_log(self, log, debug_level=0):
        if debug_level <= get_debug_level():
            self.action_log_queue.put_nowait(log)

    def set_debug_line(self, debug_line: str = ''):
        self.set_debug_line_1(debug_line)

    def set_debug_line_1(self, debug_line: str = ''):
        self.debug_line_1 = debug_line

    def set_debug_line_2(self, debug_line: str = ''):
        self.debug_line_2 = debug_line

    def set_char_stats(self, char_status: CharStatus):
        self.mana = char_status.mana
        self.hp = char_status.hp
        self.speed = char_status.speed
        self.magic_shield_level = char_status.magic_shield_level

    def set_emergency_action_amulet(self, value: Any = 'N/A'):
        self.emergency_action_amulet = str(value)

    def set_emergency_action_ring(self, value: Any = 'N/A'):
        self.emergency_action_ring = str(value)

    def set_equipped_ring(self, value: Any = 'N/A'):
        self.equipped_ring = str(value)

    def set_equipped_amulet(self, value: Any = 'N/A'):
        self.equipped_amulet = str(value)

    def set_magic_shield_status(self, value: Any = 'N/A'):
        self.magic_shield_status = str(value)

    def render(self, cli_screen: CliScreen):
        self.render_header(cli_screen)
        self.render_stats(cli_screen)
        self.render_debug_lines(cli_screen)
        self.render_logs(cli_screen)
        cli_screen.refresh()

    def drain_log_queue(self):
        new_logs = []
        while (self.action_log_queue.qsize() > 0
               and len(new_logs) <= RunView.MAX_LOG_BUFFER):
            new_logs.append(self.action_log_queue.get_nowait())

        carryon = RunView.MAX_LOG_BUFFER - len(new_logs)
        new_logs.extend(self.log_entries[:carryon])
        # completely override the log entries list, rather than
        # mutate in-place.
        self.log_entries = new_logs

    def render_logs(self, cli_screen: CliScreen):
        cli_screen.print('Log Entries', RunView.LOG_ROW)
        if self.action_log_queue.qsize() > 0:
            self.drain_log_queue()

        i = 0
        # lock in logs at the moment they're rendered
        logs = self.log_entries
        while i < RunView.MAX_LOG_BUFFER:
            if i < len(logs):
                cli_screen.print(logs[i], RunView.LOG_ROW + i + 1)
            else:
                cli_screen.print(" ", RunView.LOG_ROW + i + 1)
            i += 1

    def render_stats(self, cli_screen: CliScreen):
        cli_screen.print(f"Mana: {self.mana}", RunView.MANA_ROW)
        cli_screen.print(f"HP: {self.hp}", RunView.HP_ROW)
        cli_screen.print(f"Speed: {self.speed}", RunView.SPEED_ROW)
        cli_screen.print(f"Magic Shield: {self.magic_shield_level}",
                         RunView.MAGIC_SHIELD_ROW)
        cli_screen.print(
            f"Emergency Action Amulet: {self.emergency_action_amulet}",
            RunView.EMERGENCY_ACTION_AMULET_ROW)
        cli_screen.print(
            f"Emergency Action Ring: {self.emergency_action_ring}",
            RunView.EMERGENCY_ACTION_RING_ROW)
        cli_screen.print(f"Equipped Amulet: {self.equipped_amulet}",
                         RunView.EQUIPPED_AMULET_ROW)
        cli_screen.print(f"Equipped Ring: {self.equipped_ring}",
                         RunView.EQUIPPED_RING_ROW)
        cli_screen.print(f"Magic Shield Status: {self.magic_shield_status}",
                         RunView.MAGIC_SHIELD_STATUS_ROW)
        cli_screen.print(f"Emergency Status: {self.emergency_status}",
                         RunView.EMERGENCY_STATUS_ROW)

    def render_debug_lines(self, cli_screen: CliScreen):
        cli_screen.print(self.debug_line_1, RunView.DEBUG_ROW_1)
        cli_screen.print(self.debug_line_2, RunView.DEBUG_ROW_2)


def stress_run_view(cliwin):
    # set the view's state
    int_rotation = [111, 22, 3333, 4, 55555]
    str_rotation = ['first', 'second', 'third', 'fourth', 'fifth']
    char_status = CharStatus(hp=int_rotation[0],
                             speed=int_rotation[1],
                             mana=int_rotation[2],
                             magic_shield_level=int_rotation[3],
                             equipment_status={
                                 'emergency_action_amulet': str_rotation[0],
                                 'emergency_action_ring': str_rotation[1],
                                 'equipped_ring': str_rotation[2],
                                 'equipped_amulet': str_rotation[3],
                                 'magic_shield_status': str_rotation[4],
                             })

    def update_status(char_status, idx):
        char_status.hp = int_rotation[idx % len(int_rotation)]
        char_status.speed = int_rotation[(idx + 1) % len(int_rotation)]
        char_status.mana = int_rotation[(idx + 2) % len(int_rotation)]
        char_status.magic_shield_level = \
            int_rotation[(idx + 3) % len(int_rotation)]
        char_status.emergency_action_amulet = \
            str_rotation[(idx + 0) % len(str_rotation)]
        char_status.emergency_action_ring = \
            str_rotation[(idx + 1) % len(str_rotation)]
        char_status.equipped_ring = str_rotation[(idx + 2) % len(str_rotation)]
        char_status.equipped_amulet = \
            str_rotation[(idx + 3) % len(str_rotation)]
        char_status.magic_shield_status = \
            str_rotation[(idx + 4) % len(str_rotation)]

    view = RunView()
    view.title = "This is a stress test of the RunView."
    view.main_options = "These are the main options of the RunView."
    view.error = "This is the error row of the RunView."
    renderer = ViewRenderer(cliwin)
    # enter state
    renderer.start()
    # transition into main view
    renderer.change_views(view)
    try:
        i = 0
        while True:
            view.set_char_stats(char_status)
            view.set_magic_shield_status(char_status.magic_shield_status)
            view.set_equipped_ring(char_status.equipped_ring)
            view.set_equipped_amulet(char_status.equipped_amulet)
            view.set_emergency_action_amulet(
                char_status.emergency_action_amulet)
            view.set_emergency_action_ring(char_status.emergency_action_ring)
            view.add_log(
                f"This is log #{i} and it is very very long. Let us see.",
                -100)
            view.error = f"Number of log entries: {i}"
            i += 1
            update_status(char_status, i)
            sleep(0.125)
    finally:
        renderer.stop()


def stress_config_selection_view(cliwin):
    def update_cb(config_view, keycode):
        if keycode >= 48 and keycode <= 57:
            config_view.user_input += str(keycode - 48)
        elif keycode == curses.KEY_BACKSPACE:
            config_view.user_input = \
                config_view.user_input[:len(config_view.user_input) - 1]
        else:
            config_view.signal_error()

    view = ConfigSelectionView(['one', 'two', 'three', 'four', 'five'],
                               update_cb)
    view.title = "This is a stress test of the ConfigSelectionView."
    view.main_options = "These are the main options of the ConfigSelectionView."
    view.error = "This is the error row of the RunView."
    renderer = ViewRenderer(cliwin)
    # enter state
    renderer.start()
    # transition into main view
    renderer.change_views(view)
    try:
        while True:
            sleep(0.1)
    finally:
        renderer.stop()


def main(cliwin, layout):
    if layout == 'run':
        stress_run_view(cliwin)
    elif layout == 'selection':
        stress_config_selection_view(cliwin)
    else:
        raise Exception(
            f'Unknown layout <{layout}>. Please specify a valid layout.')


if __name__ == '__main__':
    args = parser.parse_args()
    curses.wrapper(main, args.layout)
