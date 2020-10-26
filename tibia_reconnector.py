#!/usr/bin/env python2.7
"""Reconnects to the first character of the tibia client."""

import os
import argparse
import time
from credentials import CREDENTIALS
from window_utils import (
    get_tibia_wid, focus_tibia, ScreenReader, send_key, send_text, left_click,
    get_pixel_color_slow
)

parser = argparse.ArgumentParser(
    description='Tibia reconnector'
)
parser.add_argument(
    'pid', help='The PID of Tibia.'
)
parser.add_argument(
    '--credentials_profile', help='Name of the credentials profile to use.',
    type=str
)
parser.add_argument(
    '--check_if_ingame',
    help='Exits with code 0 if the charcacter is in-game',
    action='store_true'
)
parser.add_argument(
    '--login',
    help='Logs in the first character in the list.',
    action='store_true'
)


SCREEN_SPECS = {
    "logged_out": [
        "f59afa",
        "fbe422",
        "ce4ff6",
        "41e8fb"
    ]
}

SCREEN_COORDS = [
    (1132, 316),
    (1531, 713),
    (480, 310),
    (482, 546)
]


class IntroScreenReader():
    def is_screen(self, tibia_wid, name):
        pixels = map(
            lambda (x, y): get_pixel_color_slow(tibia_wid, x, y),
            SCREEN_COORDS
        )
        for i in range(0, 3):
            if pixels[i] != SCREEN_SPECS[name][i]:
                print('%s (%s) is not equal to %s' %
                      (pixels[i], i, SCREEN_SPECS[name][i]))
                return False
        return True

    def is_logged_out_screen(self, tibia_wid):
        return self.is_screen(tibia_wid, 'logged_out')


def check_ingame(tibia_wid):
    reader = IntroScreenReader()
    return not reader.is_logged_out_screen(tibia_wid)

def close_dialogs(tibia_wid):
    # Press Escape key in case the character Menu is displayed.
    send_key(tibia_wid, 'Escape')
    time.sleep(0.5)
    # Press Enter key in case we're stuck in an Error screen.
    send_key(tibia_wid, 'Enter')
    time.sleep(0.5)
    # Press Escape key in case the character Menu is displayed.
    send_key(tibia_wid, 'Escape')
    time.sleep(0.5)
    # Press Enter key in case we're stuck in an Error screen.
    send_key(tibia_wid, 'Enter')
    time.sleep(0.5)
    # Press Escape key in case the character Menu is displayed.
    send_key(tibia_wid, 'Escape')
    time.sleep(0.5)
    # Press Enter key in case we're stuck in an Error screen.
    send_key(tibia_wid, 'Enter')


def login(tibia_wid, credentials):
    # Focus tibia window
    focus_tibia(tibia_wid)
    time.sleep(0.5)
    close_dialogs(tibia_wid)
    time.sleep(0.5)
    # Click on the password field (x:973, y:506)
    left_click(tibia_wid, 973, 506)
    time.sleep(0.1)
    # Send keypress: End
    send_key(tibia_wid, 'End')
    time.sleep(0.1)
    # Send keypress: Ctrl + Backspace
    send_key(tibia_wid, 'Ctrl+Backspace')
    time.sleep(0.1)
    # Type in password with 250ms between keypress
    send_text(tibia_wid, credentials['password'])
    time.sleep(0.1)
    # Click [Login] button
    left_click(tibia_wid, 1040, 610)
    time.sleep(5)
    #   - Focus should be on the 1st char on the list.
    # Click [OK] in char menu
    left_click(tibia_wid, 1216, 725)
    #   - Spin-wait for 30 seconds waiting for character to be in-game
    for i in range(1, 30):
        if check_ingame(tibia_wid):
            return True
        time.sleep(1)
    # 8a. If after 30 seconds char is not in-game, return False
    return False


def wait_for_lock():
    if not os.path.exists('.tibia_reconnector.lock'):
        return True

    print('Another Tibia account is reconnecting, waiting.')
    max_wait_retry_secs = 60 * 32
    wait_retry_secs = 60
    while wait_retry_secs <= max_wait_retry_secs:
        locked = os.path.exists('.tibia_reconnector.lock')
        if locked:
            print('Still locked.')
            print('Waiting %s seconds before retrying.' % wait_retry_secs)
            time.sleep(wait_retry_secs)
        else:
            return True
        wait_retry_secs *= 2

    return False


def handle_login(tibia_wid, credentials):
    if not wait_for_lock():
        print('Unable to acquire reconnector lock, quitting.')
        exit(1)
    else:
        open('.tibia_reconnector.lock', 'a').close()

    try:
        if check_ingame(tibia_wid):
            print('A character is already in-game.')
            exit(0)

        max_wait_retry_secs = 60 * 32
        wait_retry_secs = 60
        while wait_retry_secs <= max_wait_retry_secs:
            success = login(tibia_wid, credentials)
            if success:
                print('Login succeeded.')
                exit(0)
            else:
                print('Login failed.')
                print('Waiting %s seconds before retrying.' % wait_retry_secs)
                time.sleep(wait_retry_secs)
            wait_retry_secs *= 2
        exit(1)
    finally:
        os.remove('./.tibia_reconnector.lock')


def handle_check(tibia_wid):
    """Handles the case where the user only wants to check if the character is
    in-game."""
    if check_ingame(tibia_wid):
        exit(0)
    else:
        exit(1)


def main(tibia_pid, credentials_profile, only_check=False, login=False):
    """Main entry point of the program."""
    tibia_wid = get_tibia_wid(tibia_pid)
    if only_check:
        handle_check(tibia_wid)
    if login:
        if credentials_profile is None:
            print("We require a profile to login. See credentials.py")
            exit(1)
        credentials = CREDENTIALS.get(credentials_profile, None)
        if credentials is None:
            print("Unknown credentials profile " + credentials_profile)
            exit(1)
        handle_login(tibia_wid, credentials)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args.pid, args.credentials_profile, args.check_if_ingame, args.login)
