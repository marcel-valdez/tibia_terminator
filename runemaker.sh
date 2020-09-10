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

# Playable area set at Y: 696 with 2 cols on left and 2 cols on right
# To get the realtime mouse location use:
#   watch -t -n 0.0001 xdotool getmouselocation
function click_mana_potion {
  local SCREEN=0
  local tibia_window=$1
  local minX=1695
  local maxX=1719
  # with full depot box
  local minY=280
  local maxY=305
  # with 1500 manas
  #local minY=169
  #local maxY=195
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  echo "Pausing ${wait_time}" &
  sleep ${wait_time}

  echo "Clicking mana potion (${X},${Y})" &
  xdotool mousemove --screen 0 ${X} ${Y}
  xdotool click --window ${tibia_window} --delay $(random 125 250) 1
}

function click_char {
  local tibia_window=$1
  local X=958
  local Y=372
  local SCREEN=0

  local minY=364
  local maxY=399
  local minX=939
  local maxX=980
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  echo "Pausing ${wait_time}" &
  sleep ${wait_time}

  echo "Clicking char (${X},${Y})" &
  xdotool mousemove --screen 0 --window ${tibia_window} ${X} ${Y}
  xdotool click --window ${tibia_window} --delay $(random 125 250) 1
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
    local wait_time="0.$(random 110 350)s"
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


potions_seq_counter=0
function get_potion_count {
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

function drink_mana_potion {
  local tibia_window=$1
  if [[ ${use_mouse_for_mana_potion} ]]; then
    click_mana_potion ${tibia_window}
    click_char ${tibia_window}
  else
    send_keystroke "${window}" 'm' 1 1
  fi
}

function drink_mana_potions {
  local window=$1
  local potion_count=$(get_potion_count)
  potions_seq_counter=$((potions_seq_counter + 1))

  echo '-----------------------'
  echo "Drinking ${potion_count} mana potions"
  echo '-----------------------'
  for i in $(seq 1 ${potion_count}); do
    drink_mana_potion ${tibia_window}
    local wait_time="0.$(random 310 560)s"
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

function hold_life_ring {
  local tibia_window=$1
  local minX=1760
  local maxX=1783
  local minY=487
  local maxY=510

  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  sleep ${wait_time}
  xdotool mousemove --sync --screen 0 ${X} ${Y}
  wait_time="0.$(random 250 390)s"
  sleep ${wait_time}
  #xdotool keydown --window "${tibia_window}" Pointer_Button1
  xdotool mousedown --window "${tibia_window}" 1
}

function drop_life_ring {
  local tibia_window=$1
  local minX=1755
  local maxX=1781
  local minY=323
  local maxY=349

  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})


  local wait_time="0.$(random 250 390)s"
  sleep "${wait_time}"
  for i in $(seq 1 160); do
    xdotool mousemove_relative --sync 0 -1
  done
  # xdotool mousemove --screen 0 ${X} ${Y}
  wait_time="0.$(random 250 390)s"
  sleep "${wait_time}"
  xdotool keyup --window "${tibia_window}" Pointer_Button1
  # xdotool mouseup --window "${tibia_window}" 1
}


function equip_life_ring {
  local tibia_window="$1"
  if [[ ! -z "${use_mouse_for_life_ring}" ]]; then
    #hold_life_ring "${tibia_window}"
    #drop_life_ring "${tibia_window}"
    drag_drop_ring ${tibia_window}
  else
    # equip secondary ring
    send_keystroke "${tibia_window}}" 'u' 1
    # small wait to make sure primary gets equipped
    wait_time="0.$(random 250 390)s"
    sleep "${wait_time}"
    # equip primary ring
    send_keystroke "${tibia_window}}" 'n' 1
  fi
}

function equip_soft_boots {
  local tibia_window="$1"
  # equip soft boots
  send_keystroke "${tibia_window}}" 'j' 1
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
  echo 'Equipping life ring and soft boots'
  echo '-------------------'
  equip_life_ring "${window}"
  equip_soft_boots "${window}"
  drink_mana_potions "${window}"
}

function wait_for_mana {
  local window=$1
  local total_sit_seconds=$( random ${min_wait_per_turn} ${max_wait_per_turn}  )
  # only if using mana potions
  echo
  echo '------------------------'
  echo "| Waiting for mana ${total_sit_seconds}s |"
  echo '------------------------'
  echo
  local third_sit_seconds=$((total_sit_seconds / 3))
  wait_ui "${third_sit_seconds}"
  # cast rune spell half way through wait to make sure we don't get full mana
  # and waste
  cast_rune_spell "${window}"
  wait_ui "${third_sit_seconds}"
  cast_rune_spell "${window}"
  wait_ui "${third_sit_seconds}"
}

function manasit {
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

    # wait random time
    sleep "0.$(random 2 5)$(random 1 5)s"

    # make the rune
    make_rune "${tibia_window}"

    # return to prev window
    sleep "$(random 1 2).$(random 1 9)$(random 1 9)s"
    if [[ ${refocus_tibia_to_make_rune} ]]; then
      xdotool mousemove --screen ${curr_screen}\
              ${curr_x} ${curr_y}
      focus_window ${curr_window}
    fi

    # sit until next rune spell with randomization
    wait_for_mana ${tibia_window}
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
mana_potions_seq=()
use_mouse_for_mana_potion=
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
        refocus_tibia_to_make_rune=1
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
      --mana-potions-seq)
        # split space or comma separated sequence of elements as an array
        IFS=', ' read -r -a mana_potions_seq <<< "$2"
        shift
        ;;
      --use-mouse-for-mana-potion)
        use_mouse_for_mana_potion=1
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

  local mana_potions_seq_len=${#mana_potions_seq[@]}
  if [[ ${mana_potions_seq_len} -gt 0 ]]; then
    debug "Mana potion sequence length: ${mana_potions_seq_len}"

    max_mana_potions_per_turn=0
    min_mana_potions_per_turn=0
  else
    if [[ -z "${max_mana_potions_per_turn}" ]]; then
      max_mana_potions_per_turn=$(mana_potion_count)
    fi

    if [[ -z "${min_mana_potions_per_turn}" ]]; then
      min_mana_potions_per_turn=0
    fi
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
  if [[ ${mana_potions_seq_len} -gt 0 ]]; then
    echo "Mana potion sequence: ${mana_potions_seq[@]}"
  else
    echo "Min mana potions per turn: ${min_mana_potions_per_turn}"
    echo "Max mana potions per turn: ${max_mana_potions_per_turn}"
  fi

  if [[ ! -z ${use_mouse_for_mana_potion} ]]; then
    echo "Using mouse for drinking mana potions"
  fi

}

function main {
  parse_args "$@"
  manasit
}

main "$@"

