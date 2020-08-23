#!/usr/bin/env bash

function random {
  local min=$1
  local max=$2
  local delta=$((max - min))
  echo $((min + (RANDOM%(delta+1)) ))
}

function send_keystroke {
  local window="$1"
  local keystroke="$2"
  local min="$3"
  [[ -z ${min} ]] && min=2
  local max="$4"
  [[ -z ${max} ]] && max=2
  local reps=$(random ${min} ${max})
  for i in $(seq 1 ${reps}); do
    local delay="$(random 123 257)"
    echo "Sending ${keystroke} with delay 0.${delay}s"
    xdotool key --delay "${delay}" --window "${window}" "${keystroke}"
    local wait_time="0.$(random 1 3)$(random 1 5)s"
    echo "Pausing ${wait_time}"
    sleep "${wait_time}"
  done
}

function sec_per_rune {
  echo $((mana_per_rune / mana_per_sec))
}

function mana_potion_count {
  echo $(( (mana_per_rune / 100) - 1))
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

function drink_mana_potions {
  local window=$1
  local potion_count=$(random ${min_mana_potions_per_turn} ${max_mana_potions_per_turn})

  echo '-----------------------'
  echo "Drinking ${potion_count} mana potions"
  echo '-----------------------'
  for i in $(seq 1 ${potion_count}); do
    send_keystroke "${window}" 'm' 1 1
    local wait_time="0.$(random 3 5)$(random 1 6)s"
    echo "Pausing ${wait_time}"
    sleep "${wait_time}"

    # cast rune spell in case we have enough mana to use it again
    if [[ ! -z "${cast_rune_spell_after_drinking_potion}" ]]; then
      cast_rune_spell "${window}" 1 2
    fi
  done
}

function cast_rune_spell {
  # call the rune spell a random number of times between 2 and 5
  local window="$1"
  local min=$2
  [[ -z ${min} ]] && min=2
  local max=$3
  [[ -z ${min} ]] && max=5
  echo '------------------'
  echo 'Calling rune spell'
  echo '------------------'
  send_keystroke "${window}" 'y' ${min} ${max}
}

function make_rune {
  local window=$1
  cast_rune_spell "${window}"
  # call the eat command a random number between 0 and 3
  # we don't want to always issue the eat command
  echo '-----------'
  echo 'Eating food'
  echo '-----------'
  send_keystroke "${window}" 'h' 0 3
  # equip a life ring  a random number between 0 and 2
  # we don't want to always place the ring
  echo '-------------------'
  echo 'Equipping life ring'
  echo '-------------------'
  send_keystroke "${window}" 'n' 0 2

  drink_mana_potions "${window}"
}

function wait_for_mana {
  local sit_time_secs=$( random ${min_wait_per_turn} ${max_wait_per_turn}  )
  # only if using mana potions
  echo
  echo '------------------------'
  echo "| Waiting for mana ${sit_time_secs}s |"
  echo '------------------------'
  echo
  sleep "${sit_time_secs}s"
}

function manasit {
  while true; do
    # get current focused window
    local curr_window=$(get_current_window_id)

    # focus tibia window
    local tibia_window=$(get_tibia_window_id)
    if [[ ${refocus_tibia_to_make_rune} ]]; then
      focus_window ${tibia_window}
    fi

    # wait random time
    sleep "0.$(random 2 5)$(random 1 5)s"

    # make the rune
    make_rune "${tibia_window}"

    # return to prev window
    sleep "$(random 1 2).$(random 1 9)$(random 1 9)s"
    if [[ ${refocus_tibia_to_make_rune} ]]; then
      focus_window ${curr_window}
    fi

    # sit until next rune spell with randomization
    wait_for_mana
  done
}

mana_per_rune=
mana_per_sec=5
half_mana_potions=
cast_rune_spell_after_drinking_potion=
refocus_tibia_to_make_rune=
min_mana_potions_per_turn=
max_mana_potions_per_turn=
max_wait_per_turn=
min_wait_per_turn=
function parse_args {
  while [[ $# -gt 0 ]]; do
    arg=$1
    case $arg in
      --mana-per-rune)
        mana_per_rune=$2
        shift
        ;;
      --mana-per-sec)
        mana_per_sec=$2
        shift
        ;;
      --rune-spell-after-potion)
        cast_rune_spell_after_drinking_potion=1
        ;;
      --half-mana-potions)
        half_mana_potions=1
        ;;
      --refocus-tibia-to-make-rune)
        refocus_window_to_make_rune=1
        ;;
      --min-mana-potions-per-turn)
        min_mana_potions_per_turn=$2
        shift
        ;;
      --max-mana-potions-per-turn)
        max_mana_potions_per_turn=$2
        shift
        ;;
      --min-wait-per-turn)
        min_wait_per_turn=$2
        shift
        ;;
      --max-wait-per-turn)
        max_wait_per_turn=$2
        shift
        ;;
      *)
        break
        ;;
    esac
    shift
  done

  if [[ -z "${max_wait_per_turn}" ]]; then
    max_wait_per_turn=$(sec_per_rune)
  fi

  if [[ -z "${min_wait_per_turn}" ]]; then
    local tmp=$(sec_per_rune)
    min_wait_per_turn=$(( tmp / 2 ))
  fi

  if [[ ${min_mana_potions_per_turn} -gt ${max_mana_potions_per_turn} ]]; then
    echo "min-mana-potions-per-turn ${min_mana_potions_per_turn} is greater than \
max-mana-potions-per turn ${max_mana_potions_per_turn}" >&2
    exit 1
  fi

    if [[ ${min_wait_per_turn} -gt ${max_wait_per_turn} ]]; then
    echo "min-wait-per-turn ${min_wait_per_turn} is greater than\
max-wait-per turn ${max_wait_per_turn}" >&2
    exit 1
  fi
  
  if [[ ! -z "${half_mana_potions}" ]]; then
    echo "Using half the mana potions"
  fi

  if [[ -z "${mana_per_rune}" ]]; then
    echo "You need to provide the mana cost per rune. (--mana-per-rune <amount>)" >&2
    exit 1
  fi

  if [[ -z "${max_mana_potions_per_turn}" ]]; then
    max_mana_potions_per_turn=$(mana_potion_count)
  fi

  if [[ -z "${min_mana_potions_per_turn}" ]]; then
    min_mana_potions_per_turn=0
  fi

  if [[ ! -z "${cast_rune_spell_after_drinking_potion}}" ]]; then
    echo "We will cast the rune spell right after drinking potions."
  fi

  if [[ ! -z "${refocus_tibia_to_make_rune}" ]]; then
    echo "We will refocus the Tibia window to make a rune (and then return focus to the original window)."
  fi
  echo "Mana per rune spell: ${mana_per_rune}"
  echo "Mana regen per sec: ${mana_per_sec}"
  echo "Minimum wait per turn: ${min_wait_per_turn}"
  echo "Maximum wait per turn: ${max_wait_per_turn}"
  echo "Min mana potions per turn: ${min_mana_potions_per_turn}"
  echo "Max mana potions per turn: ${max_mana_potions_per_turn}"

}

function main {
  parse_args "$@"
  manasit
}

main "$@"

