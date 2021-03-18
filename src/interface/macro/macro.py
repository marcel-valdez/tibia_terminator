#!/usr/bin/env python3.8

import keyboard
import pyautogui

from typing import List, Set, Dict
from keyboard import KeyboardEvent

from interface.client_interface import ClientInterface

pyautogui.PAUSE = 0.02


class Macro:
    key_macro_count: Dict[str, int] = {}
    modifiers: Set = None
    key: str = None
    hotkey_hook = None

    def __init__(self, hotkey: str, key_event_type="up", suppress=False):
        self.modifiers, self.key = self.__parse_hotkey(hotkey)
        self.hotkey_hook = None
        self.key_event_type = key_event_type
        self.suppress = suppress

    def __action(self, event: KeyboardEvent):
        if event.event_type != self.key_event_type:
            return

        if len(self.modifiers) == 0 and len(event.modifiers) > 0:
            return

        if self.modifiers.issubset(set(event.modifiers or [])):
            self._action()

    def _action(self, event: KeyboardEvent):
        pass

    def __parse_hotkey(self, hotkey: str) -> (List[str], str):
        modifiers = []
        while "+" in hotkey:
            modifier_idx = hotkey.index("+")
            modifiers.append(hotkey[:modifier_idx])
            hotkey = hotkey[modifier_idx + 1:]

        return (set(modifiers), hotkey)

    def hook_hotkey(self, hotkey=None):
        if hotkey is None:
            if self.key is None:
                raise Exception("Please provide a hotkey for the macro.")
            else:
                hotkey = self.key

        # Do nothing if we're already hooked
        if self.hotkey_hook is None:
            Macro.key_macro_count[hotkey] = Macro.key_macro_count.get(
                hotkey, 0) + 1
            self.hotkey_hook = keyboard.hook_key(hotkey, self.__action,
                                                 self.suppress)

    def unhook_hotkey(self):
        if self.hotkey_hook is not None:
            Macro.key_macro_count[self.key] -= 1
            # Fragile: Based on remove_ function from hook_key
            # Remove own listener
            del keyboard._hooks[self.__action]
            # Remove the hotkey remover
            del keyboard._hooks[self.hotkey_hook]
            # Only remove the global key hook if nobody else is listening.
            # This is the code that keyboard didn't support.
            if Macro.key_macro_count[self.key] == 0:
                del keyboard._hooks[self.key]
            # Remove self from scancode listener
            scan_codes = keyboard.key_to_scan_codes(self.key)
            # Important: If we ever supress keys, we need to use
            #  _listener.blocking_keys instead.
            store = keyboard._listener.nonblocking_keys
            for scan_code in scan_codes:
                store[scan_code].remove(self.__action)
            self.hotkey_hook = None


class ClientMacro(Macro):
    client: ClientInterface = None
    hotkey: str = None
    command_type: str = None
    throttle_ms: int = None

    def __init__(self, client: ClientInterface, hotkey: str, command_type: str,
                 throttle_ms: int, *args, **kwargs):
        super().__init__(hotkey, *args, **kwargs)
        self.client = client
        self.hotkey = hotkey
        self.command_type = command_type
        self.throttle_ms = throttle_ms

    def _client_action(self, tibia_wid):
        raise Exception("This should be implemented by the child class")

    def _action(self):
        # Tibia will detect the key to trigger the action and this macro
        # will actually trigger the mouse click, so it is all done in a
        # single action.
        self.client.execute_macro(self._client_action,
                                  self.command_type,
                                  throttle_ms=self.throttle_ms)
