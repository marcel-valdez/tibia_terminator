#!/usr/bin/env bash
# requirements: xdotool

function debug() {
  [[ "${DEBUG}" ]] && echo "$@" >&2
}

function random() {
  local min=$1
  local max=$2
  local delta=$((max - min))
  echo $((min + (RANDOM % (delta + 1))))
}

function get_tibia_window_id() {
  if [[ "${tibia_pid}" ]]; then
    echo $(xdotool search --pid ${tibia_pid})
  else
    echo $(xdotool search --class Tibia)
  fi
}

function focus_window() {
  local window_id=$1
  xdotool windowactivate --sync "${window_id}"
}

function get_mana() {
  if [[ "${tibia_pid}" ]]; then
    eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  else
    eval "$(sudo ./char_reader.py)"
  fi
  echo "${MANA}"
}

function get_soul_pts() {
  if [[ "${tibia_pid}" ]]; then
    eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  else
    eval "$(sudo ./char_reader.py)"
  fi
  echo "${SOUL_POINTS}"
}

function is_out_of_souls_or_max_mana() {
  if [[ "${tibia_pid}" ]]; then
    eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  else
    eval "$(sudo ./char_reader.py)"
  fi
  [[ ${MANA} -gt ${max_mana_threshold} ]] || [[ ${SOUL_POINTS} -lt 6 ]]
}

function send_keystroke() {
  local window="$1"
  local keystroke="$2"
  local min="$3"
  [[ -z "${min}" ]] && min=2
  local max="$4"
  [[ -z "${max}" ]] && max=2
  local reps=$(random ${min} ${max})
  for i in $(seq 1 ${reps}); do
    local delay="$(random 123 257)"
    echo "Sending ${keystroke} with delay 0.${delay}s"
    xdotool key --delay "${delay}" --window "${window}" "${keystroke}"
    local wait_time="0.$(random 110 350)s"
    echo "Pausing ${wait_time}"
    sleep "${wait_time}"
  done
}

function equip_regen_ring() {
  # Use/Equip all mana regen items:
  #   In order to equip regen ring:
  #     if soul pts are higher than 10: equip secondary then primary ring
  #     else if soul pts are greater than 5: equip the secondary one
  #     else: do not equip any ring

  local tibia_window="$1"
  if is_out_of_souls_or_max_mana; then
    return 1
  fi

  if [[ "${tibia_pid}" ]]; then
    eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  else
    eval "$(sudo ./char_reader.py)"
  fi
  if [[ ${SOUL_POINTS} -le 10 ]]; then
    echo '-------------------'
    echo 'Equipping life ring'
    echo '-------------------'
  fi

  send_keystroke "${tibia_window}}" 'u' 1
  if [[ ${SOUL_POINTS} -gt 10 ]]; then
    echo '-------------------------'
    echo 'Equipping ring of healing'
    echo '-------------------------'
    local wait_time="0.$(random 250 390)s"
    sleep "${wait_time}"
    # equip ring of healing
    send_keystroke "${tibia_window}}" 'n' 1
  fi
}

function equip_soft_boots() {
  local tibia_window="$1"
  if is_out_of_souls_or_max_mana; then
    return 1
  fi
  # equip soft boots
  echo '-------------------'
  echo 'Equipping soft boots'
  echo '-------------------'
  send_keystroke "${tibia_window}}" 'j' 1
}

function eat_food() {
  # Eat food 4 times with a 1.25-1.39 sec interval
  local tibia_window="$1"
  if is_out_of_souls_or_max_mana; then
    return 1
  fi
  echo '-----------'
  echo 'Eating food'
  echo '-----------'
  send_keystroke "${tibia_window}" 'h' 1 1
  sleep "1s"
  send_keystroke "${tibia_window}" 'h' 1 1
  sleep "1s"
  send_keystroke "${tibia_window}" 'h' 1 1
  sleep "1s"
  send_keystroke "${tibia_window}" 'h' 1 1
}

function cast_rune_spell() {
  local window="$1"
  local min="$2"
  [[ -z "${min}" ]] && min=1
  local max="$3"
  [[ -z "${min}" ]] && max=3

  echo '------------------'
  echo 'Calling rune spell'
  echo '------------------'
  send_keystroke "${window}" 'y' "${min}" "${max}"
}

function make_rune() {
  local window="$1"
  local min_wait="$2"
  local max_wait="$3"
  local mana=$(get_mana)
  if [[ ${mana} -ge ${mana_per_rune} ]]; then
    cast_rune_spell "${window}" "${min_wait}" "${max_wait}"
  fi
}

function consume_mana_for_runes() {
  # Use up all the mana until it is less than the mana required for the spell
  # or we have less than 6 soul points
  local tibia_window="$1"
  local mana=$(get_mana)
  sleep "1s"
  local soul_pts=$(get_soul_pts)
  while [[ ${mana} -ge ${mana_per_rune} ]] && [[ ${soul_pts} -ge 6 ]]; do
    make_rune "${tibia_window}"
    mana=$(get_mana)
    sleep "1s"
    soul_pts=$(get_soul_pts)
  done
}

function wait_for_mana() {
  # Wait until mana is nearly full
  echo
  echo '-------------------------------'
  echo "| Waiting for mana until ${max_mana_threshold} |"
  echo '-------------------------------'
  echo
  local mana=$(get_mana)
  while [[ ${mana} -lt ${max_mana_threshold} ]]; do
    sleep "3s"
    local msg="Mana: ${mana}/${max_mana_threshold}  "
    local overwrite=$(printf '\\b%0.s' $(seq 1 ${prev_msg_len}))
    local prev_msg_len=${#msg}
    printf "${overwrite}${msg}"
    mana=$(get_mana)
  done
  echo
}

function click_dummy() {
  local SCREEN=0
  local tibia_window=$1
  # x:941 y:257
  local minX=931
  local maxX=951
  local minY=247
  local maxY=267
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  echo "Pausing ${wait_time}" &
  sleep ${wait_time}

  echo "Clicking dummy (${X},${Y})" &
  xdotool mousemove --screen 0 ${X} ${Y}
  xdotool click --window "${tibia_window}" --delay $(random 125 250) 1
}

function use_exercise_rod() {
  # get current focused window
  local tibia_window="$1"
  eval "$(xdotool getmouselocation --shell)"
  local curr_x=${X}
  local curr_y=${Y}
  local curr_screen=${SCREEN}
  local curr_window=${WINDOW}
  debug "curr_x,y: ${curr_x}, ${curr_y}"
  debug "curr_screen=${curr_screen}"
  debug "curr_window=${curr_window}"

  # use exercise rod (k hotkey)
  echo "---------------------"
  echo "| Using exercise rod |"
  echo "---------------------"

  # focus tibia window
  if [[ ${refocus_tibia_to_train} ]]; then
    echo "Focusing Tibia window..."
    focus_window ${tibia_window}
  fi

  send_keystroke "${tibia_window}" 'k' 1 1
  click_dummy "${tibia_window}"

  # return to prev window
  if [[ ${refocus_tibia_to_train} ]]; then
    sleep "0.$(random 110 550)s"
    xdotool mousemove --screen ${curr_screen} \
            ${curr_x} ${curr_y}
    focus_window ${curr_window}
  fi
}

function is_logged_out {
  ! ./tibia_reconnector.py --check_if_ingame "${tibia_pid}"
}

function login {
 ./tibia_reconnector.py --login \
    --credentials_profile "${credentials_profile}" \
    "${tibia_pid}"

  if [[ $? -ne 0 ]]; then
    echo "Failed log back into the game." >&2
    echo "Smart rod trainer is quitting." >&2
    exit 1
  fi
}

function train() {
  local tibia_window=$(get_tibia_window_id)
  while true; do
    if [[ "${credentials_profile}" ]] && is_logged_out; then
        sleep "$(random 180 300)s"
        login
    fi

    sleep "0.$(random 210 550)s"
    consume_mana_for_runes "${tibia_window}"
    equip_regen_ring "${tibia_window}"
    equip_soft_boots "${tibia_window}"
    eat_food "${tibia_window}"
    use_exercise_rod "${tibia_window}"
    if [[ "${credentials_profile}" ]] && is_logged_out; then
        sleep "$(random 180 300)s"
        login
    fi

    wait_for_mana "${tibia_window}"
  done
}

refocus_tibia_to_train=
mana_per_rune=
max_char_mana=
max_mana_threshold=
credentials_profile=
tibia_pid=
function parse_args() {
  while [[ $# -gt 0 ]]; do
    arg=$1
    case ${arg} in
    --tibia-pid)
      tibia_pid=$2
      shift
      ;;
    --credentials-profile)
      credentials_profile=$2
      shift
      ;;
    --mana-per-rune)
      mana_per_rune=$2
      shift
      ;;
    --refocus-tibia-to-train)
      refocus_tibia_to_train=1
      ;;
    --max-char-mana)
      max_char_mana=$2
      max_mana_threshold=$((${max_char_mana} - 200))
      shift
      ;;
    *)
      echo "Unknown parameter: $1" >&2
      exit 1
      ;;
    esac
    shift
  done

  if [[ -z "${max_char_mana}" ]]; then
    echo "You need to provide the maximum character mana (--max-char-mana <amount>" >&2
    exit 1
  fi

  if [[ -z "${mana_per_rune}" ]]; then
    echo "You need to provide the mana cost per rune. (--mana-per-rune <amount>)" >&2
    exit 1
  fi

  if [[ "${refocus_tibia_to_train}" ]]; then
    echo "We will refocus the Tibia window to make a rune (and then return focus to the original window)."
  else
    echo "We will not refocus the Tibia window to use the exercise dummy (risky / unpredictable)."
  fi

  echo "Mana per rune spell: ${mana_per_rune}"
  echo "Maximum character mana: ${max_char_mana}"
}

function main() {
  parse_args "$@"
  train
}

main "$@"
