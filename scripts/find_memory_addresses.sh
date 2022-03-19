#!/usr/bin/env bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname "${SCRIPT_PATH}")"
[[ -z "${TERMINATOR_PATH}" ]] && TERMINATOR_PATH="${ROOT_PATH}/tibia_terminator"
[[ -z "${PYTHONPATH}" ]] && PYTHONPATH="${PYTHONPATH}:${TERMINATOR_PATH}"
[[ -z "${APP_CONFIG_PATH}" ]] && \
    APP_CONFIG_PATH="${TERMINATOR_PATH}/app_config.json"
[[ -z "${TIBIA_WINDOW_CONFIG_PATH}" ]] && \
    TIBIA_WINDOW_CONFIG_PATH="${ROOT_PATH}/char_configs/tibia_window_config.json"
[[ -z "${HOTKEYS_CONFIG_PATH}" ]] && \
    HOTKEYS_CONFIG_PATH="${ROOT_PATH}/char_configs/hotkeys_config.json"

function parse_args {
    TIBIA_PID="$1"
    if [[ -z ${TIBIA_PID} ]]; then
        echo "You must specify the Tibia PID to find the memory addresses of." >&2
        exit 1
    fi
}

function clean_exit() {
    popd &>/dev/null
    exit
}

pushd "${HOME}/projects/tibia_bot"
trap clean_exit SIGINT EXIT SIGKILL SIGTERM

[[ -z "${PYTHON_BIN}" ]] && PYTHON_BIN="$(type -p python3.8)"
[[ -z "${DISPLAY}" ]] && DISPLAY=":0"
export DISPLAY
[[ -z "${DEBUG}" ]] && DEBUG=1
export DEBUG
export PYTHONPATH

function find_memory_addresses() {
    sudo -E "${PYTHON_BIN}" -m tibia_terminator.tools.app_config_manager \
         "${APP_CONFIG_PATH}" \
         find_addresses \
         --tibia_window_config "${TIBIA_WINDOW_CONFIG_PATH}" \
         --hotkeys_config "${HOTKEYS_CONFIG_PATH}" \
         --pid "${TIBIA_PID}"
}

function main() {
    local retry_count=3
    while [[ ${retry_count} -gt 0 ]]; do
        if find_memory_addresses; then
            exit 0
        fi
        retry_count=$((retry_count-1))
    done
    echo "FATAL: Unable to find memory addresses after 3 attempts." >&2
    exit 1
}

parse_args "$@"
main
