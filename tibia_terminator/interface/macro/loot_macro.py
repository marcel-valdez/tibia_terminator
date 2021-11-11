#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import time

from threading import Lock

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
from tibia_terminator.interface.keystroke_sender import (
    KeystrokeSender
)

parser = argparse.ArgumentParser(description="Loots all 9 SQMs around a char.")
pyautogui.PAUSE = 0.02
LEFT_BTN = "1"
RIGHT_BTN = "3"

LOOT_SQMS = [
    # We press ourselves first to avoid opening bodies or interacting with stuff
    CENTER_SQM,
    UPPER_LEFT_SQM,
    UPPER_SQM,
    UPPER_RIGHT_SQM,
    LEFT_SQM,
    RIGHT_SQM,
    LOWER_LEFT_SQM,
    LOWER_SQM,
    LOWER_RIGHT_SQM,
    # Click one lsat time on the first SQM since if the cursor is in crosshair
    # that click will simply trigger the crosshair.
    # Also we leave the cursor on ourselves to avoid accidentally moving.
    CENTER_SQM,
]
LEN_LOOT_SQMS = len(LOOT_SQMS)

# (unused) Amount of time to wait after looting the 9 SQM before putting the cursor
# back in the original x,y
SLEEP_POST_LOOT_SEC = 25 / 1000
LOOT_THROTTLE_MS = 375
# (unused) Pause before returning the cursor to the previous position
PAUSE_BEFORE_RETURN_SEC = 62.5 / 1000
# Amount of time to wait to click on SQM after pressing the loot modifier
SLEEP_LOOT_MODIFIER_SEC = 10 / 1000
# Pause in between pyautogui commands
PYAUTOGUI_LOOT_PAUSE_SEC = 2 / 1000


class LootMacro(ClientMacro):
    def __init__(
        self,
        client: ClientInterface,
        hotkeys: HotkeysConfig,
        # X offset of the Tibia window with respect to 0,0 (upper left corner)
        # in dual monitor setups, this is normally the width in pixeld of the
        # monitor to the left
        x_offset: int = 0,
        throttle_ms: int = LOOT_THROTTLE_MS,
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
        self.x_offset = x_offset
        self.lock = Lock()

    def get_pressed_direction_key(self) -> str:
        for direction_key in self.directional_keys:
            if keyboard.is_pressed(direction_key):
                return direction_key

    def _wait_for_mouse_pos(self, x: int, y: int, max_attempts = 10) -> bool:
        poll_freq = 1 / 1000 # 0.1 ms
        curr_x, curr_y = pyautogui.position()
        attempt_count = 1
        while curr_x != x and curr_y != y and attempt_count < max_attempts:
            time.sleep(poll_freq)
            curr_x, curr_y = pyautogui.position()
            attempt_count += 1

        return curr_x == x and curr_y == y

    def _do_loot(self):
        prev_pause = pyautogui.PAUSE
        pyautogui.PAUSE = PYAUTOGUI_LOOT_PAUSE_SEC
        pressed_direction_key = self.get_pressed_direction_key()
        try:
            if self.loot_modifier:
                pyautogui.keyDown(self.loot_modifier)
                time.sleep(SLEEP_LOOT_MODIFIER_SEC)
            for sqm_x, sqm_y in LOOT_SQMS:
                sqm_x += self.x_offset
                pyautogui.moveTo(sqm_x, sqm_y)
                # We only want to wait on the *last* sqm
                if self._wait_for_mouse_pos(sqm_x, sqm_y):
                    pyautogui.click(button=self.loot_button)

            if self.loot_modifier:
                pyautogui.keyUp(self.loot_modifier)
                time.sleep(SLEEP_LOOT_MODIFIER_SEC)
            if pressed_direction_key:
                pyautogui.keyDown(pressed_direction_key)
        finally:
            pyautogui.PAUSE = prev_pause


    def _client_action(self, tibia_wid):
        if self.lock.acquire(blocking=False):
            try:
                self._do_loot()
            finally:
                self.lock.release()


class MockLogger:
    def log_action(self, level, msg):
        print(str(level), msg)


class MockKeystrokeSender(KeystrokeSender):
    def send_key(self, key: str):
        pass

def main(args):
    logger = MockLogger()
    cmd_processor = CommandProcessor("wid", logger, False)
    client = ClientInterface(
        {},
        MockKeystrokeSender(),
        logger,
        cmd_processor
    )
    macro = LootMacro(
        client,
        hotkeys=HotkeysConfig(
            loot="\\",
            loot_button="left",
            loot_modifier="shift",
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
