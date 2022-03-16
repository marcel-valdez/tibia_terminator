#!/usr/bin/env python3.8

import logging

from argparse import ArgumentParser, Namespace
from typing import NamedTuple, List, Union, Tuple, Any


from tesserocr import PyTessBaseAPI, OEM
from tibia_terminator.reader.window_utils import ScreenReader


logger = logging.getLogger(__name__)


class Rect(NamedTuple):
    x: int
    y: int
    width: int
    height: int

    def copy(self, **update) -> "Rect":
        data = self._asdict()
        data.update(update)
        return Rect(**data)


def gen_bw_color_table() -> List[int]:
    color_table = []
    for i in range(256):
        if i <= 120:
            color_table.append(1)
        else:
            color_table.append(0)
    return color_table


class OcrNumberReader:
    def __init__(self, screen_reader: ScreenReader, ocr_api: PyTessBaseAPI):
        self.screen_reader = screen_reader
        self.ocr_api = ocr_api
        self.color_table = gen_bw_color_table()

    def __enter__(self, *args, **kwargs) -> "OcrNumberReader":
        self.open()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def open(self) -> None:
        # Do not load dicionaries of words or common word patterns, since
        # we'll only read numbers
        self.ocr_api.SetVariable("load_bigram_dawg", "0")
        self.ocr_api.SetVariable("load_freq_dawg", "0")
        self.ocr_api.SetVariable("load_system_dawg", "0")
        self.ocr_api.SetVariable("load_unambig_dawg", "0")
        self.ocr_api.SetVariable("tessedit_ocr_engine_mode", str(int(OEM.LSTM_ONLY)))
        # Only detect numbers
        self.ocr_api.SetVariable("tessedit_char_whitelist", "1234567890")
        self.ocr_api.Init()
        # Assum single uniform block of vertically aligned text
        self.ocr_api.SetVariable("tessedit_pageseg_mode", "8")
        # Only classify numbers
        self.ocr_api.SetVariable("classify_bln_numeric_mode", "1")
        # Do not invert image text colors
        self.ocr_api.SetVariable("tessedit_do_invert", "0")
        # Text is all proportional
        self.ocr_api.SetVariable("textord_all_prop", "1")
        # Run in parallel where possible
        self.ocr_api.SetVariable("tessedit_parallelize", "1")
        # Don't use any alphabetic-specific tricks (it is all digits)
        self.ocr_api.SetVariable("segment_nonalphabetic_script", "1")
        # Don't post-process after OCR detection
        self.ocr_api.SetVariable("paragraph_text_based", "0")

    def close(self) -> None:
        self.ocr_api.End()

    def read_number(
        self, rect: Rect, return_image: bool = False
    ) -> Union[str, Tuple[str, Any]]:
        with self.screen_reader.get_area_image(
            rect.x, rect.y, rect.width, rect.height
        ) as image:
            # convert image into black text over white background, since
            # tesseract is MUCH better at parsing the image like that.
            bw_image = image.convert("L").point(self.color_table, mode="1")
            try:
                self.ocr_api.SetImage(bw_image)
                number = str(self.ocr_api.GetUTF8Text()).strip()
                if return_image:
                    return (number, bw_image)
                return number
            finally:
                if not return_image:
                    bw_image.close()


if __name__ == "__main__":
    from tibia_terminator.reader.window_utils import get_tibia_wid
    import time

    def percentile(times: List[int], percentile_value: float) -> float:
        return times[int(len(times) * percentile_value)] * 1000

    def main(args: Namespace):
        tibia_wid = get_tibia_wid(args.tibia_pid)
        with ScreenReader(int(tibia_wid)) as screen_reader:
            with OcrNumberReader(screen_reader, PyTessBaseAPI()) as ocr_reader:
                times = []
                text = None
                rect = Rect(
                    x=args.coords[0],
                    y=args.coords[1],
                    width=args.width,
                    height=args.height,
                )
                # warm-up
                logger.info("Performing warm-up")
                for _ in range(10):
                    text = ocr_reader.read_number(rect)

                logger.info("Reading %s samples", args.samples)
                for _ in range(args.samples):
                    start = time.time()
                    text = ocr_reader.read_number(rect)
                    end = time.time()
                    times.append(end - start)

                if args.show_image:
                    (_, image) = ocr_reader.read_number(rect, True)
                    image.show()

                times.sort()
                avg_ms = sum(times) * 1000 / len(times)
                max_ms = times[-1] * 1000
                min_ms = times[0] * 1000
                median_ms = percentile(times, 0.5)
                p99_ms = percentile(times, 0.99)
                p95_ms = percentile(times, 0.95)
                p75_ms = percentile(times, 0.75)
                p25_ms = percentile(times, 0.25)
                p90_ms = percentile(times, 0.90)
                p01_ms = percentile(times, 0.01)
                p05_ms = percentile(times, 0.05)
                p10_ms = percentile(times, 0.10)

                print(f"samples: {args.samples}")
                print(f"avg: {avg_ms:.1f} median: {median_ms:.1f}")
                print(f"max: {max_ms:.1f} min: {min_ms:.1f}")
                print(f"p99: {p99_ms:.1f} p95: {p95_ms:.1f} p90: {p90_ms:.1f}")
                print(f"p75: {p75_ms:.1f} p50: {median_ms:.1f} p25: {p25_ms:.1f}")
                print(f"p10: {p10_ms:.1f} p05: {p05_ms:.1f} p01: {p01_ms:.1f}")
                print(f"Read text: {text}")

    parser = ArgumentParser(
        "OCR Scanner for the Tibia Window",
        description="Use this to read numbers directly from the window's pixels.",
    )
    parser.add_argument(
        "tibia_pid", help="Process identifier of the Tibia Window", type=int
    )
    parser.add_argument(
        "coords",
        nargs=2,
        type=int,
        help=(
            "X Y coordinates of the upper left pixel of the rectangle where "
            "the text is located. e.g. 12 34"
        ),
    )
    parser.add_argument("width", type=int, help="Width of the rectangle")
    parser.add_argument("height", type=int, help="Height of the rectangle")
    parser.add_argument(
        "--samples",
        type=int,
        default=1,
        help=(
            "Number of times to read the screen. Useful for tunning the "
            "OCR performance settings"
        ),
    )
    parser.add_argument(
        "--show_image",
        action="store_true",
        help="Show the last image processed.",
        default=False,
        required=False,
    )

    main(parser.parse_args())
