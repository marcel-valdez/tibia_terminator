#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/src"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
PYTHON_BIN="$(type -p python3.8)"

function python_bin {
  PYTHONPATH=${PYTHONPATH} "${PYTHON_BIN}" "$@"
}

python_bin ${RECONNECTOR_BIN} "$@"
