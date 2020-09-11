#!/usr/bin/env python2.7

import subprocess

from multiprocessing import Lock, Pool


class ClientInterface:
    def __init__(
            self,
            tibia_wid,
            hotkeys_config,
            process_pool=Pool(processes=6)):
        self.tibia_wid = tibia_wid
        self.hotkeys_config = hotkeys_config
        self.process_pool = process_pool
        self.last_cmd = {}
        self.locks = {
            'heal': Lock(),
            'speed': Lock(),
            'mana': Lock()
        }

    def throttle(self, key, throttle_ms=250):
        """Throttles an action by a given key.

        throttle has a side effect of refreshing the timestamp of the
        key passed in. So make sure to only use it if you're ACTUALLY
        going to execute the action being throttled.

        Returns:

            bool: False if the action should be throttled (not executed),
                  True otherwise.
        """

        timestamp = self.timestamp_millis()
        result = False
        if timestamp - self.last_cmd.get(key, 0) >= throttle_ms:
            self.locks[key].acquire(timeout=3)
            if timestamp - self.last_cmd.get(key, 0) >= throttle_ms:
                self.last_cmd[key] = timestamp
                result = True
            self.locks[key].release()

        return result

    def send_keystroke(self, throttle_key, throttle_ms, key):
        if self.throttle(throttle_key, throttle_ms):
            # asynchronously send the keystroke
            subprocess.Popen([
                "/usr/bin/xdotool", "key",
                "--window", str(self.tibia_wid),
                str(key)
            ])

    def send_keystroke_async(self, throttle_key, throttle_ms, key):
        self.process_pool.apply_async(self.send_keystroke,
                                      (self, throttle_key, throttle_ms, key))

    def cast_exura(self, throttle_ms):
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura'])

    def cast_exura_gran(self, throttle_ms):
        self.send_keystroke_async('heal',  throttle_ms,
                                  self.hotkeys_config['exura_gran'])

    def cast_exura_sio(self, throttle_ms):
        self.send_keystroke_async('heal', throttle_ms,
                                  self.hotkeys_config['exura_sio'])

    def drink_mana(self, throttle_ms):
        self.send_keystroke_async('mana', throttle_ms,
                                  self.hotkeys_config['mana_potion'])

    def cast_haste(self, throttle_ms):
        self.send_keystroke_async('speed', throttle_ms,
                                  self.hotkeys_config['utani_hur'])
