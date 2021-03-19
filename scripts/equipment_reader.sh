#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
EQUIPMENT_READER_BIN="${ROOT_PATH}/reader/equipment_reader.py"

function python_bin {
  PYTHONPATH=${PYTHONPATH} python3.8 "$@"
}

python_bin ${EQUIPMENT_READER_BIN} "$@"
