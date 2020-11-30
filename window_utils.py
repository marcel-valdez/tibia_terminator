"""Utilities to interact with the Tibia Window.

Requires python-xlib, python-imaging and imagemagick
"""

import subprocess
import Xlib.display  # python-xlib
import PIL.Image  # python-imaging
import PIL.ImageStat  # python-imaging
import os


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
    return wid.strip()


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
    pixel_snapshot_proc = subprocess.Popen(
        [
            "/usr/bin/import",
            "-window", str(wid),
            "-crop", "1x1+%s+%s" % (x, y),
            "-depth", "8",
            "rgba:-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    pixel_rgb_bytes, stderr = pixel_snapshot_proc.communicate()
    if pixel_snapshot_proc.returncode != 0:
        print(str(stderr) + "\nUnable to fetch window snapshot.")
        raise

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

    def get_pixel_rgb_bytes_xlib(self, x, y):
        return self.screen.root.get_image(
            x, y, 1, 1, Xlib.X.ZPixmap, 0xffffffff)

    def get_pixel_color(self, x, y):
        """TODO."""
        pixel_rgb_bytes = self.get_pixel_rgb_bytes_xlib(x, y)
        pixel_rgb_image = PIL.Image.frombytes(
            "RGB", (1, 1), pixel_rgb_bytes.data, "raw", "BGRX")
        pixel_rgb_color = PIL.ImageStat.Stat(pixel_rgb_image).mean
        return rgb_color_to_hex_str(pixel_rgb_color)

    def get_pixel_color_slow(self, wid, x, y):
        return get_pixel_color_slow(wid, x, y)

    def matches_screen(self, coords, color_spec):
        pixels = map(lambda (x, y): self.get_pixel_color(x, y), coords)
        match = True
        for i in range(0, len(pixels)):
            match &= pixels[i].lower() == color_spec[i].lower()
        return match
