#!/usr/bin/env bash


# usage
# rune_maker_strategies.sh <script> <time in minutes> <script> <time in minutes>
# 0 on last to run forever



script_pid=

function kill_strat {
  if [[ ! -z ${script_pid} ]]; then
    kill -9 ${script_pid}
    script_pid=
  fi
}
trap kill_strat EXIT

function sigint_exit {
  kill_strat
  exit
}
trap sigint_exit SIGINT


function main {
  local args="$@"
  IFS=', ' read -r -a strategies <<< "${args}"
  local strategies_len=${#strategies[@]}
  strategies_len=$((strategies_len / 2))

  for i in $(seq 0 $((strategies_len - 1))); do
    local script="${strategies[$((i*2))]}"
    local time_min="${strategies[$((i*2 + 1))]}"

    if [[ ${time_min} -gt 0 ]]; then
      echo "Strategy: ${script} will run for ${time_min} minutes."
      "${script}" &
      script_pid=$!
      sleep "${time_min}m"
      kill_strat
    else
      # keep running the strat forever
      echo "Strategy: ${script} will run forever."
      "${script}"
    fi
  done
}


main "$@"
