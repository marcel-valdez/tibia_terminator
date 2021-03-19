#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
EQUIPMENT_READER_BIN="${ROOT_PATH}/reader/equipment_reader.py"

function python_bin {
  PYTHONPATH=${PYTHONPATH} python3.8 "$@"
}

# Run this script while resizing the Tibia playable area until the
# equipment status read by Tibia terminator matches what you see
# on screen.
# Example:
# 1. Setup your character to have the action bar hotkeys set:
#    - Emergency Amulet: 10th slot [right to left, upper bar]
#    - Emergency Ring: 9th slot [right to left, upper bar]
#    - Normal Ring: 10th slot [right to left, lower bar]
#    - Normal Amulet: 9th slot [right to left, lower bar]
#    - Utamo vita: 7th slot [right to left, lower bar]
# 2. Equip the emergency amulet and ring on your character.
# 3. Execute this script: ./screen_resize_monitor.sh
# 4. Resize your screen until it prints out the CORRECT name of your emergency
#    ring, emergency amulet, equipped amulet, equipped ring and magic shield
#    status.
#    - Set tibia in full screen mode.
#    - Configure tibia to resize proportionally.
#    - Approximate vertical size is at y=698. Use the mouse location indicator
#      to adjust the size accordingly.

function __screen_resize_monitor {
  echo "mouse location: $(xdotool getmouselocation)"
  python_bin "${EQUIPMENT_READER_BIN}" --equipment_status dummy_wid
}

export -f __screen_resize_monitor

watch -n 0.1 -x bash -c __screen_resize_monitor
