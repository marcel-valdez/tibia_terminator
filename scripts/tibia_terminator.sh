#!/usr/bin/env bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
TERMINATOR_PATH="$(dirname ${SCRIPT_PATH})"
export PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"

function sudo_python_bin {
  sudo python3.8 "$@"
}

pushd "${TERMINATOR_PATH}" >/dev/null
trap popd >/dev/null SIGINT SIGTERM

sudo_python_bin -m tibia_terminator start "$@"

