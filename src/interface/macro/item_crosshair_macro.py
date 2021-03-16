#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time
import sys
import threading

from typing import Any, Callable, Dict

from interface.macro.macro import ClientMacro
from interface.client_interface import (
    ClientInterface, CommandType, CommandProcessor
)

parser = argparse.ArgumentParser(description='Test item cross hair macro.')
parser.add_argument("keys", nargs='+', type=str,
                    help="Keys to hook for crosshair macro.")

class ItemCrosshairMacro(ClientMacro):
    hotkey: str = None

    def __init__(self, client: ClientInterface, hotkey: str):
        super().__init__(client, hotkey, CommandType.USE_ITEM, 125)
        self.hotkey = hotkey

    def _client_action(self, tibia_wid):
        # re-executing the keypress makes sure we don't issue a click
        # without a keypress and it does not affect client behavior
        pyautogui.press([self.hotkey])  # use interval=0.## to add a pause
        pyautogui.leftClick()


class MockLogger():
    def log_action(self, level, msg):
        print(str(level), msg)

def main(args):
    macros = []
    logger = MockLogger()
    cmd_processor = CommandProcessor('wid', logger, False)
    client = ClientInterface({}, logger, cmd_processor)
    cmd_processor.start()
    for key in args.keys:
        print(f'Listening on key {key}, a click will be issued when it is pressed.')
        macro = ItemCrosshairMacro(client, key)
        macro.hook_hotkey()
        macros.append(macro)
    try:
        print('Press [Enter] to exit.')
        keyboard.wait('enter')
    finally:
        cmd_processor.stop()
        for macro in macros:
            macro.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
