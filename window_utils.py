"""Utilities to interact with the Tibia Window.

Requires python-xlib, python-imaging and imagemagick
"""

import subprocess
import Xlib.display  # python-xlib
import PIL.Image  # python-imaging
import PIL.ImageStat  # python-imaging
import os
from pprint import pprint


def get_debug_level():
    level = os.environ.get('DEBUG_LEVEL')
    if level is not None and isinstance(level, str) and level.isdigit():
        return int(level)
    else:
        return -1


def debug(msg, debug_level=0):
    if get_debug_level() >= debug_level:
        print(msg)


class Key:
    BACKSPACE = 'BackSpace'
    SPACE = 'space'
    ENTER = 'Return'
    ESCAPE = 'Escape'
    CTRL = 'Ctrl'
    END = 'End'


def get_tibia_wid(pid):
    """Get the Tibia window id belonging to the process with PID."""
    debug("/usr/bin/xdotool search --pid %s" % (pid))
    wid = subprocess.check_output(
        ["/usr/bin/xdotool", "search", "--pid", str(pid)],
        stderr=subprocess.STDOUT)
    debug(wid)
    return wid.decode('utf-8').strip()


def focus_tibia(wid):
    """Bring the tibia window to the front by focusing it."""
    debug("/usr/bin/xdotool windowactivate --sync %s" % (wid))
    wid = subprocess.check_output(
        ["/usr/bin/xdotool", "windowactivate", "--sync", str(wid)],
        stderr=subprocess.STDOUT)
    debug(wid)
    return wid


def rgb_color_to_hex_str(rgb_color):
    r, g, b = int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2])
    return "%s%s%s" % (hex(r)[2:], hex(g)[2:], hex(b)[2:])


def get_pixel_rgb_bytes_imagemagick(wid, x, y):
    cmd = [
        "/usr/bin/import",
        "-window", str(wid),
        "-crop", "1x1+%s+%s" % (x, y),
        "-depth", "8",
        "rgba:-",
    ]
    pixel_snapshot_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    pixel_rgb_bytes, stderr = pixel_snapshot_proc.communicate()
    if pixel_snapshot_proc.returncode != 0:
        print(str(stderr) + "\nUnable to fetch window snapshot.")
        raise Exception(str(stderr) + "\nUnable to fetch window snapshot.")

    return pixel_rgb_bytes


def get_pixel_color_slow(wid, x, y):
    """Get color of a pixel very slowly, only use for runemaking."""
    pixel_rgb_bytes = get_pixel_rgb_bytes_imagemagick(wid, x, y)
    pixel_rgb_image = \
        PIL.Image.frombytes("RGB", (1, 1), pixel_rgb_bytes, "raw")
    try:
        pixel_rgb_color = PIL.ImageStat.Stat(pixel_rgb_image).mean
        return rgb_color_to_hex_str(pixel_rgb_color)
    finally:
        pixel_rgb_image.close()

def matches_screen_slow(wid, coords, color_spec):
    get_pixel_fn = lambda coords: get_pixel_color_slow(wid, *coords)
    pixels = list(map(get_pixel_fn, coords))
    match = True
    for i in range(0, len(pixels)):
        match &= pixels[i].lower() == color_spec[i].lower()
    return match


def send_key(wid, key):
    # synchronously send the keystroke
    debug("/usr/bin/xdotool key --window %s %s" % (wid, key))
    output = subprocess.check_output(
        [
            "/usr/bin/xdotool", "key", "--window",
            str(wid),
            str(key)
        ],
        stderr=subprocess.STDOUT
    )

    if output is not None and output != '':
        print(output)


def send_text(wid, text):
    debug("/usr/bin/xdotool type --window %s --delay 50 <text>" % (wid))
    output = subprocess.check_output(
        [
            '/usr/bin/xdotool', 'type', '--window',
            str(wid),
            '--delay',
            '50',
            text
        ],
        stderr=subprocess.STDOUT
    )

    if output is not None and output != '':
        print(output)


def left_click(wid, x, y):
    debug("/usr/bin/xdotool mousemove --window %s --sync %s %s" % (wid, x, y))
    output = subprocess.check_output(
        [
            '/usr/bin/xdotool', 'mousemove', '--window',
            str(wid),
            '--sync',
            str(x), str(y)
        ],
        stderr=subprocess.STDOUT
    )
    if output is not None and output != '':
        print(output)
    debug("/usr/bin/xdotool click --window %s --delay 50 1" % (wid))
    output = subprocess.check_output(
        [
            '/usr/bin/xdotool', 'click', '--window',
            str(wid),
            '--delay',
            '50',
            '1'
        ],
        stderr=subprocess.STDOUT
    )
    if output is not None and output != '':
        print(output)


class ScreenReader():
    """Reads pixels in the screen."""

    def __init__(self, x_offset=0):
        """TODO."""
        self.screen = None
        self.display = None
        self.x_offset = x_offset

    def open(self):
        """TODO."""
        self.display = Xlib.display.Display()
        self.screen = self.display.screen()
        # pprint(vars(self.screen))
        # pprint(vars(self.screen.root))
        # pprint(dir(self.screen.root))

    def close(self):
        """TODO."""
        self.screen = None
        self.display.close()
        self.display = None

    def get_pixel_rgb_bytes_xlib(self, x, y):
        return self.screen.root.get_image(
            x + self.x_offset, y, 1, 1, Xlib.X.ZPixmap, 0xffffffff)

    def get_pixel_color(self, x, y):
        """TODO."""
        pixel_rgb_res = self.get_pixel_rgb_bytes_xlib(x, y)

        # for some reason sometimes the byte data comes back as a string
        # but the data backing that string are the actual bytes
        if isinstance(pixel_rgb_res.data, str):
            pixel_rgb_bytes = bytes(pixel_rgb_res.data, 'utf-8')
        else:
            pixel_rgb_bytes = pixel_rgb_res.data

        pixel_rgb_image = PIL.Image.frombytes(
            "RGB", (1, 1), pixel_rgb_bytes, "raw", "BGRX")
        pixel_rgb_color = PIL.ImageStat.Stat(pixel_rgb_image).mean
        return rgb_color_to_hex_str(pixel_rgb_color).lower()

    def get_pixel_color_slow(self, wid, x, y):
        return get_pixel_color_slow(wid, x, y)

    def get_pixels(self, coords):
        def get_pixel(coord):
            return self.get_pixel_color(*coord)

        return list(map(get_pixel, coords))

    def pixels_match(self, pixels_a, pixels_b):
        match = True
        for i in range(0, len(pixels_a)):
            match &= pixels_a[i].lower() == pixels_b[i].lower()
        return match

    def matches_screen(self, coords, color_spec):
        return self.pixels_match(self.get_pixels(coords), color_spec)
