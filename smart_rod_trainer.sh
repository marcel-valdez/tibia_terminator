#!/usr/bin/env bash
# requirements: xdotool

EQUIP_RING_ROH_KEY='n'
EQUIP_RING_LR_KEY='u'
EAT_FOOD_KEY='h'
DRINK_POTION_KEY='m'
CAST_RUNE_SPELL_KEY='y'
EQUIP_SOFT_BOOTS_KEY='j'
USE_EXERCISE_ROD_KEY='k'
EXERCISE_DUMMY_CENTER_X=846
EXERCISE_DUMMY_CENTER_Y=213
SCREEN_NO=0
MIN_SOUL_POINTS=6


function debug() {
  [[ "${DEBUG}" ]] && echo "$@" >&2
}

function random() {
  local min=$1
  local max=$2
  local delta=$((max - min))
  echo $((min + (RANDOM % (delta + 1))))
}

function timestamp_secs() {
  date "+%s"
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
  [[ ${MANA} -gt ${max_mana_threshold} ]] || \
    [[ ${SOUL_POINTS} -lt ${MIN_SOUL_POINTS} ]]
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
  if [[ ${SOUL_POINTS} -lt 6 ]]; then
    echo '-------------------'
    echo 'Equipping life ring'
    echo '-------------------'
  fi

  send_keystroke "${tibia_window}}" "${EQUIP_RING_LR_KEY}" 1
  if [[ ${SOUL_POINTS} -ge 6 ]]; then
    echo '-------------------------'
    echo 'Equipping ring of healing'
    echo '-------------------------'
    local wait_time="0.$(random 250 390)s"
    sleep "${wait_time}"
    send_keystroke "${tibia_window}}" "${EQUIP_RING_ROH_KEY}" 1
  fi
}

function is_ring_slot_empty() {
  local tibia_window="$1"
  ./equipment_reader.py --check_slot_empty 'ring' "${tibia_window}"
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
  send_keystroke "${tibia_window}}" "${EQUIP_SOFT_BOOTS_KEY}" 2
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
  send_keystroke "${tibia_window}" "${EAT_FOOD_KEY}" 1 1
  sleep "1s"
  send_keystroke "${tibia_window}" "${EAT_FOOD_KEY}" 1 1
  sleep "1s"
  send_keystroke "${tibia_window}" "${EAT_FOOD_KEY}" 1 1
  sleep "1s"
  send_keystroke "${tibia_window}" "${EAT_FOOD_KEY}" 1 1
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
  send_keystroke "${window}" "${CAST_RUNE_SPELL_KEY}" "${min}" "${max}"
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
  while [[ ${mana} -ge ${mana_per_rune} ]] && \
        [[ ${soul_pts} -ge ${MIN_SOUL_POINTS} ]]; do
    make_rune "${tibia_window}"
    mana=$(get_mana)
    sleep "1s"
    soul_pts=$(get_soul_pts)
  done
}

function wait_for_mana() {
  local tibia_window="$1"
  # Wait until mana is nearly full
  echo
  echo '-------------------------------'
  echo "| Waiting for mana until ${max_mana_threshold} |"
  echo '-------------------------------'
  echo
  local mana=$(get_mana)
  while [[ ${mana} -lt ${max_mana_threshold} ]]; do
    # Warning: If we run out of life rings, the ring slot will be empty
    # every time we're under 10 soul points. So we'd end up using the exercise
    # rod very often and thereby switching windows very often as well.
    if ! is_out_of_souls_or_max_mana && is_ring_slot_empty "${tibia_window}"; then
      local secs_since_last_use=$((secs_since_last_rod_use))
      # only equip regen ring if it has been at least 30 seconds since the last
      # time we used the exercise rod.
      if secs_since_last_rod_use -gt 30; then
        equip_regen_ring "${tibia_window}"
        equip_soft_boots "${tibia_window}"
        eat_food "${tibia_window}"
        # We have to re-use the rod, since equipping the ring will stops the
        # rod training.
        use_exercise_rod "${tibia_window}"
      fi
    fi

    if [[ "${pending_rod_usage}" ]];  then
        use_exercise_rod "${tibia_window}"
    fi
    sleep "3s"
    if [[ "${credentials_profile}" ]] && is_logged_out; then
        sleep "$(random 180 300)s"
        login
    fi
    local msg="Mana: ${mana}/${max_mana_threshold}  "
    local overwrite=$(printf '\\b%0.s' $(seq 1 ${prev_msg_len}))
    local prev_msg_len=${#msg}
    printf "${overwrite}${msg}"
    mana=$(get_mana)
  done
  echo
}

function click_dummy() {
  local tibia_window=$1
  local minX=$((EXERCISE_DUMMY_CENTER_X-4))
  local maxX=$((EXERCISE_DUMMY_CENTER_X+4))
  local minY=$((EXERCISE_DUMMY_CENTER_Y-4))
  local maxY=$((EXERCISE_DUMMY_CENTER_Y+4))
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 100 250)s"
  echo "Pausing ${wait_time}" &
  sleep "${wait_time}"

  echo "Clicking dummy (${X},${Y})" &
  xdotool mousemove --screen "${SCREEN_NO}" "${X}" "${Y}"
  xdotool click --window "${tibia_window}" --delay "$(random 100 250)" 1
}

last_rod_usage=0
pending_rod_usage=
function secs_since_last_rod_use() {
  local curr_timestamp=$(timestamp_secs)
  local secs_since_last_use=$((curr_timestamp-last_rod_usage))
  echo ${secs_since_last_use}
}

function use_exercise_rod() {
  local secs_since_last_use=$(secs_since_last_rod_use)
  if [[ ${secs_since_last_use} -le 30 ]]; then
    printf "Unable to use exercise rod yet, it has only been " >&2
    echo "${secs_since_last_use} secs since last use." >&2
    pending_rod_usage=1
    return 1
  else
    pending_rod_usage=
  fi
  # get current focused window
  local tibia_window="$1"
  eval "$(xdotool getmouselocation --shell)"
  local curr_x="${X}"
  local curr_y="${Y}"
  local curr_screen="${SCREEN}"
  local curr_window="${WINDOW}"
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
    focus_window "${tibia_window}"
  fi

  send_keystroke "${tibia_window}" "${USE_EXERCISE_ROD_KEY}" 1 1
  click_dummy "${tibia_window}"
  last_rod_usage=$(timestamp_secs)

  # return to prev window
  if [[ ${refocus_tibia_to_train} ]]; then
    sleep "0.$(random 100 250)s"
    xdotool mousemove --screen "${curr_screen}" \
            "${curr_x}" "${curr_y}"
    focus_window "${curr_window}"
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
