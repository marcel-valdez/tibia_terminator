#!/usr/bin/env python3.8

import argparse
import time
from pynput import (mouse, keyboard)

parser = argparse.ArgumentParser(description="Loots all 9 SQMs around a char.")

def click_reporter():
    keys = {
        "shift": False
    }

    def on_press(key):
        if key == keyboard.Key.shift:
            keys["shift"] = True

    def on_release(key):
        if key == keyboard.Key.shift:
            keys["shift"] = False

    def on_click(x, y, button, pressed):
        if pressed:
            print(f"btn: {button}, pos: ({x},{y}), pressed: {pressed}, shift? {keys['shift']}")

    with mouse.Listener(
            on_click=on_click
    ) as mouse_listener:
        with keyboard.Listener(
                on_press=on_press,
                on_release=on_release
        ) as keyboard_listener:
            mouse_listener.join()
            keyboard_listener.join()

def main(*args):
    click_reporter()

if __name__ == "__main__":
    main(parser.parse_args())
