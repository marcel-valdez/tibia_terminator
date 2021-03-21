#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"

PYTHONPATH="${PYTHONPATH}" python3.8 -m unittest discover -t "${ROOT_PATH}" -s "${ROOT_PATH}/tests"
