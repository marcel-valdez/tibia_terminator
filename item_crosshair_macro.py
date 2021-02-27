#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time
import sys

from key_listener import KeyListener

pyautogui.PAUSE = 0.02

parser = argparse.ArgumentParser(description='Test item cross hair macro.')


LEFT_BTN = "1"
RIGHT_BTN = "3"


class ItemCrosshairMacro(KeyListener):
    def __init__(self, hotkey):
        super().__init__(hotkey)

    def _action(self):
        # Tibia will detect the key to trigger the crosshair and this macro
        # will actually trigger the mouse click, so it is all done in a single
        # action.

        print(f'Macro {self.hotkey} triggered', file=sys.stderr)
        pyautogui.click(button='left', interval=0)


def main(args):
    print('Macros with keys "r" and "f" were added, test by pressing those'
          ' keys.')
    macroR = ItemCrosshairMacro('r')
    macroF = ItemCrosshairMacro('f')
    macroR = macroR.hook_hotkey()
    macroF = macroF.hook_hotkey()
    try:
        print('Press [Enter] to exit.')
        keyboard.wait('enter')
    finally:
        macroR.unhook_hotkey()
        macroF.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
