#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui

from typing import Dict
from interface.macro.macro import ClientMacro
from interface.client_interface import ClientInterface, CommandType, CommandProcessor

parser = argparse.ArgumentParser(description="Loots all 9 SQMs around a char.")

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
    (LEFT_X, UPPER_Y),
    (CENTER_X, UPPER_Y),
    (RIGHT_X, UPPER_Y),
    (LEFT_X, CENTER_Y),
    (CENTER_X, CENTER_Y),
    (RIGHT_X, CENTER_Y),
    (LEFT_X, LOWER_Y),
    (CENTER_X, LOWER_Y),
    (RIGHT_X, LOWER_Y),
]


class LootMacro(ClientMacro):
    def __init__(
        self, client: ClientInterface, hotkeys: Dict[str, str] = {}, *args, **kwargs
    ):
        super().__init__(
            client,
            hotkey=hotkeys.get("loot"),
            command_type=CommandType.USE_ITEM,
            throttle_ms=250,
            *args,
            **kwargs,
        )

    def _client_action(self, tibia_wid):
        mouse_x, mouse_y = pyautogui.position()
        pyautogui.keyDown("altleft")
        for (sqm_x, sqm_y) in LOOT_SQMS:
            pyautogui.click(sqm_x, sqm_y, button="left", interval=0)
        pyautogui.keyUp("altleft")
        pyautogui.moveTo(mouse_x, mouse_y)


class MockLogger:
    def log_action(self, level, msg):
        print(str(level), msg)


def main(args):
    logger = MockLogger()
    cmd_processor = CommandProcessor("wid", logger, False)
    client = ClientInterface({}, logger, cmd_processor)
    macro = LootMacro(client, {"loot": "v"})
    cmd_processor.start()
    print(f"Listening on key v, 9 SQMs will be alt+clicked when pressed.")
    macro.hook_hotkey()
    try:
        print("Press [Enter] to exit.")
        keyboard.wait("enter")
    finally:
        cmd_processor.stop()
        macro.unhook_hotkey()


if __name__ == "__main__":
    main(parser.parse_args())
