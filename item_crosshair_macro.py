#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time
import sys

from macro import Macro

parser = argparse.ArgumentParser(description='Test item cross hair macro.')
parser.add_argument("keys", nargs='+', type=str,
                    help="Keys to hook for crosshair macro.")


class ItemCrosshairMacro(Macro):
    def __init__(self, hotkey: str):
        super().__init__(hotkey)

    def _action(self):
        # Tibia will detect the key to trigger the crosshair and this macro
        # will actually trigger the mouse click, so it is all done in a single
        # action.
        pyautogui.click(button='left', interval=0)


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
