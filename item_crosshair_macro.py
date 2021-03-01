#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time
import sys
import threading

from typing import Any, Dict
from macro import Macro

parser = argparse.ArgumentParser(description='Test item cross hair macro.')
parser.add_argument("keys", nargs='+', type=str,
                    help="Keys to hook for crosshair macro.")

class ItemCrosshairMacro(Macro):
    class_lock: threading.Lock = threading.Lock()
    last_click_ts_ms: int = 0
    __hotkey: str = None

    def __init__(self, hotkey: str):
        super().__init__(hotkey)
        self.__hotkey = hotkey

    def _action(self):
        # Tibia will detect the key to trigger the crosshair and this macro
        # will actually trigger the mouse click, so it is all done in a single
        # action.
        self.__class__.click()

    @classmethod
    def click(cls):
        if not cls.class_lock.locked() and cls.time_since_click_ms() >= 100:
            cls.class_lock.acquire()
            try:
                cls.last_click_ts_ms = time.time() * 1000
                pyautogui.leftClick()
            finally:
                cls.class_lock.release()

    @classmethod
    def time_since_click_ms(cls):
        return (time.time() * 1000) - cls.last_click_ts_ms


def main(args):
    macros = []
    for key in args.keys:
        print(f'Listening on key {key}, a click will be issued when it is pressed.')
        macro = ItemCrosshairMacro(key)
        macro.hook_hotkey()
        macros.append(macro)
    try:
        print('Press [Enter] to exit.')
        keyboard.wait('enter')
    finally:
        for macro in macros:
            macro.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
