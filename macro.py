#!/usr/bin/env python3.8

import keyboard
import pyautogui

from typing import List, Set

from keyboard import KeyboardEvent

pyautogui.PAUSE = 0.02


class Macro():
    modifiers: Set = None
    key: str = None
    hotkey_hook = None

    def __init__(self, hotkey: str):
        self.modifiers, self.key = self.__parse_hotkey(hotkey)
        self.hotkey_hook = None

    def __action(self, event: KeyboardEvent):
        if self.modifiers.issubset(set(event.modifiers or [])):
            self._action()

    def _action(self, event: KeyboardEvent):
        pass

    def __parse_hotkey(self, hotkey: str) -> (List[str], str):
        modifiers = []
        while '+' in hotkey:
            modifier_idx = hotkey.index('+')
            modifiers.append(hotkey[:modifier_idx])
            hotkey = hotkey[modifier_idx+1:]

        return (set(modifiers), hotkey)

    def hook_hotkey(self, hotkey=None):
        if hotkey is None:
            if self.key is None:
                raise Exception("Please provide a hotkey for the macro.")
            else:
                hotkey = self.key

        self.unhook_hotkey()
        self.hotkey_hook = keyboard.on_press_key(hotkey, self.__action)

    def unhook_hotkey(self):
        if self.hotkey_hook is not None:
            keyboard.unhook(self.hotkey_hook)
            self.hotkey_hook = None
