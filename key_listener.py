#!/usr/bin/env python3.8

import keyboard
import pyautogui

pyautogui.PAUSE = 0.02


class KeyListener():
    def __init__(self, hotkey):
        self.hotkey = hotkey
        self.hotkey_hook = None

    def __action(self, event):
        self._action()

    def _action(self, event):
        pass

    def hook_hotkey(self, hotkey=None):
        if hotkey is None:
            if self.hotkey is None:
                raise Exception("Please provide a hotkey for the macro.")
            else:
                hotkey = self.hotkey

        self.unhook_hotkey()
        self.hotkey_hook = keyboard.on_press_key(hotkey, self.__action)

    def unhook_hotkey(self):
        if self.hotkey_hook is not None:
            keyboard.remove_hotkey(self.hotkey_hook)
            self.hotkey_hook = None
