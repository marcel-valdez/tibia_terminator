#!/usr/bin/env bash
# requirements: xdotool

function debug {
  [[ ! -z "${DEBUG}" ]] && echo "$@" >&2
}

function random {
  local min=$1
  local max=$2
  local delta=$((max - min))
  echo $((min + (RANDOM%(delta+1)) ))
}

function click_weapon {
  local SCREEN=0
  local tibia_window=$1
  # middle is X=1596,Y=35
  local minX=1586
  local maxX=1606
  local minY=25
  local maxY=45
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  echo "Pausing ${wait_time}" &
  sleep ${wait_time}

  echo "Clicking weapon (${X},${Y})" &
  xdotool mousemove --screen 0 ${X} ${Y}
  xdotool click --window ${tibia_window} --delay $(random 125 250) 1
}

function click_dummy {
  local SCREEN=0
  local tibia_window=$1
  # middle is X=960,Y=424
  local minX=950
  local maxX=970
  local minY=415
  local maxY=434
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  echo "Pausing ${wait_time}" &
  sleep ${wait_time}

  echo "Clicking dummy (${X},${Y})" &
  xdotool mousemove --screen 0 ${X} ${Y}
  xdotool click --window ${tibia_window} --delay $(random 125 250) 1
}

function get_current_window_id {
  echo $(xdotool getactivewindow)
}

function get_tibia_window_id {
  echo $(xdotool search --class Tibia)
}

function focus_window {
  local window_id=$1
  xdotool windowactivate --sync "${window_id}"
}

function timestamp_ms {
  date "+%s%N" | cut -b1-13
}

function wait_ui {
  local wait_time_secs="$1"
  local wait_time_ms=$((wait_time_secs * 1000))
  local start_timestamp_ms=$(timestamp_ms)
  sleep "${wait_time_secs}s" & local wait_pid=$!

  echo
  local prev_msg_len=0
  while kill -0 ${wait_pid} 2>/dev/null; do
    local current_timestamp_ms=$(timestamp_ms)
    local elapsed_time_ms=$((current_timestamp_ms - start_timestamp_ms))
    local remaining_time_ms=$((wait_time_ms - elapsed_time_ms))
    if [[ ${remaining_time_ms} -gt 0 ]]; then
      local remaining_time_sec=$((remaining_time_ms / 1000))
      local msg="Waiting ${remaining_time_sec}s  "
      local overwrite=$(printf '\\b%0.s' $(seq 1 ${prev_msg_len}))
      local prev_msg_len=${#msg}
      printf "${overwrite}${msg}"
    fi
  done
  echo
  echo
}

function train {
  while true; do
    # get current focused window
    eval "$(xdotool getmouselocation --shell)"
    local curr_x=${X}
    local curr_y=${Y}
    local curr_screen=${SCREEN}
    local curr_window=${WINDOW}
    debug "curr_x,y: ${curr_x}, ${curr_y}"
    debug "curr_screen=${curr_screen}"
    debug "curr_window=${curr_window}"

    # focus tibia window
    local tibia_window=$(get_tibia_window_id)
    if [[ ${refocus_tibia_to_make_rune} ]]; then
      focus_window ${tibia_window}
    fi

    click_weapon "${tibia_window}"
    sleep "0.$(random 210 550)s"
    click_dummy "${tibia_window}"


    # return to prev window
    sleep "1.$(random 110 990)s"
    if [[ ${refocus_tibia_to_make_rune} ]]; then
      xdotool mousemove --screen ${curr_screen}\
              ${curr_x} ${curr_y}
      focus_window ${curr_window}
    fi

    # sit until next rune spell with randomization
    wait_ui 60
  done
}

train
