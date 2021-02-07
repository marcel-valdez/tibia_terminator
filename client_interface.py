#!/usr/bin/env python2.7

import subprocess
import time

from multiprocessing import Lock, Pool
from logger import debug, get_debug_level


LOG_ROW = 8
LOG_BUFFER_COUNTER = 0
MAX_LOG_BUFFER = 10

class WinLogger():
    CLEAR =  (' ' * 40 + '\n') * 11
    def __init__(self, log_row=LOG_ROW):
        self.log_buffer_counter = 0
        self.log_row = log_row
        self.logs = []

    def log(self, cliwin, debug_level, msg):
        if get_debug_level() >= debug_level:
            row = self.log_row
            cliwin.move(row, 0)
            cliwin.clrtobot()
            cliwin.addstr(row, 0, 'Log Entries')
            if len(self.logs) > MAX_LOG_BUFFER:
                self.logs.pop(0)
            self.logs.append(msg)
            rowi = row
            for log in self.logs:
                cliwin.move(rowi + 1, 0)
                cliwin.insstr(log)
                rowi += 1



LOGGER = WinLogger(log_row=LOG_ROW)

def winlog(cliwin, winlog_level, msg):
    LOGGER.log(cliwin, winlog_level, msg)

class LogEntry:
    def __init__(self, log_level, msg):
        self.log_level = log_level
        self.msg = msg


def timestamp_millis():
    return int(round(time.time() * 1000))


def throttle(last_cmd, locks, key, throttle_ms=250):
    """Throttles an action by a given key.

    throttle has a side effect of refreshing the timestamp of the
    key passed in. So make sure to only use it if you're ACTUALLY
    going to execute the action being throttled.

    Returns:

        bool: False if the action should be throttled (not executed),
                True otherwise.
    """

    timestamp = timestamp_millis()
    result = False
    debug('[throttle] start', 3)
    if timestamp - last_cmd.get(key, 0) >= throttle_ms:
        debug('[throttle] acquiring lock', 3)
        locks[key].acquire(timeout=3)
        if timestamp - last_cmd.get(key, 0) >= throttle_ms:
            last_cmd[key] = timestamp
            result = True
        debug('[throttle] releasing lock', 3)
        locks[key].release()

    return result


def send_keystroke(tibia_wid, throttle_key, throttle_ms, hotkey):
    # asynchronously send the keystroke
    if not ponly_monitor:
        subprocess.Popen([
            "/usr/bin/xdotool", "key", "--window",
            str(tibia_wid),
            str(hotkey)
        ])
        return LogEntry(0, '[send_keystroke] ' + throttle_key + ' (' + str(throttle_ms) + '): ' +
                        hotkey)


def proc_init(locks, only_monitor, last_cmd, logs):
    global ponly_monitor
    ponly_monitor = only_monitor
    global plocks
    plocks = locks
    global plast_cmd
    plast_cmd = last_cmd


class ClientInterface:
    def __init__(self, tibia_wid, hotkeys_config, cliwin, only_monitor=False):
        self.tibia_wid = tibia_wid
        self.hotkeys_config = hotkeys_config
        self.last_cmd = {}
        self.only_monitor = only_monitor
        self.locks = {
            'heal': Lock(),
            'utility_spell': Lock(),
            'mana': Lock(),
            'item_usage': Lock()
        }
        self.cliwin = cliwin
        self.logs = []
        self.process_pool = Pool(
            processes=6,
            initargs=[self.locks, self.only_monitor, self.last_cmd, self.logs],
            initializer=proc_init)

    def send_keystroke_async(self, throttle_key, throttle_ms, hotkey):
        if throttle(self.last_cmd, self.locks, throttle_key, throttle_ms):
            f = self.process_pool.apply_async(
                send_keystroke,
                (self.tibia_wid, throttle_key, throttle_ms, hotkey))
            log_entry = f.get()
            if log_entry is not None:
                winlog(self.cliwin, log_entry.log_level, log_entry.msg)


    def cast_exura(self, throttle_ms):
        winlog(self.cliwin, 2, 'cast_exura' + str(throttle_ms))
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura'])

    def cast_exura_gran(self, throttle_ms):
        winlog(self.cliwin, 2, 'cast_exura_gran' + str(throttle_ms))
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_gran'])

    def cast_exura_sio(self, throttle_ms):
        winlog(self.cliwin, 2, 'cast_exura_sio' + str(throttle_ms))
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_sio'])

    def drink_mana(self, throttle_ms):
        winlog(self.cliwin, 2, 'drink_mana' + str(throttle_ms))
        self.send_keystroke_async('mana', throttle_ms,
                                  self.hotkeys_config['mana_potion'])

    def cast_haste(self, throttle_ms):
        winlog(self.cliwin, 2, 'cast_haste' + str(throttle_ms))
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['utani_hur'])

    def equip_ring(self, throttle_ms=250):
        winlog(self.cliwin, 2, 'equip_ring' + str(throttle_ms))
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['equip_ring'])

    def equip_amulet(self, throttle_ms=250):
        winlog(self.cliwin, 2, 'equip_amulet' + str(throttle_ms))
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['equip_amulet'])

    def eat_food(self, throttle_ms=250):
        winlog(self.cliwin, 2, 'eat_food' + str(throttle_ms))
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['eat_food'])

    def cast_magic_shield(self, throttle_ms=250):
        winlog(self.cliwin, 2, 'cast_magic_shield' + str(throttle_ms))
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['magic_shield'])

    def cancel_magic_shield(self, throttle_ms=250):
        winlog(self.cliwin, 2, 'cancel_magic_shield' + str(throttle_ms))
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['cancel_magic_shield'])
