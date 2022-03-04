#!/usr/bin/env python3.8

import sys
import psutil
import commentjson as json

from typing import Iterable, List


from tibia_terminator.schemas.app_config_schema import (
    AppConfigsSchema,
    AppConfigs,
    AppConfig,
)
from argparse import ArgumentParser, Namespace


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog=(
            "AppConfig Manager: Tool to load and generate Tibia Terminator App Configs"
        )
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
    parser.add_argument(
        "--only_cleanup",
        help=("Tells this tool to only cleanup stale entries in the AppConfig" "file."),
        action="store_true",
    )
    parser.add_argument(
        "--only_append",
        help=("Tells this tool to only append entries to the AppConfig file."),
        action="store_true",
    )
    return parser.parse_args()


def get_tibia_pids() -> Iterable[int]:
    for proc in psutil.process_iter():
        for arg in proc.cmdline():
            if "Tibia" in arg:
                yield proc.pid


def remove_stale_entries(app_configs: AppConfigs, tibia_pids: List[int]) -> AppConfigs:
    configs = []
    default_pid = tibia_pids[0]
    if app_configs.default_pid in tibia_pids:
        default_pid = app_configs.default_pid

    for app_config in app_configs.configs:
        if app_config.pid in tibia_pids:
            configs.append(app_config)

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
        json.dump(
            AppConfigsSchema().dump(app_configs), fp, indent=4, sort_keys=True
        )


def read_app_configs(app_config_file: str) -> AppConfigs:
    return AppConfigsSchema().loadf(app_config_file)


def main(args: Namespace) -> None:
    app_configs = read_app_configs(args.app_config)
    tibia_pids = list(get_tibia_pids())
    if len(tibia_pids) == 0:
        print("There are no running Tibia process, nothing to do.")
        sys.exit(0)

    if not args.only_append:
        app_configs = remove_stale_entries(app_configs, tibia_pids)

    if not args.only_cleanup:
        app_configs = append_new_entries(app_configs, tibia_pids)

    write_app_config(app_configs, args.app_config)
    print(f"Successfully updated {args.app_config}")


if __name__ == "__main__":
    main(parse_args())
