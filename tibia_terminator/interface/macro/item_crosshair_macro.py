#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui

from typing import Any, Callable, List, Tuple, Iterable
from tibia_terminator.schemas.item_crosshair_macro_config_schema import (
    ItemCrosshairMacroConfig, MacroAction, Direction)
from tibia_terminator.interface.macro.macro import (ClientMacro,
                                                    UPPER_LEFT_SQM, UPPER_SQM,
                                                    UPPER_RIGHT_SQM, LEFT_SQM,
                                                    RIGHT_SQM, LOWER_LEFT_SQM,
                                                    LOWER_SQM, LOWER_RIGHT_SQM)
from tibia_terminator.interface.client_interface import (ClientInterface,
                                                         CommandType,
                                                         CommandProcessor)

parser = argparse.ArgumentParser(description='Test item cross hair macro.')
parser.add_argument("--action",
                    "-a",
                    type=str,
                    default=str(MacroAction.CLICK),
                    choices=MacroAction._member_names_)
parser.add_argument("keys",
                    nargs='+',
                    type=str,
                    help="Keys to hook for crosshair macro.")

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


def gen_click_action_fn(hotkey: str, *args, **kwargs):
    # re-executing the keypress makes sure we don't issue a click
    # without a keypress and it does not affect client behavior
    def click_action(*args, **kwargs):
        pyautogui.press([hotkey])  # use interval=0.## to add a pause
        pyautogui.leftClick()

    return click_action


def gen_click_behind_fn(item_key: str, direction_key: str,
                        direction: Direction, *args, **kwargs):
    x, y = OPPOSITE_DIRECTION_SQM_MAP[direction]

    def click_behind(*args, **kwargs):
        pyautogui.hotkey(item_key)
        pyautogui.leftClick(x, y)

    return click_behind


class SingleItemCrosshairMacro(ClientMacro):
    hotkey: str

    def __init__(self, client: ClientInterface, hotkey: str,
                 action: Callable[[Tuple[Any, ...]], None]):
        super().__init__(client, hotkey, CommandType.USE_ITEM, 125)
        self.hotkey = hotkey
        self.__action = action

    def _client_action(self, tibia_wid):
        self.__action(tibia_wid)

    def hook_hotkey(self, *args, **kwargs):
        if self.hotkey_hook is None:
            # timeout parameter controls how long between each key in the
            # hotkey combination, default=1
            self.hotkey_hook = keyboard.add_hotkey(self.hotkey,
                                                   self._action,
                                                   timeout=1)

    def unhook_hotkey(self, *args, **kwargs):
        if self.hotkey_hook is not None:
            keyboard.remove_hotkey(self.hotkey_hook)
            self.hotkey_hook = None


class ItemCrosshairMacro():
    __macros: List[SingleItemCrosshairMacro]

    def __init__(self, client: ClientInterface,
                 config: ItemCrosshairMacroConfig):
        self.__macros = list(self.gen_macros(client, config))

    def gen_macros(
        self, client: ClientInterface, config: ItemCrosshairMacroConfig
    ) -> Iterable[SingleItemCrosshairMacro]:
        if config.action == MacroAction.CLICK:
            action = gen_click_action_fn(config.hotkey)
            yield SingleItemCrosshairMacro(client, config.hotkey, action)
        elif config.action == MacroAction.CLICK_BEHIND:
            for direction_key, direction in config.direction_map.items():
                hotkey = f"{config.hotkey}+{direction_key}"
                action = gen_click_behind_fn(config.hotkey, direction_key,
                                             direction)
                yield SingleItemCrosshairMacro(client, hotkey, action)
        else:
            raise Exception(f"Unsupported action: {config.action}")

    def hook_hotkey(self, *args, **kwargs):
        for macro in self.__macros:
            macro.hook_hotkey(*args, **kwargs)

    def unhook_hotkey(self, *args, **kwargs):
        for macro in self.__macros:
            macro.unhook_hotkey(*args, **kwargs)


class MockLogger():
    def log_action(self, level, msg):
        print(str(level), msg)


def main(keys: List[str], action: str):
    macros = []
    logger = MockLogger()
    action = MacroAction.from_str(action)
    cmd_processor = CommandProcessor('wid', logger, False)
    client = ClientInterface({}, logger, cmd_processor)
    cmd_processor.start()
    for key in keys:
        print(f'Listening on key {key}, a click will be issued when it is '
              'pressed.')
        macro = ItemCrosshairMacro(
            client,
            ItemCrosshairMacroConfig(hotkey=key,
                                     action=action,
                                     direction_map={
                                         'e': Direction.UP,
                                         's': Direction.LEFT,
                                         'd': Direction.DOWN,
                                         'f': Direction.RIGHT
                                     }))
        macro.hook_hotkey()
        macros.append(macro)
    try:
        print('Press [Enter] to exit.')
        keyboard.wait('enter')
    finally:
        cmd_processor.stop()
        for macro in macros:
            macro.unhook_hotkey()


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.keys, args.action)
