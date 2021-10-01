#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
CHAR_READER_BIN="${ROOT_PATH}/reader/char_reader38.py"
PYTHON_BIN="$(type -p python3.8)"
function sudo_python_bin {
  sudo -E PYTHONPATH="${PYTHONPATH}" "${PYTHON_BIN}" "$@"
}

sudo_python_bin "${CHAR_READER_BIN}" "$@"
