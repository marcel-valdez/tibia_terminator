#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui

from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig
from tibia_terminator.interface.macro.macro import (
    ClientMacro, UPPER_LEFT_SQM, UPPER_SQM, UPPER_RIGHT_SQM, LEFT_SQM,
    CENTER_SQM, RIGHT_SQM, LOWER_LEFT_SQM, LOWER_SQM, LOWER_RIGHT_SQM)
from tibia_terminator.interface.client_interface import (ClientInterface,
                                                         CommandType,
                                                         CommandProcessor)

parser = argparse.ArgumentParser(description="Loots all 9 SQMs around a char.")

LEFT_BTN = "1"
RIGHT_BTN = "3"

LOOT_SQMS = [
    UPPER_LEFT_SQM,
    UPPER_SQM,
    UPPER_RIGHT_SQM,
    LEFT_SQM,
    CENTER_SQM,
    RIGHT_SQM,
    LOWER_LEFT_SQM,
    LOWER_SQM,
    LOWER_RIGHT_SQM,
]


class LootMacro(ClientMacro):
    def __init__(self, client: ClientInterface, hotkeys: HotkeysConfig, *args,
                 **kwargs):
        super().__init__(
            client,
            hotkey=hotkeys.loot,
            command_type=CommandType.USE_ITEM,
            throttle_ms=250,
            *args,
            **kwargs,
        )

    def _client_action(self, tibia_wid):
        mouse_x, mouse_y = pyautogui.position()
        # TODO: Make loot modifier a configurable value
        pyautogui.keyDown("altleft")
        for sqm_x, sqm_y in LOOT_SQMS:
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
    macro = LootMacro(client, HotkeysConfig(
        minor_heal="1", medium_heal="2", greater_heal="3", haste="4",
        equip_ring="5", equip_amulet="6", eat_food="7", magic_shield="8",
        cancel_magic_shield="9", mana_potion="0", toggle_emergency_amulet="a",
        toggle_emergency_ring="b", start_emergency="c", cancel_emergency="d",
        loot="v")
    )
    cmd_processor.start()
    print("Listening on key v, 9 SQMs will be alt+clicked when pressed.")
    macro.hook_hotkey()
    try:
        print("Press [Enter] to exit.")
        keyboard.wait("enter")
    finally:
        cmd_processor.stop()
        macro.unhook_hotkey()


if __name__ == "__main__":
    main(parser.parse_args())
