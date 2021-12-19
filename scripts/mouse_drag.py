#!/usr/bin/env python3.8

from typing import Optional

import argparse
import pyautogui

parser = argparse.ArgumentParser()
parser.add_argument("--origin_x", "--orig_x", required=False, type=int)
parser.add_argument("--origin_y", "--orig_y", required=False, type=int)
parser.add_argument("--destination_x", "--dest_x", required=True, type=int)
parser.add_argument("--destination_y", "--dest_y", required=True, type=int)
parser.add_argument("--button",
                    "--btn",
                    help="Mouse button to drag with.",
                    choices=["left", "right"],
                    required=False,
                    default="left",
                    type=str)
parser.add_argument("--duration_sec",
                    "--duration",
                    help="How long the drag should take.",
                    required=False,
                    type=float,
                    default=0.25)


def main(orig_x: Optional[int], orig_y: Optional[int], dest_x: int,
         dest_y: int, btn: str, duration_sec: float) -> None:
    if orig_x and orig_y:
        pyautogui.moveTo(orig_x, orig_y)

    pyautogui.dragTo(dest_x, dest_y, duration=duration_sec, button=btn)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.origin_x, args.origin_y, args.destination_x, args.destination_y,
         args.button, args.duration_sec)
