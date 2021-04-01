#!/usr/bin/env python3.8

import sys
import argparse
import keyboard
import pyautogui

from typing import Dict
from tibia_terminator.schemas.item_crosshair_macro_config_schema import (
    ItemCrosshairMacroConfig, MacroAction, Direction)
from tibia_terminator.interface.macro.macro import (ClientMacro, parse_hotkey,
                                                    UPPER_LEFT_SQM, UPPER_SQM,
                                                    UPPER_RIGHT_SQM, LEFT_SQM,
                                                    RIGHT_SQM,
                                                    LOWER_LEFT_SQM, LOWER_SQM,
                                                    LOWER_RIGHT_SQM)
from tibia_terminator.interface.client_interface import (ClientInterface,
                                                         CommandType,
                                                         CommandProcessor)

parser = argparse.ArgumentParser(description='Test item cross hair macro.')
parser.add_argument("keys",
                    nargs='+',
                    type=str,
                    help="Keys to hook for crosshair macro.")


def click_action(hotkey: str, direction_map: Dict[str, Direction] = {}):
    # re-executing the keypress makes sure we don't issue a click
    # without a keypress and it does not affect client behavior
    pyautogui.press([hotkey])  # use interval=0.## to add a pause
    pyautogui.leftclick()


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


def click_behind(hotkey: str, direction_map: Dict[str, Direction]):
    parsed_hotkey = parse_hotkey(hotkey)
    direction = None
    keys = parsed_hotkey.to_list()
    direction_key = None
    for key in keys:
        if key in direction_map:
            direction_key = key
            direction = direction_map[key]
            break

    if direction is None:
        print(
            "Item crosshair macro triggered "
            f"unexpectedly by hotkey: {hotkey}",
            file=sys.stderr)
    else:
        x, y = OPPOSITE_DIRECTION_SQM_MAP[direction]
        rune_key = keys - [direction_key]
        pyautogui.hotkey(rune_key)
        pyautogui.leftClick(x, y)


ACTION_MAP = {
    MacroAction.CLICK: click_action,
    MacroAction.CLICK_BEHIND: click_behind
}


class ItemCrosshairMacro(ClientMacro):
    hotkey: str = None

    def __init__(self, client: ClientInterface,
                 config: ItemCrosshairMacroConfig):
        super().__init__(client, config.hotkey, CommandType.USE_ITEM, 125)
        self.hotkey = config.hotkey
        # TODO: We need to make this macro a composed macro for it to support
        # click behind.
        self.__direction_map = config.direction_map
        self.__action = ACTION_MAP[config.action]

    def _client_action(self, tibia_wid):
        self.__action(self.hotkey, self.__direction_map)


class MockLogger():
    def log_action(self, level, msg):
        print(str(level), msg)


def main(args):
    macros = []
    logger = MockLogger()
    cmd_processor = CommandProcessor('wid', logger, False)
    client = ClientInterface({}, logger, cmd_processor)
    cmd_processor.start()
    for key in args.keys:
        print(
            f'Listening on key {key}, a click will be issued when it is pressed.'
        )
        macro = ItemCrosshairMacro(client, key)
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
    main(parser.parse_args())
