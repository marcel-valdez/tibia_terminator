SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$(dirname ${SCRIPTPATH})/tibia_terminator"
PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
MENU_READER_BIN="${ROOT_PATH}/reader/menu_reader.py"
XDOTOOL_LEFT_BTN=1
XDOTOOL_RIGHT_BTN=3
WAIT_TIME_SEC="0.3"

function is_interaction_owner {
  local owner_pid=$(cat /tmp/tibia_refill)
  [[ ${owner_pid} -eq $$ ]]
}

function free_interaction {
  if [[ -e /tmp/tibia_refill ]]; then
    local owner_pid=$(cat /tmp/tibia_refill)
    if [[ ${owner_pid} -eq $$ ]]; then
      rm /tmp/tibia_refill
    fi
  fi
}

function lock_interaction {
  if [[ -e /tmp/tibia_refill ]]; then
    local owner_pid=$(cat /tmp/tibia_refill)
    if [[ ${owner_pid} -ne $$ ]]; then
      echo "Another process is interacting with a Tibia Window" >&2
      return 1
    else
      return 0
    fi
  else
    echo $$ > /tmp/tibia_refill
    return 0
  fi
}

function browse_field() {
    local tibia_wid="$1"
    local x="$2"
    local y="$3"

    local delta_x=50
    local delta_y=85
    local click_x=$((x+delta_x))
    local click_y=$((y+delta_y))

        xdotool \
            windowfocus "${tibia_wid}" \
            sleep "${WAIT_TIME_SEC}" \
            mousemove --window "${tibia_wid}" "${x}" "${y}" \
            sleep "${WAIT_TIME_SEC}" \
            keydown --window "${tibia_wid}" "Control_L" \
            sleep "${WAIT_TIME_SEC}" \
            click ${XDOTOOL_RIGHT_BTN} \
            sleep "${WAIT_TIME_SEC}" \
            keyup --window "${tibia_wid}" "Control_L" \
            sleep "${WAIT_TIME_SEC}" \
            mousemove --window "${tibia_wid}" "${click_x}" "${click_y}" \
            sleep "${WAIT_TIME_SEC}" \
            click ${XDOTOOL_LEFT_BTN} \
            sleep "${WAIT_TIME_SEC}"
}


CLOSE_X=1909
CLOSE_Y=503
function close_menu {
  local tibia_wid="$1"
  xdotool windowfocus "${tibia_wid}" \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${CLOSE_X}" "${CLOSE_Y}" \
          sleep "${WAIT_TIME_SEC}" click ${XDOTOOL_LEFT_BTN}
}

function is_depot_box_open {
  local tibia_wid=$1
  PYTHONPATH="${PYTHONPATH}" python3.8 "${MENU_READER_BIN}" \
    "${tibia_wid}" --check_menu "depot_box_open"
}

function is_other_menu_open {
  local tibia_wid=$1
  ! PYTHONPATH="${PYTHONPATH}" python3.8 "${MENU_READER_BIN}" \
    "${tibia_wid}" --check_menu "empty"
}

BP_X=1840
BP_Y=268
STOW_X=1725
STOW_Y=455
function stow_bp {
  local tibia_wid="$1"
  xdotool windowfocus "${tibia_wid}" \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${BP_X}" "${BP_Y}" \
          sleep "${WAIT_TIME_SEC}" keydown ctrl \
          sleep "${WAIT_TIME_SEC}" click ${XDOTOOL_LEFT_BTN} \
          sleep "${WAIT_TIME_SEC}" keyup ctrl \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${STOW_X}" "${STOW_Y}" \
          sleep "${WAIT_TIME_SEC}" click ${XDOTOOL_LEFT_BTN}
}

STASH_X=1806
STASH_Y=530
function open_stash {
  local tibia_wid="$1"
  open_depot "${tibia_wid}"
  xdotool windowfocus "${tibia_wid}" \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${STASH_X}" "${STASH_Y}" \
          sleep "${WAIT_TIME_SEC}" click ${XDOTOOL_RIGHT_BTN}

}

DEPOT_X=944
DEPOT_Y=320
function open_depot {
  local tibia_wid="$1"
  xdotool windowfocus "${tibia_wid}" \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${DEPOT_X}" "${DEPOT_Y}" \
          sleep "${WAIT_TIME_SEC}" click ${XDOTOOL_RIGHT_BTN}
}

DEPOT_SEARCH_BTN_X=1880
DEPOT_SEARCH_BTN_Y=500
SEARCH_X=1843
SEARCH_Y=$((695+87))
SEARCH_CLEAR_X=1905
SEARCH_CLEAR_Y=$((695+87))
SEARCH_RESULT_X=1765
SEARCH_RESULT_Y=$((640+87))
SEARCH_RETRIEVE_X=1842
SEARCH_RETRIEVE_Y=$((578+87))
SEARCH_BACK_X=1884
SEARCH_BACK_Y=$((500+87))
SEARCH_RETRIEVE_PAGE_X=1828
SEARCH_RETRIEVE_PAGE_Y=$((720+87))
SEARCH_RETRIEVE_OK_X=1000
SEARCH_RETRIEVE_OK_Y=580
function fetch_from_locker {
  local tibia_wid="$1"
  local item_name="$2"
  local item_count="$3"
  # search for the item
  xdotool windowfocus "${tibia_wid}" \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${DEPOT_SEARCH_BTN_X}" "${DEPOT_SEARCH_BTN_Y}" \
          sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${SEARCH_BACK_X}" "${SEARCH_BACK_Y}" \
          sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${SEARCH_CLEAR_X}" "${SEARCH_CLEAR_Y}" \
          sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${SEARCH_X}" "${SEARCH_Y}" \
          sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
          sleep "${WAIT_TIME_SEC}" type --window "${tibia_wid}" --terminator @ "${item_name}" @ \
          sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" --sync "${SEARCH_RESULT_X}" "${SEARCH_RESULT_Y}" \
          sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
          sleep "$((WAIT_TIME_SEC / 2))" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN}

  # retrieve the item
  if [[ "${item_count}" = "page" ]]; then
    xdotool mousemove --window "${tibia_wid}" --sync "${SEARCH_RETRIEVE_PAGE_X}" "${SEARCH_RETRIEVE_PAGE_Y}" \
            sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
            sleep "${WAIT_TIME_SEC}" key --window "${tibia_wid}" Escape
  else
    xdotool mousemove --window "${tibia_wid}" --sync "${SEARCH_RETRIEVE_X}" "${SEARCH_RETRIEVE_Y}" \
            sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
            sleep "${WAIT_TIME_SEC}" type --window "${tibia_wid}" --terminator @ "${item_count}" @ \
            sleep "${WAIT_TIME_SEC}" mousemove --window "${tibia_wid}" "${SEARCH_RETRIEVE_OK_X}" "${SEARCH_RETRIEVE_OK_Y}" \
            sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
            sleep "${WAIT_TIME_SEC}" key --window "${tibia_wid}" Escape
  fi

  # set search menu back to original state and exit the search subwindow focus
  xdotool mousemove --window "${tibia_wid}" --sync "${SEARCH_BACK_X}" "${SEARCH_BACK_Y}" \
          sleep "${WAIT_TIME_SEC}" click --window "${tibia_wid}" ${XDOTOOL_LEFT_BTN} \
          sleep "${WAIT_TIME_SEC}" key --window "${tibia_wid}" Escape
}
