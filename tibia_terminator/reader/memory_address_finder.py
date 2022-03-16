#!/usr/bin/env python3.8

from typing import List, Optional, Callable, Tuple
from ctypes import c_int

import time
import logging
import math

from tibia_terminator.reader.ocr_number_reader import OcrNumberReader, Rect
from tibia_terminator.reader.window_utils import get_tibia_wid, send_key
from tibia_terminator.reader.read_only_process import ReadOnlyProcess

logger = logging.getLogger(__name__)


class MemoryAddressFinder:
    def __init__(
        self,
        ocr_reader: OcrNumberReader,
        tibia_pid: int,
    ):
        self.tibia_pid = tibia_pid
        self.ocr_reader = ocr_reader

    def read_ocr_value(
        self, rect: Rect, prev_value: Optional[int] = None
    ) -> Tuple[int, bool, Rect]:
        retry_updates = [
            ("y", 2),
            ("y", -2),
            ("x", 2),
            ("x", -2),
            ("width", 2),
            ("width", -2),
            ("height", 2),
            ("height", -2),
        ]

        def retry_rect(orig: Rect, retry_no: int) -> Rect:
            key, value = retry_updates[retry_no]
            return orig.update({key: getattr(orig, key) + value})

        def read_valid_ocr_value() -> Optional[int]:
            _retries_left = 5
            while _retries_left > 0:
                logger.info("Attempting to OCR read next value.")
                value_str = self.ocr_reader.read_number(rect).strip()
                if len(value_str) > 0:
                    return int(value_str)
                _retries_left -= 1

        if prev_value is None:
            return (read_valid_ocr_value(), False, rect)

        value = None

        def should_discard_value():
            if value is None:
                return True

            delta = abs(value - prev_value)
            value_digits = int(math.log(value, 10))
            prev_value_digits = int(math.log(value, 10))
            if value_digits != prev_value_digits:
                if delta >= 1000:
                    logger.info(
                        (
                            "Discarding poorly read OCR value: %s, "
                            "because it has fewer digits (%s -> %s) "
                            "and the delta (%s) is over 1000."
                        ),
                        value,
                        value_digits,
                        prev_value_digits,
                        delta,
                    )
                    # We probably lost a digit during OCR
                    return True

            # There was an 80% difference between values and over a
            # thousand points of difference
            ratio = max(value, prev_value) / min(value, prev_value)
            if delta >= 1000:
                logger.info(
                    "Discarding poorly read OCR value: %s,"
                    "because the ratio (%s) between the old value (%s) "
                    "and the new value (%s) is over 5 and the delta (%s) "
                    "is over 1000.",
                    value,
                    int(ratio),
                    prev_value,
                    value,
                    delta,
                )
                return True

        orig_rect = rect
        best_rect = orig_rect
        retries_left = len(retry_updates)
        while should_discard_value() and retries_left > 0:
            value = read_valid_ocr_value()
            if not should_discard_value():
                best_rect = rect
            else:
                rect = retry_rect(orig_rect, len(retry_updates) - retries_left)
                logger.info("Will attempt to OCR read with rect: %s", rect)
            retries_left -= 1

        return (value, should_discard_value(), best_rect)

    def find_address(
        self,
        update_keys: List[str],
        text_field_rectangle: Rect,
        ctype_ctor: Callable = c_int,
        initial_address_space: Optional[List[int]] = None,
    ) -> Tuple[List[int], Rect]:
        with ReadOnlyProcess(self.tibia_pid) as proc:
            prev_value = None
            tibia_wid = int(get_tibia_wid(self.tibia_pid))
            value, _, __ = self.read_ocr_value(text_field_rectangle, prev_value)
            if initial_address_space is None:
                addresses = proc.search_all_memory(
                    ctype_ctor(value), writeable_only=True
                )
            else:
                addresses = proc.search_addresses(addresses, ctype_ctor(value))

            logger.info("OCR Scan of %s: %s", text_field_rectangle, value)
            logger.info("Found %s matching.", len(addresses))

            for i, update_key in enumerate(update_keys):
                if len(addresses) <= 1:
                    return (addresses, text_field_rectangle)

                if i > 0:
                    time.sleep(0.75)  # Wait for next key press
                logger.info("Sending key %s to window %s", update_key, tibia_wid)
                send_key(tibia_wid, update_key)
                time.sleep(0.25)  # Wait for the memory to update
                new_value, should_discard_value, new_rect = self.read_ocr_value(
                    text_field_rectangle, value
                )
                # look for the value *immediately*
                if should_discard_value:
                    logger.warning(
                        "OCR had poor results, ignoring value read (%s).", new_value
                    )
                else:
                    prev_value = value
                    value = new_value
                    text_field_rectangle = new_rect
                    logger.info("Searching %s addresses.", len(addresses))
                    addresses = proc.search_addresses(addresses, ctype_ctor(value))
                    logger.info("OCR Scan of %s: %s", text_field_rectangle, value)
                    logger.info("Found %s matching.", len(addresses))
            return (addresses, text_field_rectangle)

    def read_memory(self, addr: int, ctype_ctor: Callable = c_int) -> int:
        with ReadOnlyProcess(self.tibia_pid) as proc:
            return proc.read_memory(addr, ctype_ctor())


if __name__ == "__main__":
    from argparse import ArgumentParser, Namespace
    from tibia_terminator.reader.window_utils import ScreenReader
    from tesserocr import PyTessBaseAPI

    def main(args: Namespace) -> None:
        logging.basicConfig(level=args.log_level)
        with ScreenReader(int(get_tibia_wid(args.tibia_pid))) as screen_reader:
            with OcrNumberReader(screen_reader, PyTessBaseAPI()) as ocr_reader:
                f = MemoryAddressFinder(ocr_reader, args.tibia_pid)
                addresses, _ = f.find_address(
                    args.update_keys,
                    Rect(args.x, args.y, args.width, args.height),
                    c_int,
                )
                for address in addresses:
                    value = f.read_memory(address, c_int)
                    print(f"Address: {hex(address)}")
                    print(f"Value: {value}")

    parser = ArgumentParser(
        "Memory Address finder for the Tibia Client",
        description=(
            "Use this to find the memory address of a field that can"
            " be read via OCR within the Tibia Client"
        ),
    )
    parser.add_argument(
        "tibia_pid", help="Process identifier of the Tibia Window", type=int
    )
    parser.add_argument(
        "x",
        type=int,
        help=(
            "X coordinate of the upper left pixel of the rectangle where "
            "the text is located."
        ),
    )
    parser.add_argument(
        "y",
        type=int,
        help=(
            "Y coordinate of the upper left pixel of the rectangle where "
            "the text is located."
        ),
    )
    parser.add_argument("width", type=int, help="Width of the rectangle")
    parser.add_argument("height", type=int, help="Height of the rectangle")
    parser.add_argument(
        "update_keys",
        nargs="+",  # one or more
        type=str,
        help="Key to send to the client in order to update the value",
    )
    parser.add_argument(
        "--log_level",
        type=int,
        choices=[
            logging.INFO,
            logging.DEBUG,
            logging.WARN,
            logging.ERROR,
            logging.FATAL,
        ],
        required=False,
        default=logging.INFO,
    )

    main(parser.parse_args())
