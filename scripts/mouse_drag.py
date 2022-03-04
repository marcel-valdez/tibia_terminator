#!/usr/bin/env python3.8

from typing import Optional, Tuple

import time
import pyautogui


def drag(
    dest: Tuple[int, int],
    btn: str,
    duration_sec: float,
    orig: Optional[Tuple[int, int]],
) -> None:
    if orig:
        pyautogui.moveTo(*orig)

    time.sleep(0.01)  # Sleep 10 ms after moving mouse to origin
    pyautogui.dragTo(*dest, duration=duration_sec, button=btn)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", "--orig", required=False, type=int, nargs=2)
    parser.add_argument("--destination", "--dest", required=True, type=int, nargs=2)
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
        "--duration_sec",
        "--duration",
        help="How long the drag should take.",
        required=False,
        type=float,
        default=0.25,
    )

    def main(args: argparse.Namespace) -> None:
        pyautogui.PAUSE = 5 / 1000  # 5 ms
        drag(
            tuple(args.destination),
            args.button,
            args.duration_sec,
            tuple(args.origin) if args.origin else None
        )

    main(parser.parse_args())
