#!/usr/bin/env bash
# requirements: xdotool

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
TERMINATOR_PATH="${ROOT_PATH}"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
CHAR_READER_BIN="${ROOT_PATH}/reader/char_reader38.py"
RECONNECTOR_BIN="${ROOT_PATH}/tibia_reconnector.py"
PYTHON_BIN="$(type -p python3.8)"
APP_CONFIG_PATH="${TERMINATOR_PATH}/app_config.json"

function python_bin {
    PYTHONPATH=${PYTHONPATH} "${PYTHON_BIN}" "$@"
}

function sudo_python_bin {
    sudo PYTHONPATH=${PYTHONPATH} "${PYTHON_BIN}" "$@"
}

PRIMARY_SPELL_KEY='g'
SECONDARY_SPELL_KEY='b'
DRINK_POTION_KEY='k'
SCREEN_WIDTH_PIXELS=1920
MANA_POTION_CENTER_X=1707
MANA_POTION_CENTER_Y=292
CHAR_CENTER_X=958
CHAR_CENTER_Y=372
SCREEN_NO=0
LEFT_BTN="1"
RIGHT_BTN="3"

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
    if [[ ${mana} -ge ${MAX_MANA} ]]; then
        return 1
    fi
    # call the eat command a random number between 0 and 3
    # we don't want to always issue the eat command
    echo '-----------'
    echo 'Eating food'
    echo '-----------'
    send_keystroke 'h' 0 3
}

function fetch_char_stats() {
    eval "$(sudo_python_bin ${CHAR_READER_BIN} --pid ${tibia_pid} --app_config_path ${APP_CONFIG_PATH})"
}

function get_mana() {
    fetch_char_stats
    echo "${MANA}"
}

function cast_spell() {
    send_spell_keystroke "${PRIMARY_SPELL_KEY}" 1 1
}

function cast_secondary_spell() {
    send_spell_keystroke "${SECONDARY_SPELL_KEY}" 1 1
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

function owns_interaction_lock() {
    local my_pid="$$"

    if [[ -e "/tmp/mana_waster_pid.lock" ]]; then
        local locking_pid="$(cat "/tmp/mana_waster_pid.lock")"
        if [[ "${locking_pid}" ]] && kill -0 "${locking_pid}" &>/dev/null; then
           # other owner for lock and it is running
           if [[ "${locking_pid}" -ne "${my_pid}" ]]; then
               return 1
           fi
        fi
    fi


    return 0
}

function acquire_interaction_lock() {
    echo "$$" > "/tmp/mana_waster_pid.lock"
}

function release_interaction_lock() {
    echo "" > "/tmp/mana_waster_pid.lock"
}

function click_mana_potion() {
    local minX=$((MANA_POTION_CENTER_X-12))
    local maxX=$((MANA_POTION_CENTER_X+12))
    # with full depot box
    local minY=$((MANA_POTION_CENTER_Y-12))
    local maxY=$((MANA_POTION_CENTER_Y+12))
    # with 1500 manas
    #local minY=169
    #local maxY=195
    local X=$(random ${minX} ${maxX})
    local Y=$(random ${minY} ${maxY})

    local wait_time="0.$(random 250 390)s"
    echo "Pausing ${wait_time}" &
    sleep ${wait_time}

    echo "Clicking mana potion (${X},${Y})" &
    xdotool mousemove --screen "${SCREEN_NO}" --window "${tibia_window}" "${X}" "${Y}"
    xdotool click --window "${tibia_window}" --delay $(random 125 250) "${RIGHT_BTN}"
}

function click_char() {
  local minY=$((CHAR_CENTER_Y-12))
  local maxY=$((CHAR_CENTER_Y+12))
  local minX=$((CHAR_CENTER_X-12))
  local maxX=$((CHAR_CENTER_X+12))
  local X=$(random ${minX} ${maxX})
  local Y=$(random ${minY} ${maxY})

  local wait_time="0.$(random 250 390)s"
  echo "Pausing ${wait_time}" &
  sleep ${wait_time}

  echo "Clicking char (${X},${Y})" &
  xdotool mousemove --screen "${SCREEN_NO}" --window "${tibia_window}" "${X}" "${Y}"
  xdotool click --window "${tibia_window}" --delay "$(random 125 250)" "${LEFT_BTN}"
}

function drink_mana_potion() {
    fetch_char_stats
    if [[ ${MANA} -ge ${MAX_MANA} ]]; then
        return 1
    fi


    if [[ ${click_for_potion} ]]; then
        click_mana_potion
        click_char
    else
        send_keystroke "${DRINK_POTION_KEY}" 1 1
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

        fetch_char_stats
        local mana=$(get_mana)
        local mana_potion_threshold=$((MAX_MANA-125))
        echo "MAX_MANA:${MAX_MANA}"
        echo "mana_potion_threshold=${mana_potion_threshold}"
        if [[ ${mana} -ge ${mana_per_spell} ]]; then
            cast_spell
        elif [[ ${mana} -le ${mana_potion_threshold} ]]; then
            echo 'drink mana potion'
            drink_mana_potion ${tibia_window}
        elif [[ ${mana} -ge ${mana_per_secondary_spell} ]]; then
            cast_secondary_spell
        fi

        sleep "0.$(random 125 250)s"
        eat_food
    done
}

tibia_pid=
credentials_profile=
mana_per_spell=
click_for_potion=
screen="left"
function parse_args() {
    while [[ $# -gt 0 ]]; do
        arg=$1
        case $arg in
            --mana-per-spell|-m)
                mana_per_spell=$2
                shift
                ;;
            --mana-per-secondary-spell|-s)
                mana_per_secondary_spell=$2
                shift
                ;;
            --tibia-pid|-p)
                tibia_pid=$2
                shift
                ;;
            --credentials-profile|-c)
                credentials_profile=$2
                shift
                ;;
            --click-for-potion|-l)
                click_for_potion=1
                shift
                ;;
            *)
                break
                ;;
        esac
        shift
    done

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
}

function main() {
    trap release_interaction_lock SIGINT SIGTERM ERR EXIT
    parse_args "$@"
    waste_mana
}

main "$@"
