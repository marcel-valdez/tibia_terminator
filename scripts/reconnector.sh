#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
RECONNECTOR_BIN="${ROOT_PATH}/tibia_reconnector.py"
PYTHON_BIN="$(type -p python3.8)"

function python_bin {
  PYTHONPATH=${PYTHONPATH} "${PYTHON_BIN}" "$@"
}

python_bin ${RECONNECTOR_BIN} "$@"
