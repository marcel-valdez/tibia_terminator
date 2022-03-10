#!/usr/bin/env python3.8


import math
import time

from threading import Lock
from typing import Tuple

import pyautogui

from tibia_terminator.schemas.drag_macro_config_schema import DragMacroConfig
from tibia_terminator.interface.macro.macro import ClientMacro
from tibia_terminator.interface.client_interface import (
    ClientInterface,
    CommandType,
    CommandProcessor,
    ThrottleBehavior,
)
from tibia_terminator.schemas.common import Direction


DRAG_THROTTLE_MS = 100
SQRT_TWO = math.sqrt(2.0)


def drag_relative(
    distance: int, direction: Direction, btn: str = "left", duration_ms: int = 100
) -> Tuple[int, int]:
    x_offset = 0
    y_offset = 0
    if direction is Direction.UP:
        y_offset = -distance
    elif direction is Direction.DOWN:
        y_offset = distance
    elif direction is Direction.RIGHT:
        x_offset = distance
    elif direction is Direction.LEFT:
        x_offset = -distance
    elif direction is Direction.UPPER_RIGHT:
        x_offset = int(distance / SQRT_TWO)
        y_offset = -x_offset
    elif direction is Direction.UPPER_LEFT:
        x_offset = -int(distance / SQRT_TWO)
        y_offset = x_offset
    elif direction is Direction.LOWER_RIGHT:
        x_offset = int(distance / SQRT_TWO)
        y_offset = x_offset
    elif direction is Direction.LOWER_LEFT:
        y_offset = int(distance / SQRT_TWO)
        x_offset = -y_offset

    if btn.lower() == "left":
        btn = pyautogui.PRIMARY
    elif btn.lower() == "right":
        btn = pyautogui.SECONDARY

    pyautogui.dragRel(
        xOffset=x_offset, yOffset=y_offset, duration=duration_ms / 1000, button=btn
    )

    return (x_offset, y_offset)


def _wait_for_mouse_pos(x: int, y: int, max_attempts=10) -> bool:
    poll_freq_ms = 2 / 1000  # 2 ms
    curr_x, curr_y = pyautogui.position()
    attempt_count = 1
    while curr_x != x and curr_y != y and attempt_count < max_attempts:
        time.sleep(poll_freq_ms)
        curr_x, curr_y = pyautogui.position()
        attempt_count += 1

    return curr_x == x and curr_y == y


class DragMacro(ClientMacro):
    def __init__(
        self,
        client: ClientInterface,
        config: DragMacroConfig,
        *args,
        **kwargs,
    ):
        super().__init__(
            client,
            config.hotkey,
            CommandType.USE_ITEM,
            config.throttle_ms or DRAG_THROTTLE_MS,
            *args,
            cmd_id="DRAG_CMD",
            throttle_behavior=ThrottleBehavior.DROP,
            **kwargs,
        )
        self.distance = config.distance
        self.direction = config.direction
        self.duration_ms = config.duration_ms
        self.btn = config.btn
        self.lock = Lock()

    def _do_drag(self):
        prev_pause = pyautogui.PAUSE
        pyautogui.PAUSE = 5 / 1000  # 5 ms
        try:
            curr_x, curr_y = pyautogui.position()
            x_offset, y_offset = drag_relative(
                self.distance, self.direction, self.btn, self.duration_ms
            )
            # return mouse to original position
            if _wait_for_mouse_pos(curr_x + x_offset, curr_y + y_offset):
                pyautogui.moveTo(curr_x, curr_y)
        finally:
            pyautogui.PAUSE = prev_pause

    def _client_action(self, tibia_wid):
        if self.lock.acquire(blocking=False):
            try:
                self._do_drag()
            finally:
                self.lock.release()


if __name__ == "__main__":
    import argparse
    import keyboard
    from tibia_terminator.interface.keystroke_sender import KeystrokeSender

    parser = argparse.ArgumentParser()
    parser.add_argument("--hotkey", "--key", required=True, type=str)
    parser.add_argument("--distance", "--dist", required=True, type=int)
    parser.add_argument(
        "--direction",
        "--dir",
        required=True,
        type=str,
        choices=Direction._member_names_,
    )
    parser.add_argument(
        "--duration_ms", "--duration", "--dur", required=False, type=int
    )
    parser.add_argument(
        "--button",
        "--btn",
        help="Mouse button to drag with.",
        choices=["left", "right"],
        required=False,
        default="left",
        type=str,
    )
    parser.add_argument(
        "--throttle_ms",
        "--throttle",
        help="Throttle maximum rate at which the command can be issued.",
        required=False,
        default=50,
        type=int
    )

    class MockLogger:
        def log_action(self, level, msg):
            print(str(level), msg)

    class MockKeystrokeSender(KeystrokeSender):
        def send_key(self, key: str):
            pass

    def main(args: argparse.Namespace) -> None:
        logger = MockLogger()
        direction = Direction.from_str(args.direction.upper())
        cmd_processor = CommandProcessor("wid", logger, False)
        client = ClientInterface(
            hotkeys_config={},
            keystroke_sender=MockKeystrokeSender(),
            logger=logger,
            cmd_processor=cmd_processor,
        )
        cmd_processor.start()
        try:
            macro = DragMacro(
                client,
                DragMacroConfig(
                    hotkey=args.hotkey,
                    distance=args.distance,
                    direction=direction,
                    btn=args.button,
                    duration_ms=args.duration_ms,
                    throttle_ms=args.throttle_ms
                ),
            )
            macro.hook_hotkey()
            print(
                f"Listening on key {args.hotkey}, a drag will be issued when it is pressed."
            )
            try:
                print("Press [Enter] to exit.")
                keyboard.wait("enter")
            finally:
                macro.unhook_hotkey()
        finally:
            cmd_processor.stop()

    main(parser.parse_args())
