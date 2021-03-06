#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/src"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"


function python_bin {
  PYTHONPATH=${PYTHONPATH} python3.8 "$@"
}

python_bin ${RECONNECTOR_BIN} "$@"
