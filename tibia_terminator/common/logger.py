#!/usr/bin/env python3.8

import os

global DEBUG_LEVEL
DEBUG_LEVEL = None


def init_debug_level():
    global DEBUG_LEVEL
    if DEBUG_LEVEL is None:
        DEBUG_LEVEL = os.getenv("DEBUG", -1)


def set_debug_level(debug_level):
    global DEBUG_LEVEL
    DEBUG_LEVEL = debug_level


def get_debug_level():
    global DEBUG_LEVEL
    return DEBUG_LEVEL


def debug(msg, debug_level=0):
    if get_debug_level() >= debug_level:
        print(msg)


class StatsEntry():
    def __init__(self, stats, prev_stats, equipment_status,
                 prev_equipment_status):
        self.stats = stats
        self.prev_stats = prev_stats
        self.equipment_status = equipment_status
        self.prev_equipment_status = prev_equipment_status


class ActionLogEntry():
    def __init__(self, debug_level, msg):
        self.debug_level = debug_level
        self.msg = msg


class LogEntry():
    def __init__(self, msg, row=0, col=0, end='\n'):
        self.msg = msg
        self.row = row
        self.col = col
        self.end = end


class StatsLogger():
    def __init__(self, run_view = None):
        self.run_view = run_view

    def log_action(self, debug_level: int, msg: str):
        if self.run_view:
            self.run_view.add_log(msg, debug_level)

    def set_debug_line_1(self, msg: str):
        if self.run_view:
            self.run_view.set_debug_line_1(msg)

    def set_debug_line_2(self, msg: str):
        if self.run_view:
            self.run_view.set_debug_line_2(msg)


if __name__ != "__main__":
    init_debug_level()
