#!/usr/bin/env python3.8

import argparse
import curses
from queue import Queue
from logger import get_debug_level
from threading import Thread, Lock
from time import sleep
from char_status import CharStatus


parser = argparse.ArgumentParser(
    description='Maually test the Tibia Terminator renderer.')
parser.add_argument('--layout',
                    help='Options: run, selection.')


class View():
    TITLE_ROW = 0
    MAIN_OPTIONS_ROW = TITLE_ROW + 1
    ERRORS_ROW = MAIN_OPTIONS_ROW + 1

    def __init__(self):
        self.title = ''
        self.main_options = ''
        self.error = ''

    def render_header(self, cliwin):
        cliwin.addstr(View.TITLE_ROW, 0, self.title)
        cliwin.addstr(View.MAIN_OPTIONS_ROW, 0, self.main_options)
        cliwin.addstr(View.ERRORS_ROW, 0, self.error)

    def set_modes(self, cliwin):
        """Called once when the view is being transitioned to. Use this to set the
        required modes in cliwin."""
        cliwin.nodelay(True)
        cliwin.idlok(True)
        cliwin.leaveok(True)

    def unset_modes(self, cliwin):
        """Called once when the view is being transitioned to. Use this to unset any
        special/conflicting modes that were set in set_modes."""
        pass

    def render(self, cliwin):
        raise Exception("This method needs to be implemented by a subclass.")


class ViewRenderer(Thread):
    def __init__(self, cliwin):
        super().__init__(daemon=True)
        self.cliwin = cliwin
        self.view = None
        self.next_view = None
        self.stopped = False
        self.transition = False
        self.lock = Lock()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            if self.transition:
                self.lock.acquire()
                try:
                    if self.view is not None:
                        self.view.unset_modes(self.cliwin)
                    self.next_view.set_modes(self.cliwin)
                    self.view = self.next_view
                    self.next_view = None
                    self.transition = False
                finally:
                    self.lock.release()
            self.render()
            # sleep 50 ms
            sleep(0.05)

    def change_views(self, view: View):
        self.lock.acquire()
        try:
            self.transition = True
            self.next_view = view
        finally:
            self.lock.release()

    def render(self):
        if not self.view is None:
            self.view.render(self.cliwin)


class ConfigSelectionView(View):
    CONFIG_SELECTION_ROW = View.ERRORS_ROW + 1

    def __init__(self, config_options, input_cb):
        super().__init__()
        self.config_options = config_options
        self.input_cb = input_cb
        self.selection_title = "Type the number of the char config to load: "
        self.user_input = ''
        self.error_count = 0

    def set_modes(self, cliwin):
        cliwin.nodelay(True)
        cliwin.idlok(True)
        cliwin.leaveok(False)
        cliwin.clear()

    def unset_modes(self, cliwin):
        cliwin.clear()

    def signal_error(self):
        self.error_count += 1

    def render(self, cliwin):
        cliwin.clear()
        subtitle = self.selection_title + self.user_input
        input_yx = (ConfigSelectionView.CONFIG_SELECTION_ROW, len(subtitle))
        self.render_header(cliwin)
        self.render_content(cliwin, subtitle)
        keycode = cliwin.getch(*input_yx)
        self.input_cb(self, keycode)
        if self.error_count > 0:
            curses.beep()
            self.error_count -= 1
        cliwin.refresh()

    def render_content(self, cliwin, subtitle):
        i = 0
        for config in self.config_options:
            cliwin.addstr(
                ConfigSelectionView.CONFIG_SELECTION_ROW + i + 1, 0,
                f"{i}: {config}")
            i += 1
        cliwin.addstr(
            ConfigSelectionView.CONFIG_SELECTION_ROW,
            0,
            subtitle)


class PausedView(View):
    def __init__(self):
        super().__init__()

    def set_modes(self, cliwin):
        cliwin.nodelay(True)
        cliwin.idlok(True)
        cliwin.leaveok(True)

    def render(self, cliwin):
        cliwin.clear()
        self.render_header(cliwin)
        cliwin.refresh()


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
    DEBUG_ROW = MAGIC_SHIELD_STATUS_ROW + 1
    LOG_ROW = DEBUG_ROW + 1
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
        self.action_log_queue = Queue()
        self.log_entries = []
        self.lock = Lock()

    def set_modes(self, cliwin):
        cliwin.nodelay(True)
        cliwin.idlok(True)
        cliwin.leaveok(True)


    def add_log(self, log, debug_level=0):
        if debug_level <= get_debug_level():
            self.action_log_queue.put_nowait(log)

    def set_char_status(self, char_status: CharStatus):
        self.mana = char_status.mana
        self.hp = char_status.hp
        self.speed = char_status.speed
        self.magic_shield_level = char_status.magic_shield_level
        self.emergency_action_amulet = char_status.emergency_action_amulet
        self.emergency_action_ring = char_status.emergency_action_ring
        self.equipped_ring = char_status.equipped_ring
        self.equipped_amulet = char_status.equipped_amulet
        self.magic_shield_status = char_status.magic_shield_status

    def render(self, cliwin):
        cliwin.clear()
        self.render_header(cliwin)
        self.render_stats(cliwin)
        self.render_logs(cliwin)
        cliwin.refresh()

    def drain_log_queue(self):
        new_logs = []
        while (self.action_log_queue.qsize() > 0 and
                len(new_logs) <= RunView.MAX_LOG_BUFFER):
            new_logs.append(self.action_log_queue.get_nowait())

        carryon = RunView.MAX_LOG_BUFFER - len(new_logs)
        new_logs.extend(self.log_entries[:carryon])
        # completely override the log entries list, rather than
        # mutate in-place.
        self.log_entries = new_logs

    def render_logs(self, cliwin):
        cliwin.addstr(RunView.LOG_ROW, 0, 'Log Entries')
        if self.action_log_queue.qsize() > 0:
            self.drain_log_queue()

        i = 0
        # lock in logs at the moment they're rendered
        logs = self.log_entries
        while i < RunView.MAX_LOG_BUFFER:
            if i < len(logs):
                cliwin.addstr(RunView.LOG_ROW + i + 1, 0, logs[i])
            else:
                cliwin.addstr(RunView.LOG_ROW + i + 1, 0, " ")
            i += 1

    def render_stats(self, cliwin):
        cliwin.addstr(RunView.MANA_ROW, 0, f"Mana: {str(self.mana)}")
        cliwin.addstr(RunView.HP_ROW, 0, f"HP: {str(self.hp)}")
        cliwin.addstr(RunView.SPEED_ROW, 0, f"Speed: {str(self.speed)}")
        cliwin.addstr(RunView.MAGIC_SHIELD_ROW, 0,
                      f"Magic Shield: {str(self.magic_shield_level)}")
        cliwin.addstr(RunView.EMERGENCY_ACTION_AMULET_ROW, 0,
                      f"Emergency Action Amulet: {self.emergency_action_amulet}")
        cliwin.addstr(RunView.EMERGENCY_ACTION_RING_ROW, 0,
                      f"Emergency Action Ring: {self.emergency_action_ring}")
        cliwin.addstr(RunView.EQUIPPED_AMULET_ROW, 0,
                      f"Equipped Amulet: {self.equipped_amulet}")
        cliwin.addstr(RunView.EQUIPPED_RING_ROW, 0,
                      f"Equipped Ring: {self.equipped_ring}")
        cliwin.addstr(RunView.MAGIC_SHIELD_STATUS_ROW, 0,
                      f"Magic Shield Status: {self.magic_shield_status}")


def stress_run_view(cliwin):
    # set the view's state
    int_rotation = [111, 22, 3333, 4, 55555]
    str_rotation = ['first', 'second', 'third', 'fourth', 'fifth']
    char_status = CharStatus(
        hp=int_rotation[0],
        speed=int_rotation[1],
        mana=int_rotation[2],
        magic_shield_level=int_rotation[3],
        equipment_status={
            'emergency_action_amulet': str_rotation[0],
            'emergency_action_ring': str_rotation[1],
            'equipped_ring': str_rotation[2],
            'equipped_amulet': str_rotation[3],
            'magic_shield_status': str_rotation[4],
        }
    )

    def update_status(char_status, idx):
        char_status.hp = int_rotation[idx % len(int_rotation)]
        char_status.speed = int_rotation[(idx + 1) % len(int_rotation)]
        char_status.mana = int_rotation[(idx + 2) % len(int_rotation)]
        char_status.magic_shield_level = int_rotation[(
            idx + 3) % len(int_rotation)]
        char_status.emergency_action_amulet = str_rotation[(
            idx + 0) % len(str_rotation)]
        char_status.emergency_action_ring = str_rotation[(
            idx + 1) % len(str_rotation)]
        char_status.equipped_ring = str_rotation[(idx + 2) % len(str_rotation)]
        char_status.equipped_amulet = str_rotation[(
            idx + 3) % len(str_rotation)]
        char_status.magic_shield_status = str_rotation[(
            idx + 4) % len(str_rotation)]

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
            view.set_char_status(char_status)
            view.add_log(
                f"This is log #{i} and it is very very long. Let us see.", -100)
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
            config_view.user_input = config_view.user_input[:len(
                config_view.user_input) - 1]
        else:
            config_view.signal_error()

    view = ConfigSelectionView(
        ['one', 'two', 'three', 'four', 'five'], update_cb)
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
    if layout == 'selection':
        stress_config_selection_view(cliwin)


if __name__ == '__main__':
    args = parser.parse_args()
    curses.wrapper(main, args.layout)
