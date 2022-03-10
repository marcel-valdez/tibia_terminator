"""Utilities to interact with the Tibia Window.

Requires python-xlib, python-imaging and imagemagick
"""

import subprocess
import os

from typing import Union, List, Tuple, Iterable

import Xlib.display  # python-xlib
import PIL.Image  # python-imaging
import PIL.ImageStat  # python-imaging

from tibia_terminator.schemas.reader.common import Coord


XY = Tuple[int, int]


def get_debug_level():
    level = os.environ.get("DEBUG")
    if level is not None and isinstance(level, str) and level.isdigit():
        return int(level)

    return -1


def debug(msg, debug_level=0):
    if get_debug_level() >= debug_level:
        print(msg)


class Key:
    BACKSPACE = "BackSpace"
    SPACE = "space"
    ENTER = "Return"
    ESCAPE = "Escape"
    CTRL = "Ctrl"
    END = "End"
    SHIFT = "Shift_L"
    HOME = "Home"


class WindowGeometry:
    window: int
    x: int
    y: int
    width: int
    height: int
    screen: int


def parse_bash_variables_to_object(dst: object, bash_variables: str) -> None:
    for line in bash_variables.split(os.linesep):
        clean_line = line.strip().lower()
        if clean_line:
            attr_name = clean_line[0 : clean_line.index("=")]
            attr_value = int(clean_line[clean_line.index("=") + 1 :])
            dst.__setattr__(attr_name, attr_value)
    return dst


def run_cmd(cmd: List[str], debug_level=2) -> str:
    debug(" ".join(cmd), debug_level)
    stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    debug(stdout, debug_level)
    # TODO: In windows / mac this encoding may be a different value
    return stdout.decode("utf-8")


def get_window_geometry(wid: Union[str, int]) -> WindowGeometry:
    """Get the window geometry for a given window id."""
    geometry_str = run_cmd(
        ["/usr/bin/xdotool", "getwindowgeometry", "--shell", str(wid)], debug_level=1
    )
    return parse_bash_variables_to_object(WindowGeometry(), geometry_str)


def get_tibia_wid(pid: Union[str, int], debug_level=1) -> str:
    """Get the Tibia window id belonging to the process with PID."""
    return (
        run_cmd(["/usr/bin/xdotool", "search", "--pid", str(pid)], debug_level)
        .strip()
        .splitlines()[-1]
        .strip()
    )


def focus_tibia(wid: str) -> str:
    """Bring the tibia window to the front by focusing it."""
    return run_cmd(
        ["/usr/bin/xdotool", "windowactivate", "--sync", str(wid)], debug_level=1
    ).strip()


def rgb_color_to_hex_str(rgb_color: str) -> str:
    r, g, b = int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2])
    return "%s%s%s" % (hex(r)[2:], hex(g)[2:], hex(b)[2:])


def get_pixel_rgb_bytes_imagemagick(wid: str, x: int, y: int):
    cmd = [
        "/usr/bin/import",
        "-window",
        str(wid),
        "-crop",
        f"1x1+{x}+{y}",
        "-depth",
        "8",
        "rgba:-",
    ]
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as pixel_snapshot_proc:
        pixel_rgb_bytes, stderr = pixel_snapshot_proc.communicate()
        if pixel_snapshot_proc.returncode != 0:
            print(str(stderr) + "\nUnable to fetch window snapshot.")
            raise Exception(str(stderr) + "\nUnable to fetch window snapshot.")

        return pixel_rgb_bytes


def get_pixel_color_slow(wid: str, x: int, y: int) -> str:
    """Get color of a pixel very slowly, only use for runemaking."""
    pixel_rgb_bytes = get_pixel_rgb_bytes_imagemagick(wid, x, y)
    pixel_rgb_image = PIL.Image.frombytes("RGB", (1, 1), pixel_rgb_bytes, "raw")
    try:
        pixel_rgb_color = PIL.ImageStat.Stat(pixel_rgb_image).mean
        return rgb_color_to_hex_str(pixel_rgb_color)
    finally:
        pixel_rgb_image.close()


def matches_screen_slow(wid, coords: Iterable[XY], color_spec: List[str]) -> bool:
    def get_pixel_fn(coord: XY):
        return get_pixel_color_slow(wid, *coord)

    pixels = list(map(get_pixel_fn, coords))
    match = True
    for i in range(0, len(pixels)):
        match &= pixels[i].lower() == color_spec[i].lower()
    return match


def send_key(wid: str, key: str) -> None:
    # synchronously send the keystroke
    output = run_cmd(
        ["/usr/bin/xdotool", "key", "--window", str(wid), str(key)]
    ).strip()

    if output:
        print(output)


def send_text(wid: str, text: str) -> None:
    output = run_cmd(
        ["/usr/bin/xdotool", "type", "--window", str(wid), "--delay", "250", text]
    ).strip()
    if output:
        print(output)


def left_click(wid: str, x: int, y: int) -> None:
    mousemove_output = run_cmd(
        [
            "/usr/bin/xdotool",
            "mousemove",
            "--window",
            str(wid),
            "--sync",
            str(x),
            str(y),
        ]
    ).strip()
    if mousemove_output:
        print(mousemove_output)

    click_output = run_cmd(
        ["/usr/bin/xdotool", "click", "--window", str(wid), "--delay", "50", "1"]
    ).strip()
    if click_output:
        print(click_output)


class ScreenReader:
    """Reads pixels in the screen."""

    def __init__(
        self,
        tibia_wid: int = None,
        screen: Xlib.protocol.display.Screen = None,
        display: Xlib.display.Display = None,
    ):
        self.screen = screen
        self.display = display
        self.tibia_wid = tibia_wid
        self.tibia_window = None

    def open(self):
        self.display = Xlib.display.Display()
        self.screen = self.display.screen()
        if self.tibia_wid:
            self.tibia_window = Xlib.xobject.drawable.Window(
                self.display.display, self.tibia_wid
            )

    def close(self):
        self.tibia_window = None
        self.screen = None
        self.display.close()
        self.display = None

    def get_pixel_rgb_bytes_xlib(self, x: int, y: int):
        window = self.tibia_window or self.screen.root
        return window.get_image(x, y, 1, 1, Xlib.X.ZPixmap, 0xFFFFFFFF)

    def get_coord_color(self, coord: Coord) -> str:
        return self.get_pixel_color(coord.x, coord.y)

    def get_area_image(self, x: int, y: int, width: int, height: int) -> PIL.Image:
        window = self.tibia_window or self.screen.root
        img_rgb_res = window.get_image(
            x,
            y,
            width,
            height,
            Xlib.X.ZPixmap,
            0xFFFFFFFF
        )

        if isinstance(img_rgb_res, str):
            img_rgb_bytes = bytes(img_rgb_res.data, "utf-8")
        else:
            img_rgb_bytes = img_rgb_res.data

        return PIL.Image.frombytes("RGB", (width, height), img_rgb_bytes, "raw", "BGRX")

    def get_pixel_color(self, x: int, y: int):
        pixel_rgb_res = self.get_pixel_rgb_bytes_xlib(x, y)

        # for some reason sometimes the byte data comes back as a string
        # but the data backing that string are the actual bytes
        if isinstance(pixel_rgb_res.data, str):
            pixel_rgb_bytes = bytes(pixel_rgb_res.data, "utf-8")
        else:
            pixel_rgb_bytes = pixel_rgb_res.data

        pixel_rgb_image = PIL.Image.frombytes(
            "RGB", (1, 1), pixel_rgb_bytes, "raw", "BGRX"
        )
        pixel_rgb_color = PIL.ImageStat.Stat(pixel_rgb_image).mean
        return rgb_color_to_hex_str(pixel_rgb_color).lower()

    def get_pixel_color_slow(self, x: int, y: int) -> str:
        # We do not offset this, since it uses values relative to the
        # window.
        return get_pixel_color_slow(self.tibia_wid, x, y)

    def get_coord_color_slow(self, coord: Coord) -> str:
        return self.get_pixel_color_slow(self.tibia_wid, coord.x, coord.y)

    def get_pixels_slow(self, coords: Iterable[XY]) -> List[str]:
        def get_pixel(coord: XY) -> str:
            return self.get_pixel_color_slow(*coord)

        return list(map(get_pixel, coords))

    def get_pixels(self, coords: Iterable[XY]) -> List[str]:
        def get_pixel(coord: XY) -> str:
            return self.get_pixel_color(*coord)

        return list(map(get_pixel, coords))

    def pixels_match(self, pixels_a: List[str], pixels_b: List[str]) -> bool:
        match = True
        for i in range(0, len(pixels_a)):
            match &= str(pixels_a[i]).lower() == str(pixels_b[i]).lower()
        return match

    def matches_screen(self, coords: Iterable[XY], color_spec: List[str]) -> bool:
        return self.pixels_match(self.get_pixels(coords), color_spec)
