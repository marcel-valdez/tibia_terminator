#!/usr/bin/env python2.7

import subprocess
import time
import queue

from logger import (debug, get_debug_level, ActionLogEntry)
import threading


def timestamp_ms():
    return int(round(time.time() * 1000))


class Command():
    def __init__(self, throttle_key, throttle_ms, hotkey):
        self.throttle_key = throttle_key
        self.throttle_ms = throttle_ms
        self.hotkey = hotkey


class CommandSender(threading.Thread):
    def __init__(self, tibia_wid, logger, only_monitor):
        super().__init__(daemon=True)
        self.tibia_wid = tibia_wid
        self.cmd_queue = queue.Queue()
        self.stopped = False
        self.logger = logger
        self.only_monitor = only_monitor
        self.last_cmd = {}

    def send(self, command):
        self.cmd_queue.put(command)

    def stop(self):
        self.stopped = True

    def __send_keystroke(self, hotkey):
        subprocess.Popen([
            "/usr/bin/xdotool", "key", "--window",
            str(self.tibia_wid),
            str(hotkey)
        ])

    def __log_cmd(self, cmd):
        msg = f'[send_keystroke] {cmd.throttle_key} ({cmd.throttle_ms}): {cmd.hotkey}'
        self.logger.log_action(0, msg)

    def __throttle(self, throttle_key, throttle_ms=250):
        """Throttles an action by a given throttle_key.
        Returns:

            bool: False if the action should be throttled (not executed),
                    True otherwise.
        """
        return timestamp_ms() - self.last_cmd.get(throttle_key, 0) >= throttle_ms

    def run(self):
        while not self.stopped:
            if self.cmd_queue.qsize() > 0:
                cmd = self.cmd_queue.get()
                if self.__throttle(cmd.throttle_key, cmd.throttle_ms):
                    self.last_cmd[cmd.throttle_key] = timestamp_ms()
                    if not self.only_monitor:
                        self.__send_keystroke(cmd.hotkey)
                    self.__log_cmd(cmd)
            else:
                # sleep 10 ms
                time.sleep(0.01)


class ClientInterface:
    def __init__(self, hotkeys_config, cliwin, only_monitor=False, logger=None, cmd_sender=None):
        self.hotkeys_config = hotkeys_config
        self.only_monitor = only_monitor
        self.logger = logger
        self.cmd_sender = cmd_sender


    def send_keystroke_async(self, throttle_key, throttle_ms, hotkey):
        self.cmd_sender.send(
            Command(throttle_key, throttle_ms, hotkey))

    def cast_exura(self, throttle_ms):
        self.logger.log_action(2, f'cast_exura {throttle_ms} ms')
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura'])

    def cast_exura_gran(self, throttle_ms):
        self.logger.log_action(2, f'cast_exura_gran {throttle_ms} ms')
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_gran'])

    def cast_exura_sio(self, throttle_ms):
        self.logger.log_action(2, f'cast_exura_sio {throttle_ms} ms')
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_sio'])

    def drink_mana(self, throttle_ms):
        self.logger.log_action(2, f'drink_mana {throttle_ms} ms')
        self.send_keystroke_async('mana', throttle_ms,
                                  self.hotkeys_config['mana_potion'])

    def cast_haste(self, throttle_ms):
        self.logger.log_action(2, f'cast_haste {throttle_ms} ms')
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['utani_hur'])

    def equip_ring(self, throttle_ms=250):
        self.logger.log_action(2, f'equip_ring {throttle_ms} ms')
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['equip_ring'])

    def toggle_emergency_ring(self, throttle_ms=250):
        self.logger.log_action(2, f'toggle_emergency_ring {throttle_ms} ms')
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['toggle_emergency_ring'])

    def equip_amulet(self, throttle_ms=250):
        self.logger.log_action(2, f'equip_amulet {throttle_ms} ms')
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['equip_amulet'])

    def toggle_emergency_amulet(self, throttle_ms=250):
        self.logger.log_action(2, f'toggle_emergency_amulet {throttle_ms} ms')
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config[
                                      'toggle_emergency_amulet'])

    def eat_food(self, throttle_ms=250):
        self.logger.log_action(2, f'eat_food {throttle_ms} ms')
        self.send_keystroke_async('item_usage', throttle_ms,
                                  self.hotkeys_config['eat_food'])

    def cast_magic_shield(self, throttle_ms=250):
        self.logger.log_action(2, f'cast_magic_shield {throttle_ms} ms')
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['magic_shield'])

    def cancel_magic_shield(self, throttle_ms=250):
        self.logger.log_action(2, f'cancel_magic_shield {throttle_ms} ms')
        self.send_keystroke_async('utility_spell', throttle_ms,
                                  self.hotkeys_config['cancel_magic_shield'])
