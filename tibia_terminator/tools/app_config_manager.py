#!/usr/bin/env python3.8

import sys
import logging

from argparse import ArgumentParser, Namespace
from typing import Iterable, List


import psutil
import commentjson as json

from tibia_terminator.schemas.app_config_schema import (
    AppConfigsSchema,
    AppConfigs,
    AppConfig,
)
from tibia_terminator.tools.app_config_memory_address_finder import (
    AppConfigMemoryAddressFinder,
)
from tibia_terminator.schemas.reader.interface_config_schema import (
    TibiaWindowSpecSchema,
    TibiaWindowSpec,
)
from tibia_terminator.schemas.hotkeys_config_schema import (
    HotkeysConfigSchema,
    HotkeysConfig,
)
from tibia_terminator.reader.memory_address_finder import MemoryAddressFinder
from tibia_terminator.reader.ocr_number_reader import OcrNumberReader
from tibia_terminator.reader.window_utils import ScreenReader, get_tibia_wid
from tesserocr import PyTessBaseAPI


logger = logging.getLogger(__name__)


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog=(
            "AppConfig Manager: Tool to load and generate Tibia Terminator App Configs"
        )
    )
    parser.add_argument(
        "--log_level",
        type=int,
        required=False,
        default=logging.INFO,
        choices=[
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.FATAL,
        ],
    )
    parser.add_argument(
        "--dry_run",
        help="Run without updating the JSON config file",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "app_config",
        help=(
            "Path to the AppConfig json file (e.g. app_config.json). "
            "If this file does not exist, then it will be created for you. "
            "Otherwise, the pre-existing file will be updated with a new entry "
            "and old entries will be deleted if no currently running process "
            "matches the associated PID."
        ),
        type=str,
    )
    subparser = parser.add_subparsers(
        title="App Config Manager Commands",
        required=True,
        dest="command",
    )
    update_pids = subparser.add_parser(
        "update_pids", help="Update the PIDs in the App Config file"
    )
    update_pids.add_argument(
        "--only_cleanup",
        help=("Tells this tool to only cleanup stale entries in the AppConfig file."),
        action="store_true",
    )
    update_pids.add_argument(
        "--only_append",
        help=("Tells this tool to only append entries to the AppConfig file."),
        action="store_true",
    )

    find_addresses = subparser.add_parser(
        "find_addresses",
        help="Automatically determine the memory addresses of a given PID",
    )
    find_addresses.add_argument(
        "--pid",
        help=("PID of the Tibia Process to analyze for memory addresses"),
        type=int,
        required=True,
    )
    find_addresses.add_argument(
        "--tibia_window_config",
        help="Filepath to the Tibia Window Config JSON file.",
        type=str,
        required=True,
    )
    find_addresses.add_argument(
        "--hotkeys_config",
        help="Filepath to the Hotkeys configuration JSON file.",
        type=str,
        required=True,
    )
    return parser.parse_args()


def get_tibia_pids() -> Iterable[int]:
    for proc in psutil.process_iter():
        for arg in proc.cmdline():
            if "Tibia" in arg:
                yield proc.pid


def remove_stale_entries(app_configs: AppConfigs, tibia_pids: List[int]) -> AppConfigs:
    default_pid = tibia_pids[0]
    if app_configs.default_pid in tibia_pids:
        default_pid = app_configs.default_pid

    configs = [c for c in app_configs.configs if c.pid in tibia_pids]
    return AppConfigs(
        default_pid=default_pid,
        configs=configs,
    )


def append_new_entries(app_configs: AppConfigs, tibia_pids: List[int]) -> AppConfigs:
    configs = app_configs.configs
    for tibia_pid in tibia_pids:
        if not any(c for c in configs if c.pid == tibia_pid):
            configs.append(AppConfig(pid=tibia_pid))

    return AppConfigs(default_pid=app_configs.default_pid, configs=configs)


def write_app_config(app_configs: AppConfigs, app_config_file: str) -> None:
    with open(app_config_file, mode="w", encoding="utf-8") as fp:
        json.dump(AppConfigsSchema().dump(app_configs), fp, indent=4, sort_keys=True)


def read_app_configs(app_config_file: str) -> AppConfigs:
    return AppConfigsSchema().loadf(app_config_file)


def find_memory_addresses(args: Namespace, app_configs: AppConfigs) -> AppConfigs:
    hotkeys_config = HotkeysConfigSchema().loadf(args.hotkeys_config)
    tibia_window_config = TibiaWindowSpecSchema().loadf(args.tibia_window_config)
    with ScreenReader(tibia_wid=int(get_tibia_wid(args.pid))) as screen_reader:
        with OcrNumberReader(
            screen_reader=screen_reader,
            ocr_api=PyTessBaseAPI(),
        ) as ocr_reader:
            app_config_memory_address_finder = AppConfigMemoryAddressFinder(
                tibia_pid=args.pid,
                memory_address_finder=MemoryAddressFinder(
                    tibia_pid=args.pid, ocr_reader=ocr_reader
                ),
                hotkeys_config=hotkeys_config,
                mana_rect=tibia_window_config.stats_fields.mana_field,
                speed_rect=tibia_window_config.stats_fields.speed_field,
            )
            built_config = app_config_memory_address_finder.build_app_config_entry()
            new_configs = list(
                config if config.pid != args.pid else built_config
                for config in app_configs.configs
            )
            return app_configs._replace(configs=new_configs)


def main(args: Namespace) -> None:
    logging.basicConfig(level=args.log_level)
    app_configs = read_app_configs(args.app_config)
    if args.command == "update_pids":
        tibia_pids = list(get_tibia_pids())
        if len(tibia_pids) == 0:
            print("There are no running Tibia process, nothing to do.")
            sys.exit(0)

        if not args.only_append:
            app_configs = remove_stale_entries(app_configs, tibia_pids)

        if not args.only_cleanup:
            app_configs = append_new_entries(app_configs, tibia_pids)

        print(f"Successfully updated {args.app_config}")

    if args.command == "find_addresses":
        app_configs = find_memory_addresses(args, app_configs)

    if not args.dry_run:
        write_app_config(app_configs, args.app_config)
    else:
        print(app_configs)


if __name__ == "__main__":
    main(parse_args())
