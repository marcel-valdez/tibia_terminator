#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time
import sys

from macro import Macro

pyautogui.PAUSE = 0.02

parser = argparse.ArgumentParser(description='Test item cross hair macro.')


class ItemCrosshairMacro(Macro):
    def __init__(self, hotkey: str):
        super().__init__(hotkey)

    def _action(self):
        # Tibia will detect the key to trigger the crosshair and this macro
        # will actually trigger the mouse click, so it is all done in a single
        # action.
        pyautogui.click(button='left', interval=0)


def main(args):
    print('Macros with keys "r" and "shift+end" were added, test by pressing those'
          ' keys.')
    macro_r = ItemCrosshairMacro('r')
    macro_shift_end = ItemCrosshairMacro('shift+end')
    macro_r.hook_hotkey()
    macro_shift_end.hook_hotkey()
    try:
        print('Press [Enter] to exit.')
        keyboard.wait('enter')
    finally:
        macro_r.unhook_hotkey()
        macro_shift_end.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
