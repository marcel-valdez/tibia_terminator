#!/usr/bin/env python3.8
import argparse
import os
import subprocess
import time

from types import SimpleNamespace

parser = argparse.ArgumentParser(
    description=
    "Sends keystrokes efficiently by using a running xdotool process.")
parser.add_argument("wid", type=str, help="Window id to send keystrokes to.")
parser.add_argument("key", type=str, help="Key to send every 1 second")


class KeystrokeSender:
    def send_key(self, key: str) -> None:
        raise Exception("This needs to be implemented by a child class")


class XdotoolProcess:
    def __init__(self):
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(["/usr/bin/xdotool", "-"],
                                     text=True,
                                     encoding="UTF-8",
                                     stdin=subprocess.PIPE,
                                     universal_newlines=True)

    def stop(self):
        if self.is_running():
            self.proc.kill()

    def send_cmd(self, cmd: str) -> None:
        if not self.is_running():
            self.restart()

        self.proc.stdin.write(f'{cmd}{os.linesep}')
        self.proc.stdin.flush()

    def is_running(self) -> bool:
        return self.proc and self.proc.poll() is None

    def restart(self) -> None:
        if self.is_running():
            self.stop()
        self.start()


class XdotoolKeystrokeSender(KeystrokeSender):
    def __init__(self, xdotool_proc: XdotoolProcess, window_id: str):
        self.xdotool_proc = xdotool_proc
        self.window_id = window_id

    def send_key(self, key: str) -> None:
        self.xdotool_proc.send_cmd(f"key --window {self.window_id} {key}")


def main(args: argparse.Namespace):
    xdotool_proc = XdotoolProcess()
    xdotool_proc.start()
    try:
        print(f'xdotool_proc.is_running(): {xdotool_proc.is_running()}')
        sender = XdotoolKeystrokeSender(xdotool_proc, args.wid)
        while True:
            print("Sending key: " + args.key)
            sender.send_key(args.key)
            time.sleep(1)
    finally:
        xdotool_proc.stop()


if __name__ == "__main__":
    main(parser.parse_args())
