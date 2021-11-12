#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time

from typing import Any, Callable, List, Tuple, Iterable
from threading import Lock
from tibia_terminator.schemas.item_crosshair_macro_config_schema import (
    ItemCrosshairMacroConfig,
    MacroAction,
    Direction,
)
from tibia_terminator.interface.macro.macro import (
    ClientMacro,
    UPPER_LEFT_SQM,
    UPPER_SQM,
    UPPER_RIGHT_SQM,
    LEFT_SQM,
    RIGHT_SQM,
    LOWER_LEFT_SQM,
    LOWER_SQM,
    LOWER_RIGHT_SQM,
)
from tibia_terminator.interface.client_interface import (
    ClientInterface,
    CommandType,
    CommandProcessor,
    ThrottleBehavior,
)
from tibia_terminator.interface.keystroke_sender import KeystrokeSender
from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig

parser = argparse.ArgumentParser(description="Test item cross hair macro.")
parser.add_argument(
    "--action",
    "-a",
    type=str,
    default=str(MacroAction.CLICK),
    choices=MacroAction._member_names_,
)
parser.add_argument(
    "keys", nargs="+", type=str, help="Keys to hook for crosshair macro."
)

OPPOSITE_DIRECTION_SQM_MAP = {
    Direction.LOWER_LEFT: UPPER_RIGHT_SQM,
    Direction.LEFT: RIGHT_SQM,
    Direction.UPPER_LEFT: LOWER_RIGHT_SQM,
    Direction.LOWER_RIGHT: UPPER_LEFT_SQM,
    Direction.RIGHT: LEFT_SQM,
    Direction.UPPER_RIGHT: LOWER_LEFT_SQM,
    Direction.UP: LOWER_SQM,
    Direction.DOWN: UPPER_SQM,
}

PYAUTOGUI_ITEM_CROSSHAIR_PAUSE = 5 / 1000  # 5 ms
# We want these to execute almost instantly, but not
# as fast as the keyboard can repeat itself.
SINGLE_ITEM_THROTTLE_MS = 50
SLEEP_BEFORE_CLICK_SEC = 5 / 1000


def gen_click_action_fn(hotkey: str, directional_lock: Lock, *args, **kwargs):
    # re-executing the keypress makes sure we don't issue a click
    # without a keypress and it does not affect client behavior

    def click_action(*args, **kwargs):
        # Make sure we only execute this command once at a time, otherwise
        # the character will walk into the rune target in race conditions.
        if directional_lock.acquire(blocking=False):
            prev_pause = pyautogui.PAUSE
            pyautogui.PAUSE = PYAUTOGUI_ITEM_CROSSHAIR_PAUSE
            try:
                pyautogui.press([hotkey])
                pyautogui.leftClick()
            finally:
                pyautogui.PAUSE = prev_pause
                directional_lock.release()

    return click_action


def gen_click_behind_fn(
    item_key: str,
    direction_key: str,
    direction: Direction,
    directional_lock: Lock,
    *args,
    **kwargs,
):
    # TODO: Use x_offset for this
    x, y = OPPOSITE_DIRECTION_SQM_MAP[direction]

    def click_behind(*args, **kwargs):
        if directional_lock.acquire(blocking=False):
            prev_pause = pyautogui.PAUSE
            pyautogui.PAUSE = PYAUTOGUI_ITEM_CROSSHAIR_PAUSE
            try:
                pyautogui.hotkey(item_key)
                pyautogui.leftClick(x, y)
            finally:
                pyautogui.PAUSE = prev_pause
                directional_lock.release()

    return click_behind


class SingleItemCrosshairMacro(ClientMacro):
    hotkey: str

    def __init__(
        self,
        client: ClientInterface,
        hotkey: str,
        action: Callable[[Tuple[Any, ...]], None],
        throttle_ms: int = SINGLE_ITEM_THROTTLE_MS,
        cmd_id: str = None,
        throttle_behavior=ThrottleBehavior.DROP,
    ):
        super().__init__(
            client,
            hotkey,
            CommandType.USE_ITEM,
            throttle_ms=throttle_ms,
            cmd_id=cmd_id or f"ITEM_CROSSHAIR_{hotkey}",
            throttle_behavior=throttle_behavior,
        )
        self.hotkey = hotkey
        self.__action = action

    def _client_action(self, tibia_wid):
        self.__action(tibia_wid)

    def hook_hotkey(self, *args, **kwargs):
        if self.hotkey_hook is None:
            # timeout parameter controls how long between each key in the
            # hotkey combination, default=1
            self.hotkey_hook = keyboard.add_hotkey(
                self.hotkey, self._action, timeout=0.5
            )

    def unhook_hotkey(self, *args, **kwargs):
        if self.hotkey_hook is not None:
            keyboard.remove_hotkey(self.hotkey_hook)
            self.hotkey_hook = None


class ItemCrosshairMacro:
    __macros: List[SingleItemCrosshairMacro]

    def __init__(
        self,
        client: ClientInterface,
        config: ItemCrosshairMacroConfig,
        hotkeys_config: HotkeysConfig,
    ):
        self.__macros = list(self.gen_macros(client, config, hotkeys_config))

    def gen_macros(
        self,
        client: ClientInterface,
        config: ItemCrosshairMacroConfig,
        hotkeys_config: HotkeysConfig,
    ) -> Iterable[SingleItemCrosshairMacro]:
        directional_lock = Lock()
        # Add the standard hotkey setup for when the character isn't moving
        yield SingleItemCrosshairMacro(
            client,
            config.hotkey,
            gen_click_action_fn(config.hotkey, directional_lock),
            config.throttle_ms,
        )

        direction_map = {
            hotkeys_config.up: Direction.UP,
            hotkeys_config.down: Direction.DOWN,
            hotkeys_config.left: Direction.LEFT,
            hotkeys_config.right: Direction.RIGHT,
            hotkeys_config.upper_left: Direction.UPPER_LEFT,
            hotkeys_config.upper_right: Direction.UPPER_RIGHT,
            hotkeys_config.lower_left: Direction.LOWER_LEFT,
            hotkeys_config.lower_right: Direction.LOWER_RIGHT,
        }

        # Add hooks for when the character is moving and pressing the hotkey
        # at the same time.
        for direction_key, direction in direction_map.items():
            hotkey = f"{config.hotkey}+{direction_key}"
            if config.action == MacroAction.CLICK:
                action = gen_click_action_fn(config.hotkey, directional_lock)
                yield SingleItemCrosshairMacro(
                    client, hotkey, action, config.throttle_ms
                )
            elif config.action == MacroAction.CLICK_BEHIND:
                action = gen_click_behind_fn(
                    config.hotkey, direction_key, direction, directional_lock
                )
                yield SingleItemCrosshairMacro(client, hotkey, action, config.throttle_ms)
            else:
                raise Exception(f"Unsupported action: {config.action}")

    def hook_hotkey(self, *args, **kwargs):
        for macro in self.__macros:
            macro.hook_hotkey(*args, **kwargs)

    def unhook_hotkey(self, *args, **kwargs):
        for macro in self.__macros:
            macro.unhook_hotkey(*args, **kwargs)


class MockLogger:
    def log_action(self, level, msg):
        print(str(level), msg)


class MockKeystrokeSender(KeystrokeSender):
    def send_key(self, key: str):
        pass


def main(keys: List[str], action: str):
    macros = []
    logger = MockLogger()
    action = MacroAction.from_str(action)
    cmd_processor = CommandProcessor("wid", logger, False)
    client = ClientInterface({}, MockKeystrokeSender(), logger, cmd_processor)
    hotkeys_config = HotkeysConfig(
        up="w",
        down="s",
        left="a",
        right="d",
        upper_left="q",
        upper_right="e",
        lower_left="z",
        lower_right="c",
        minor_heal="",
        medium_heal="",
        greater_heal="",
        haste="",
        equip_ring="",
        equip_amulet="",
        eat_food="",
        magic_shield="",
        cancel_magic_shield="",
        mana_potion="",
        toggle_emergency_amulet="",
        toggle_emergency_ring="",
        loot="",
        start_emergency="",
        cancel_emergency="",
    )
    cmd_processor.start()
    for key in keys:
        print(f"Listening on key {key}, a click will be issued when it is " "pressed.")
        macro = ItemCrosshairMacro(
            client,
            ItemCrosshairMacroConfig(
                hotkey=key,
                action=action,
            ),
            hotkeys_config=hotkeys_config,
        )
        macro.hook_hotkey()
        macros.append(macro)
    try:
        print("Press [Enter] to exit.")
        keyboard.wait("enter")
    finally:
        cmd_processor.stop()
        for macro in macros:
            macro.unhook_hotkey()


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.keys, args.action)
