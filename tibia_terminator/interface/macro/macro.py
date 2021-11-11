#!/usr/bin/env python3.8

import keyboard
import pyautogui

from typing import List, Set, Dict, NamedTuple
from keyboard import KeyboardEvent

from tibia_terminator.interface.client_interface import (
    ClientInterface,
    ThrottleBehavior,
)

pyautogui.PAUSE = 0.02

CENTER_Y = 385
CENTER_X = 960
SQM_LEN = 55

LEFT_X = CENTER_X - SQM_LEN
RIGHT_X = CENTER_X + SQM_LEN
UPPER_Y = CENTER_Y - SQM_LEN
LOWER_Y = CENTER_Y + SQM_LEN

UPPER_LEFT_SQM = (LEFT_X, UPPER_Y)
UPPER_SQM = (CENTER_X, UPPER_Y)
UPPER_RIGHT_SQM = (RIGHT_X, UPPER_Y)
LEFT_SQM = (LEFT_X, CENTER_Y)
CENTER_SQM = (CENTER_X, CENTER_Y)
RIGHT_SQM = (RIGHT_X, CENTER_Y)
LOWER_LEFT_SQM = (LEFT_X, LOWER_Y)
LOWER_SQM = (CENTER_X, LOWER_Y)
LOWER_RIGHT_SQM = (RIGHT_X, LOWER_Y)


class Hotkey(NamedTuple):
    key: str
    modifiers: List[str] = []

    def __str__(self):
        return "+".join(self.modifiers + [self.key])

    def to_list(self):
        return self.modifiers + [self.key]


def parse_hotkey(hotkey: str) -> Hotkey:
    modifiers = []
    while "+" in hotkey:
        modifier_idx = hotkey.index("+")
        modifiers.append(hotkey[:modifier_idx])
        hotkey = hotkey[modifier_idx + 1 :]
    return Hotkey(hotkey, modifiers)


def to_issuable(hotkey: Hotkey) -> Hotkey:
    issuable_modifiers = []
    for modifier in hotkey.modifiers:
        if modifier in ("ctrl", "shift", "alt"):
            modifier = f"{modifier}left"
        issuable_modifiers.append(modifier)
    return Hotkey(hotkey.key, issuable_modifiers)


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
            hotkey = hotkey[modifier_idx + 1 :]

        return (set(modifiers), hotkey)

    def hook_hotkey(self, hotkey=None):
        if hotkey is None:
            if self.key is None:
                raise Exception("Please provide a hotkey for the macro.")
            else:
                hotkey = self.key

        # Do nothing if we're already hooked
        if self.hotkey_hook is None:
            Macro.key_macro_count[hotkey] = Macro.key_macro_count.get(hotkey, 0) + 1
            self.hotkey_hook = keyboard.hook_key(hotkey, self.__action, self.suppress)

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
                if self.__action in store[scan_code]:
                    store[scan_code].remove(self.__action)
            self.hotkey_hook = None


class ClientMacro(Macro):
    client: ClientInterface = None
    hotkey: str = None
    command_type: str = None
    throttle_ms: int = None
    cmd_id: str = None

    def __init__(
        self,
        client: ClientInterface,
        hotkey: str,
        command_type: str,
        throttle_ms: int,
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
        *args,
        **kwargs,
    ):
        super().__init__(hotkey, *args, **kwargs)
        self.client = client
        self.hotkey = hotkey
        self.command_type = command_type
        self.throttle_ms = throttle_ms
        self.throttle_behavior = throttle_behavior
        self.cmd_id = cmd_id

    def _client_action(self, tibia_wid):
        raise Exception("This should be implemented by the child class")

    def _action(self):
        self.client.execute_macro(
            macro_fn=self._client_action,
            cmd_type=self.command_type,
            throttle_ms=self.throttle_ms,
            cmd_id=self.cmd_id,
            throttle_behavior=self.throttle_behavior
        )
