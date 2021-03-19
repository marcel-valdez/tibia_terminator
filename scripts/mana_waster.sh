#!/usr/bin/env bash
# requirements: xdotool

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
CHAR_READER_BIN="${ROOT_PATH}/reader/char_reader38.py"
RECONNECTOR_BIN="${ROOT_PATH}/tibia_reconnector.py"

function python_bin {
  PYTHONPATH=${PYTHONPATH} python3.8 "$@"
}

function sudo_python_bin {
  sudo PYTHONPATH=${PYTHONPATH} python3.8 "$@"
}

SCREEN_WIDTH_PIXELS=1920
CHAR_POS_Y=380
CHAR_POS_X=960
MANA_POTION_Y=300
MANA_POTION_X=1715
LEFT_BTN="1"

function debug() {
  [[ "${DEBUG}" ]] && echo "$@" >&2
}

function random() {
  local min=$1
  local max=$2
  local delta=$((max - min))
  echo $((min + (RANDOM % (delta + 1))))
}


function send_keystroke() {
  local keystroke="$1"
  local min="$2"
  [[ -z "${min}" ]] && min=2
  local max="$3"
  [[ -z "${max}" ]] && max=2
  local reps=$(random ${min} ${max})
  for i in $(seq 1 ${reps}); do
    local delay="$(random 123 257)"
    echo "Sending ${keystroke} with delay 0.${delay}s"
    xdotool key --delay "${delay}" --window "${tibia_window}" "${keystroke}"
    local wait_time="0.$(random 110 350)s"
    echo "Pausing ${wait_time}"
    sleep "${wait_time}"
  done
}

function sec_per_rune() {
  echo $((mana_per_spell / mana_per_sec))
}

function get_tibia_window_id() {
  echo $(xdotool search --pid ${tibia_pid})
}

function timestamp_ms() {
  date "+%s%N" | cut -b1-13
}

function is_out_of_souls_or_mana() {
  eval "$(sudo_python_bin ${CHAR_READER_BIN} --pid ${tibia_pid})"
  echo "mana: ${MANA}, soul points: ${SOUL_POINTS}"
  # do not drink mana if we're at /maximum char mana
  # do not drink mana if we're running out of soul points.
  [[ ${MANA} -gt ${max_mana_threshold} ]] || [[ ${SOUL_POINTS} -lt 6 ]]
}

function drink_mana_potion_click() {
  # click mana potion
  xdotool mousemove --window ${tibia_window} \
                    --sync ${MANA_POTION_X} ${MANA_POTION_Y} \
          sleep "0.125" \
          click --window ${tibia_window} ${LEFT_BTN} \
          sleep "0.125" \
          mousemove --window ${tibia_window} \
                    --sync ${CHAR_POS_X} ${CHAR_POS_Y} \
          sleep "0.125" \
          click --window ${tibia_window} ${LEFT_BTN}
}

function drink_mana_potion_keystroke() {
  send_keystroke 'm' 1 1
}

function drink_mana_potion() {
  local mana="$(get_mana)"
  # don't drink a mana potion if we have enough mana for a spell
  if [[ ${mana} -ge ${mana_per_spell} ]] || \
     [[ ${mana} -ge ${mana_per_secondary_spell} ]]; then
    return 1
  fi

  if [[ ${click_for_potion} ]]; then
    drink_mana_potion_click
  else
    drink_mana_potion_keystroke
  fi
}

function send_spell_keystroke() {
  # call the rune spell a random number of times between 2 and 5
  local spell_key="$1"
  local min=$2
  [[ -z "${min}" ]] && min=2
  local max=$3
  [[ -z "${min}" ]] && max=5

  echo '------------------'
  echo '   Casting spell  '
  echo '------------------'
  send_keystroke "${spell_key}" ${min} ${max}
}


function eat_food() {
  local mana=$(get_mana)
  if [[ ${mana} -ge ${max_char_mana} ]]; then
    return 1
  fi
  # call the eat command a random number between 0 and 3
  # we don't want to always issue the eat command
  echo '-----------'
  echo 'Eating food'
  echo '-----------'
  send_keystroke 'h' 0 3
}

function get_mana() {
  eval "$(sudo_python_bin ${CHAR_READER_BIN} --pid ${tibia_pid})"
  echo "${MANA}"
}

function cast_secondary_spell() {
  eval "$(sudo_python_bin ${CHAR_READER_BIN} --pid ${tibia_pid})"
  if [[ ${MANA} -gt ${mana_per_secondary_spell} ]]; then
    send_spell_keystroke 'p' 1 1
  fi
}


function cast_spell() {
  eval "$(sudo_python_bin ${CHAR_READER_BIN} --pid ${tibia_pid})"
  if [[ ${MANA} -gt ${mana_per_spell} ]]; then
    send_spell_keystroke 'y' 1 1
  fi
}


function is_logged_out {
  ! python_bin "${RECONNECTOR_BIN}" --check_if_ingame "${tibia_pid}"
}

function login {
  python_bin "${RECONNECTOR_BIN}" --login \
    --credentials_profile "${credentials_profile}" \
    "${tibia_pid}"

  if [[ $? -ne 0 ]]; then
    echo "Failed log back into the game." >&2
    echo "Runemaker is quitting." >&2
    exit 1
  fi
}

function waste_mana() {
  tibia_window=$(get_tibia_window_id)
  while true; do
    if [[ "${credentials_profile}" ]] && is_logged_out; then
      echo "We were disconnected. We will attempt login after 3-5 minutes."
      # Sleep 4-6 minutes before attempting to log back in, otherwise we may get
      # an exceptional disconnection message from which we can't recover (yet)
      # in the Tibia client.
      sleep "$(random 180 300)s"
      login
    fi

    local mana=$(get_mana)
    while [[ ${mana} -ge ${mana_per_spell} ]]; do
      cast_spell
      sleep "0.$(random 210 550)s"
      mana=$(get_mana)
    done

    while [[ ${mana} -ge ${mana_per_secondary_spell} ]]; do
      cast_secondary_spell
      sleep "0.$(random 210 550)s"
      mana=$(get_mana)
    done
    drink_mana_potion
    sleep "0.$(random 125 250)s"
    eat_food
  done
}

tibia_pid=
credentials_profile=
mana_per_spell=
mana_per_secondary_spell=99999
max_mana_threshold=99999
max_char_mana=
click_for_potion=
screen="left"
function parse_args() {
  while [[ $# -gt 0 ]]; do
    arg=$1
    case $arg in
    --max-char-mana)
      max_char_mana=$2
      shift
      ;;
    --mana-per-spell)
      mana_per_spell=$2
      shift
      ;;
    --mana-per-secondary-spell)
      mana_per_secondary_spell=$2
      shift
      ;;
    --tibia-pid)
      tibia_pid=$2
      shift
      ;;
    --credentials-profile)
      credentials_profile=$2
      shift
      ;;
    --click-for-potion)
      click_for_potion=1
      shift
      ;;
    *)
      break
      ;;
    esac
    shift
  done

  if [[ -z "${max_char_mana}" ]]; then
    echo "You need to provide the maximum char mana. (--max-char-mana <amount>)" >&2
    exit 1
  fi

  if [[ -z "${tibia_pid}" ]]; then
    echo "You need to provide the Tibia PID. (--tibia-pid <PID>)" >&2
    exit 1
  fi
  echo "Tibia PID: ${tibia_pid}"

  if [[ -z "${mana_per_spell}" ]]; then
    echo "You need to provide the mana cost per spell. (--mana-per-spell <amount>)" >&2
    exit 1
  fi
  echo "Mana per spell: ${mana_per_spell}"

  if [[ ${mana_per_secondary_spell} -ne 99999 ]]; then
    echo "Mana per secondary spell: ${mana_per_secondary_spell}"
  fi
}

function main() {
  parse_args "$@"
  waste_mana
}

main "$@"
