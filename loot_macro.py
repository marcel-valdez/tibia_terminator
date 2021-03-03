#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui

from macro import Macro

parser = argparse.ArgumentParser(
    description='Loots all 9 SQMs around a char.')

LEFT_BTN = "1"
RIGHT_BTN = "3"

CENTER_Y = 385
CENTER_X = 960
SQM_LEN = 55


LEFT_X = CENTER_X - SQM_LEN
RIGHT_X = CENTER_X + SQM_LEN
UPPER_Y = CENTER_Y - SQM_LEN
LOWER_Y = CENTER_Y + SQM_LEN

LOOT_SQMS = [
    (LEFT_X, UPPER_Y),  (CENTER_X, UPPER_Y),  (RIGHT_X, UPPER_Y),
    (LEFT_X, CENTER_Y), (CENTER_X, CENTER_Y), (RIGHT_X, CENTER_Y),
    (LEFT_X, LOWER_Y),  (CENTER_X, LOWER_Y),  (RIGHT_X, LOWER_Y)
]


class LootMacro(Macro):
    def __init__(self, hotkeys={}):
        super().__init__(hotkeys.get('loot'), key_event_type='up')

    def _action(self):
        mouse_x, mouse_y = pyautogui.position()
        pyautogui.keyDown('altleft')
        for (sqm_x, sqm_y) in LOOT_SQMS:
            pyautogui.click(sqm_x, sqm_y, button='left', interval=0)
        pyautogui.keyUp('altleft')
        pyautogui.moveTo(mouse_x, mouse_y)


def main(args):
    macro = LootMacro({'loot': 'v'})
    macro.hook_hotkey()
    try:
        print("Press [Enter] to exit.")
        keyboard.wait('enter')
    finally:
        macro.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
