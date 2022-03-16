#!/usr/bin/env python3.8

import time
import logging

from typing import Optional, Any, Callable
from ctypes import c_int, c_int16, c_int32

from tibia_terminator.reader.char_reader38 import MAGIC_SHIELD_TO_SPEED_OFFSET
from tibia_terminator.reader.memory_address_finder import MemoryAddressFinder
from tibia_terminator.reader.ocr_number_reader import Rect
from tibia_terminator.reader.window_utils import get_tibia_wid, send_key
from tibia_terminator.schemas.app_config_schema import AppConfig
from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig

logger = logging.getLogger(__name__)


class UnableToFindMemoryAddressException(Exception):
    pass


def ctype_to_int(value: Any):
    try:
        return int(value.value)
    except ValueError:
        return value


class AppConfigMemoryAddressFinder:
    def __init__(
        self,
        tibia_pid: int,
        memory_address_finder: MemoryAddressFinder,
        hotkeys_config: HotkeysConfig,
        mana_rect: Rect,
        speed_rect: Rect,
        hp_rect: Optional[Rect] = None,
        soul_points_rect: Optional[Rect] = None,
    ):
        self.tibia_pid = tibia_pid
        self.memory_address_finder = memory_address_finder
        self.hotkeys_config = hotkeys_config
        self.mana_rect = mana_rect
        self.speed_rect = speed_rect
        self.hp_rect = hp_rect
        self.soul_points_rect = soul_points_rect

    def find_mana_address(self) -> int:
        retry_count = 3
        while retry_count > 0:
            addresses, better_rect = self.memory_address_finder.find_address(
                [self.hotkeys_config.greater_heal for _ in range(6)],
                self.mana_rect,
                c_int,
            )
            self.mana_rect = better_rect
            if len(addresses) == 1:
                return addresses[0]
            retry_count -= 1

        raise UnableToFindMemoryAddressException("Unable to determine mana address")

    def find_speed_address(self) -> int:
        # Try to wait for haste to wear off
        keys = [
            self.hotkeys_config.haste,
            self.hotkeys_config.eat_food,
            self.hotkeys_config.eat_food,
            self.hotkeys_config.eat_food,
            self.hotkeys_config.eat_food,
        ]
        addresses, better_rect = self.memory_address_finder.find_address(
            keys, self.speed_rect, c_int16
        )
        self.speed_rect = better_rect
        if len(addresses) == 1:
            return addresses[0]

        # If there is no magic shield hotkey setup, then it does not
        # even matter.
        if not self.hotkeys_config.magic_shield:
            if len(addresses) == 2:
                return min(*addresses)
            raise Exception("Unable to determine speed memory address.")

        for address in addresses:
            possible_magic_shield_address = address + MAGIC_SHIELD_TO_SPEED_OFFSET
            magic_shield_value = ctype_to_int(
                self.memory_address_finder.read_memory(
                    possible_magic_shield_address, c_int16
                )
            )
            # We haven't cast magic shield, magic shield value should be 0
            if magic_shield_value != 0:
                logger.info(
                    "wrong magic_shield value: %s expected 0", magic_shield_value
                )
                continue

            logger.info("possibly correct magic_shield value: %s", magic_shield_value)
            tibia_wid = int(get_tibia_wid(self.tibia_pid))
            time.sleep(1.75)  # Wait for cooldown of support spells
            send_key(tibia_wid, self.hotkeys_config.magic_shield)
            time.sleep(1)  # Wait for the spell to take effect
            magic_shield_value = ctype_to_int(
                self.memory_address_finder.read_memory(
                    possible_magic_shield_address, c_int16
                )
            )
            # the magic shield value should NOT be 0, skip this address if
            # it is 0.
            if magic_shield_value == 0:
                logger.info(
                    "wrong magic_shield value: %s expected >0", magic_shield_value
                )
                continue

            logger.info("possibly correct magic_shield value: %s", magic_shield_value)
            time.sleep(2.5)  # Wait for cooldown of support spells
            send_key(tibia_wid, self.hotkeys_config.cancel_magic_shield)
            time.sleep(1)  # Wait for spell to take effect
            magic_shield_value = ctype_to_int(
                self.memory_address_finder.read_memory(
                    possible_magic_shield_address, c_int16
                )
            )
            # After cancelling, magic shield value should be 0
            if magic_shield_value == 0:
                # Success
                return address

        # If they're playing on a Knight, magic shield may not be running
        # and we don't really care about it in that scenario, either address
        # works.
        if len(addresses) == 2:
            return min(*addresses)

        raise UnableToFindMemoryAddressException(
            "Unable to determine speed memory address"
        )

    def build_app_config_entry(self) -> AppConfig:
        mana_address = self.find_mana_address()
        time.sleep(1)
        speed_address = self.find_speed_address()
        return AppConfig(
            pid=self.tibia_pid,
            mana_memory_address=hex(mana_address),
            speed_memory_address=hex(speed_address),
        )


if __name__ == "__main__":
    from argparse import ArgumentParser, Namespace

    import commentjson as json

    from tesserocr import PyTessBaseAPI

    from tibia_terminator.reader.ocr_number_reader import OcrNumberReader
    from tibia_terminator.reader.window_utils import ScreenReader
    from tibia_terminator.reader.window_utils import ScreenReader
    from tibia_terminator.schemas.app_config_schema import AppConfigSchema
    from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfigSchema

    def main(args: Namespace) -> None:
        logging.basicConfig(level=args.log_level)
        hotkeys_config = HotkeysConfigSchema().loadf(args.hotkeys_config_file)
        with ScreenReader(int(get_tibia_wid(args.tibia_pid))) as screen_reader:
            with OcrNumberReader(screen_reader, PyTessBaseAPI()) as ocr_reader:
                finder = AppConfigMemoryAddressFinder(
                    tibia_pid=args.tibia_pid,
                    memory_address_finder=MemoryAddressFinder(
                        ocr_reader, args.tibia_pid
                    ),
                    hotkeys_config=hotkeys_config,
                    mana_rect=Rect(
                        args.mana_xy[0],
                        args.mana_xy[1],
                        args.mana_wh[0],
                        args.mana_wh[1],
                    ),
                    speed_rect=Rect(
                        args.speed_xy[0],
                        args.speed_xy[1],
                        args.speed_wh[0],
                        args.speed_wh[1],
                    ),
                )
                app_config = finder.build_app_config_entry()
                print(
                    json.dumps(
                        AppConfigSchema().dump(app_config), indent=4, sort_keys=True
                    )
                )

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
        "--mana_xy",
        required=True,
        type=int,
        nargs=2,
        help=("(x,y) coordinates of the mana rectangle. e.g. --mana_xy 1853 516"),
        default=[1853, 520],
    )
    parser.add_argument(
        "--mana_wh",
        required=True,
        type=int,
        nargs=2,
        help=("width and height of the mana rectangle. e.g. --mana_wh 50 20"),
        default=[50, 16],
    )
    parser.add_argument(
        "--speed_xy",
        required=True,
        type=int,
        nargs=2,
        help=("(x,y) coordinates of the speed rectangle. e.g. --speed_xy 1858 561"),
        default=[1858, 565],
    )
    parser.add_argument(
        "--speed_wh",
        required=True,
        type=int,
        nargs=2,
        help=("width and height of the speed rectangle. e.g. --speed_wh 45 20"),
        default=[45, 16],
    )
    parser.add_argument(
        "--hotkeys_config_file",
        required=True,
        type=str,
        help=("Filepath to the hotkeys config file (JSON)."),
    )
    parser.add_argument(
        "--log_level",
        required=False,
        type=int,
        choices=[
            logging.DEBUG,
            logging.INFO,
            logging.WARN,
            logging.ERROR,
            logging.FATAL,
        ],
        default=logging.INFO,
    )

    main(parser.parse_args())
