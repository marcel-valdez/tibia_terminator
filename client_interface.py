#!/usr/bin/env python2.7

import subprocess
import time

from multiprocessing import Lock, Pool
from logger import debug, get_debug_level


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
    debug(
        '[send_keystroke] ' + throttle_key + ' (' + str(throttle_ms) + '): ' +
        hotkey, 0)
    # asynchronously send the keystroke
    if not ponly_monitor:
        subprocess.Popen([
            "/usr/bin/xdotool", "key", "--window",
            str(tibia_wid),
            str(hotkey)
        ])


def proc_init(locks, only_monitor, last_cmd):
    global ponly_monitor
    ponly_monitor = only_monitor
    global plocks
    plocks = locks
    global plast_cmd
    plast_cmd = last_cmd


class ClientInterface:
    def __init__(self, tibia_wid, hotkeys_config, only_monitor=False):
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
        self.process_pool = Pool(
            processes=6,
            initargs=[self.locks, self.only_monitor, self.last_cmd],
            initializer=proc_init)

    def send_keystroke_async(self, throttle_key, throttle_ms, hotkey):
        if throttle(self.last_cmd, self.locks, throttle_key, throttle_ms):
            f = self.process_pool.apply_async(
                send_keystroke,
                (self.tibia_wid, throttle_key, throttle_ms, hotkey))
            if get_debug_level() >= 0:
                f.get()

    def cast_exura(self, throttle_ms):
        debug('cast_exura' + str(throttle_ms), 2)
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura'])

    def cast_exura_gran(self, throttle_ms):
        debug('cast_exura_gran' + str(throttle_ms), 2)
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_gran'])

    def cast_exura_sio(self, throttle_ms):
        debug('cast_exura_sio' + str(throttle_ms), 2)
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_sio'])

    def drink_mana(self, throttle_ms):
        debug('drink_mana' + str(throttle_ms), 2)
        self.send_keystroke_async('mana', throttle_ms,
                                  self.hotkeys_config['mana_potion'])

    def cast_haste(self, throttle_ms):
        debug('cast_haste' + str(throttle_ms), 2)
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['utani_hur'])

    def equip_ring(self, throttle_ms=250):
        debug('equip_ring' + str(throttle_ms), 2)
        self.send_keystroke_async('item_usage', throttle_ms,
            self.hotkeys_config['equip_ring'])

    def equip_amulet(self, throttle_ms=250):
        debug('equip_amulet' + str(throttle_ms), 2)
        self.send_keystroke_async('item_usage', throttle_ms,
            self.hotkeys_config['equip_amulet'])

    def eat_food(self, throttle_ms=250):
        debug('eat_food' + str(throttle_ms), 2)
        self.send_keystroke_async('item_usage', throttle_ms,
            self.hotkeys_config['eat_food'])

    def cast_magic_shield(self, throttle_ms=250):
        debug('cast_magic_shield' + str(throttle_ms), 2)
        self.send_keystroke_async('utility_spell', throttle_ms,
            self.hotkeys_config['magic_shield'])