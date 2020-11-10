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


function send_keystroke() {
  local tibia_window="$1"
  local keystroke="$2"
  local min="$3"
  [[ -z "${min}" ]] && min=2
  local max="$4"
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

function mana_potion_count() {
  echo $(((mana_per_spell / 100) - 1))
}

function get_tibia_window_id() {
  echo $(xdotool search --pid ${tibia_pid})
}

function timestamp_ms() {
  date "+%s%N" | cut -b1-13
}

function is_out_of_souls_or_mana() {
  eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  echo "mana: ${MANA}, soul points: ${SOUL_POINTS}"
  # do not drink mana if we're at /maximum char mana
  # do not drink mana if we're running out of soul points.
  [[ ${MANA} -gt ${max_mana_threshold} ]] || [[ ${SOUL_POINTS} -lt 6 ]]
}

potions_seq_counter=0
function get_potion_count() {
  local mana_potions_seq_len=${#mana_potions_seq[@]}
  if [[ ${mana_potions_seq_len} -gt 0 ]]; then
    debug "mana_potions_seq_len=${mana_potions_seq_len}"
    debug "potions_seq_counter=${potions_seq_counter}"
    local seq_idx=$((potions_seq_counter % mana_potions_seq_len))
    debug "seq_idx=${seq_idx}"
    echo ${mana_potions_seq[seq_idx]}
  else
    echo $(random ${min_mana_potions_per_turn} ${max_mana_potions_per_turn})
  fi
}

function drink_mana_potion() {
  local tibia_window=$1
  local mana="$(get_mana)"
  # don't drink a mana potion if we have enough mana for a spell
  if [[ ${mana} -ge ${mana_per_spell} ]] || \
     [[ ${mana} -ge ${mana_per_secondary_spell} ]]; then
    return 1
  fi

  send_keystroke "${tibia_window}" 'm' 1 1
}

function send_spell_keystroke() {
  # call the rune spell a random number of times between 2 and 5
  local tibia_window="$1"
  local spell_key="$2"
  local min=$3
  [[ -z "${min}" ]] && min=2
  local max=$4
  [[ -z "${min}" ]] && max=5

  echo '------------------'
  echo '   Casting spell  '
  echo '------------------'
  send_keystroke "${tibia_window}" "${spell_key}" ${min} ${max}
}


function eat_food() {
  local tibia_window="$1"
  local mana=$(get_mana)
  if [[ ${mana} -ge ${max_char_mana} ]]; then
    return 1
  fi
  # call the eat command a random number between 0 and 3
  # we don't want to always issue the eat command
  echo '-----------'
  echo 'Eating food'
  echo '-----------'
  send_keystroke "${tibia_window}" 'h' 0 3
}

function get_mana() {
  eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  echo "${MANA}"
}

function cast_secondary_spell() {
  local tibia_window="$1"
  eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  if [[ ${MANA} -gt ${mana_per_secondary_spell} ]]; then
    send_spell_keystroke "${tibia_window}" 'p' 1 1
  fi
}


function cast_spell() {
  local tibia_window="$1"
  eval "$(sudo ./char_reader.py --pid ${tibia_pid})"
  if [[ ${MANA} -gt ${mana_per_spell} ]]; then
    send_spell_keystroke "${tibia_window}" 'y' 2 2
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
    echo "Runemaker is quitting." >&2
    exit 1
  fi
}

function waste_mana() {
  local tibia_window=$(get_tibia_window_id)
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
      cast_spell "${tibia_window}"
      sleep "0.$(random 210 550)s"
      mana=$(get_mana)
    done

    while [[ ${mana} -ge ${mana_per_secondary_spell} ]]; do
      cast_secondary_spell "${tibia_window}"
      sleep "0.$(random 210 550)s"
      mana=$(get_mana)
    done
    drink_mana_potion "${tibia_window}"
    eat_food "${tibia_window}"
  done
}

tibia_pid=
credentials_profile=
mana_per_spell=
mana_per_secondary_spell=99999
max_mana_threshold=99999
max_char_mana=
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
