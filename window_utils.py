"""Utilities to interact with the Tibia Window."""

import subprocess
import Xlib.display  # python-xlib
import PIL.Image  # python-imaging
import PIL.ImageStat  # python-imaging
import random
from functools import reduce


def get_tibia_wid(pid):
    """Get the Tibia window id belonging to the process with PID."""
    wid = subprocess.check_output(
        ["/usr/bin/xdotool", "search", "--pid", str(pid)],
        stderr=subprocess.STDOUT)
    return wid.strip()


def focus_tibia(wid):
    """Bring the tibia window to the front by focusing it."""
    wid = subprocess.check_output(
        ["/usr/bin/xdotool", "windowactivate", "--sync", str(wid)],
        stderr=subprocess.STDOUT)
    return wid


def get_pixel_color_slow(tibia_wid, x, y):
    """Get color of a pixel very slowly, only use for runemaking."""
    snapshot_proc = subprocess.Popen(
        [
            "/usr/bin/import",
            "-window", str(tibia_wid),
            "-crop", "1x1+%s+%s" % (x, y),
            "-depth", "8",
            "rgba:-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = snapshot_proc.communicate()
    if snapshot_proc.returncode != 0:
        print("Unable to fetch window snapshot")
        print(stderr)

    rgb_image = PIL.Image.frombytes("RGB", (1, 1), stdout, "raw")
    try:
        color = PIL.ImageStat.Stat(rgb_image).mean
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        return "%s%s%s" % (hex(r)[2:], hex(g)[2:], hex(b)[2:])
    finally:
        rgb_image.close()


def send_key(tibia_wid, key):
    # asynchronously send the keystroke
    subprocess.check_output(
        [
            "/usr/bin/xdotool", "key", "--window",
            str(tibia_wid),
            str(key)
        ],
        stderr=subprocess.STDOUT
    )


def send_text(tibia_wid, text):
    subprocess.check_output(
        [
            '/usr/bin/xdotool', 'type', '--window',
            str(tibia_wid),
            '--delay',
            '50',
            text
        ],
        stderr=subprocess.STDOUT
    )


def left_click(tibia_wid, x, y):
    subprocess.check_output(
        [
            '/usr/bin/xdotool', 'mousemove', '--window',
            str(tibia_wid),
            '--sync',
            str(x), str(y)
        ],
        stderr=subprocess.STDOUT
    )
    subprocess.check_output(
        [
            '/usr/bin/xdotool', 'click', '--window',
            str(tibia_wid),
            '--delay',
            '50',
            '1'
        ],
        stderr=subprocess.STDOUT
    )


class ScreenReader():
    """Reads pixels in the screen."""

    def __init__(self):
        """TODO."""
        self.screen = None
        self.display = None

    def open(self):
        """TODO."""
        self.display = Xlib.display.Display()
        self.screen = self.display.screen()

    def close(self):
        """TODO."""
        self.screen = None
        self.display.close()
        self.display = None

    # use this to get the color profile of a given amulet (or empty)
    def get_pixel_color(self, x, y):
        """TODO."""
        raw_screen_pixels = self.screen.root.get_image(
            x, y, 1, 1, Xlib.X.ZPixmap, 0xffffffff)
        rgb_screen_pixels = PIL.Image.frombytes(
            "RGB", (1, 1), raw_screen_pixels.data, "raw", "BGRX")
        rgb_pixel_color = PIL.ImageStat.Stat(rgb_screen_pixels).mean
        return reduce(lambda a, b: a[1:] + b[2:],
                      map(hex, map(int, rgb_pixel_color)))
