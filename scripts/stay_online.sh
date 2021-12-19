#!/usr/bin/env bash

tibia_pid=$1

SCRIPT="$(basename $0)"

function usage() {
    cat<<EOF
${SCRIPT} --keys|-k <"key1 key2 key3..."> --pid|-p <PID> [--help]

--keys: Keys to send sequentially to the Tibia client in a loop with 1 second apart every 1 minute.
--pid: Process ID (PID) of the Tibia client.
--help: Shows this help message.

Example:
${SCRIPT} --keys "F1 F2 F3" --pid 12356
EOF
}

function parse_args() {
  while [[ $# -gt 0 ]]; do
    arg=$1
    case $arg in
        --pid|-p)
            tibia_pid=$2
            shift
            ;;
        --keys|-k)
            keys=($2)
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown parameter $1" >&2
            exit 1
            ;;
    esac
    shift
  done
}

function get_tibia_wid() {
  if [[ "${tibia_pid}" ]]; then
    echo $(xdotool search --pid ${tibia_pid} | tail -1)
  else
    echo $(xdotool search --class Tibia)
  fi
}

function main() {
    tibia_wid=$(get_tibia_wid "${tibia_pid}")
    local overwrite=$(printf '\\b%0.s' $(seq 1 50))
    echo "tibia_wid=${tibia_wid}"
    while true; do
        for key in ${keys[@]}; do
            printf "${overwrite}Sending key ${key}."
            xdotool key --window "${tibia_wid}" "${key}"
            sleep 1
        done
        local counter=60
        while [[ ${counter} -gt 0 ]]; do
            sleep 1
            counter=$((counter-1))
            printf "${overwrite}Sleeping ${counter} seconds." &
        done
    done
}

parse_args "$@"
main
