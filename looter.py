#!/usr/bin/env python3.8

import argparse
import subprocess
import time
import keyboard
from window_utils import get_tibia_wid
import pyautogui

pyautogui.PAUSE = 0.02

parser = argparse.ArgumentParser(
    description='Loots all 9 SQMs around a char.')
parser.add_argument('tibia_pid',
                    help='Tibia proceses identifier.')

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


class Looter():
    def __init__(self, hotkeys={}):
        self.loot_hotkey = hotkeys.get('loot')
        self.hotkey_hook = None

    def loot(self):
        pyautogui.keyDown('shiftleft')
        for (sqm_x, sqm_y) in LOOT_SQMS:
            pyautogui.click(sqm_x, sqm_y, button='right', interval=0)
        pyautogui.keyUp('shiftleft') # try shiftleft and shiftright

    def hook_hotkey(self, hotkey=None):
        if hotkey is None:
            if self.loot_hotkey is None:
              raise Exception("Please configure the loot hotkey.")
            else:
              hotkey = self.loot_hotkey

        self.unhook_hotkey()
        self.hotkey_hook = keyboard.add_hotkey(hotkey, self.loot)

    def unhook_hotkey(self):
        if self.hotkey_hook is not None:
            keyboard.remove_hotkey(self.hotkey_hook)
            self.hotkey_hook = None



def main(args):
    tibia_wid = get_tibia_wid(args.tibia_pid)
    looter = Looter(tibia_wid)
    print("Looting NOW!")
    looter.hook_hotkey('v')
    keyboard.wait('enter')
    looter.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
