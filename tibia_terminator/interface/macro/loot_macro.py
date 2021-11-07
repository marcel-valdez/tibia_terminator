#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time

from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig
from tibia_terminator.interface.macro.macro import (
    ClientMacro,
    UPPER_LEFT_SQM,
    UPPER_SQM,
    UPPER_RIGHT_SQM,
    LEFT_SQM,
    CENTER_SQM,
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

parser = argparse.ArgumentParser(description="Loots all 9 SQMs around a char.")
pyautogui.PAUSE = 0.02
LEFT_BTN = "1"
RIGHT_BTN = "3"

LOOT_SQMS = [
    UPPER_LEFT_SQM,
    UPPER_SQM,
    UPPER_RIGHT_SQM,
    LEFT_SQM,
    RIGHT_SQM,
    LOWER_LEFT_SQM,
    LOWER_SQM,
    LOWER_RIGHT_SQM,
    CENTER_SQM,
    # Click one lsat time on the first SQM since if the cursos is in crosshair
    # that click will simply trigger the crosshair.
    UPPER_LEFT_SQM,
]

# Amount of time to wait after looting the 9 SQM before putting the cursor
# back in the original x,y
SLEEP_POST_LOOT_SEC = 25 / 1000 # 25 ms
LOOT_THROTTLE_MS = 375 # 375 ms
# Amount of time to wait to click on SQM after pressing the loot modifier
SLEEP_AFTER_MODIFIER_SEC = 5 / 1000  # 5 ms


class LootMacro(ClientMacro):
    def __init__(
        self,
        client: ClientInterface,
        hotkeys: HotkeysConfig,
        throttle_ms=LOOT_THROTTLE_MS,
        *args,
        **kwargs,
    ):
        super().__init__(
            client,
            hotkey=hotkeys.loot,
            command_type=CommandType.USE_ITEM,
            throttle_ms=throttle_ms,
            cmd_id="LOOT_CMD",
            # We want to drop the request in order to avoid multiple loot commands
            # stacking and making the character move around like a drunk.
            throttle_behavior=ThrottleBehavior.DROP,
            *args,
            **kwargs,
        )
        self.directional_keys = [
            hotkeys.up,
            hotkeys.down,
            hotkeys.left,
            hotkeys.right,
            hotkeys.upper_left,
            hotkeys.upper_right,
            hotkeys.lower_left,
            hotkeys.lower_right,
        ]
        self.loot_button = hotkeys.loot_button.lower()
        if hotkeys.loot_modifier:
            self.loot_modifier = f"{hotkeys.loot_modifier}left"
        else:
            self.loot_modifier = None

    def get_pressed_direction_key(self) -> str:
        for direction_key in self.directional_keys:
            if keyboard.is_pressed(direction_key):
                return direction_key

    def _client_action(self, tibia_wid):
        mouse_x, mouse_y = pyautogui.position()
        prev_pause = pyautogui.PAUSE
        pyautogui.PAUSE = 1 / 1000  # 1 ms
        pressed_direction_key = self.get_pressed_direction_key()
        try:
            if self.loot_modifier:
                pyautogui.keyDown(self.loot_modifier)

            for sqm_x, sqm_y in LOOT_SQMS:
                pyautogui.moveTo(sqm_x, sqm_y)
                if self.loot_modifier:
                    pyautogui.keyDown(self.loot_modifier)
                    time.sleep(SLEEP_AFTER_MODIFIER_SEC)
                pyautogui.click(sqm_x, sqm_y, button=self.loot_button)

            # This last sleep is to make sure the last click does happen
            # at the last SQM and shift key is still pressed.
            time.sleep(SLEEP_POST_LOOT_SEC)
            if pressed_direction_key:
                pyautogui.keyDown(pressed_direction_key)
            pyautogui.moveTo(mouse_x, mouse_y)
            if self.loot_modifier:
                pyautogui.keyUp(self.loot_modifier)
        finally:
            pyautogui.PAUSE = prev_pause


class MockLogger:
    def log_action(self, level, msg):
        print(str(level), msg)


def main(args):
    logger = MockLogger()
    cmd_processor = CommandProcessor("wid", logger, False)
    client = ClientInterface({}, logger, cmd_processor)
    macro = LootMacro(
        client,
        hotkeys=HotkeysConfig(
            minor_heal="1",
            medium_heal="2",
            greater_heal="3",
            haste="4",
            equip_ring="5",
            equip_amulet="6",
            eat_food="7",
            magic_shield="8",
            cancel_magic_shield="9",
            mana_potion="0",
            toggle_emergency_amulet="a",
            toggle_emergency_ring="b",
            start_emergency="c",
            cancel_emergency="d",
            loot="\\",
            up="w",
            down="s",
            left="a",
            right="d",
            upper_left="q",
            upper_right="e",
            lower_left="z",
            lower_right="c",
        ),
    )
    cmd_processor.start()
    print("Listening on key \\, 9 SQMs will be looted when pressed.")
    macro.hook_hotkey()
    try:
        print("Press [Enter] to exit.")
        keyboard.wait("enter")
    finally:
        cmd_processor.stop()
        macro.unhook_hotkey()


if __name__ == "__main__":
    main(parser.parse_args())
