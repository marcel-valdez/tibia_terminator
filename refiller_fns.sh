
BP_X=1840
BP_Y=268
STOW_X=1725
STOW_Y=455
function stow_bp {
  local tibia_wid="$1"
  xdotool windowfocus "${tibia_wid}" \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${BP_X}" "${BP_Y}" \
          sleep 0.3 keydown ctrl \
          sleep 0.3 click 1 \
          sleep 0.3 keyup ctrl \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${STOW_X}" "${STOW_Y}" \
          sleep 0.3 click 1
}

STASH_X=1806
STASH_Y=530
function open_stash {
  local tibia_wid="$1"
  open_depot "${tibia_wid}"
  xdotool windowfocus "${tibia_wid}" \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${STASH_X}" "${STASH_Y}" \
          sleep 0.3 click 3

}

DEPOT_X=944
DEPOT_Y=320
function open_depot {
  local tibia_wid="$1"
  xdotool windowfocus "${tibia_wid}" \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${DEPOT_X}" "${DEPOT_Y}" \
          sleep 0.3 click 3
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
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${DEPOT_SEARCH_BTN_X}" "${DEPOT_SEARCH_BTN_Y}" \
          sleep 0.3 click --window "${tibia_wid}" 1 \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${SEARCH_BACK_X}" "${SEARCH_BACK_Y}" \
          sleep 0.3 click --window "${tibia_wid}" 1 \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${SEARCH_CLEAR_X}" "${SEARCH_CLEAR_Y}" \
          sleep 0.3 click --window "${tibia_wid}" 1 \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${SEARCH_X}" "${SEARCH_Y}" \
          sleep 0.3 click --window "${tibia_wid}" 1 \
          sleep 0.3 type --window "${tibia_wid}" --terminator @ "${item_name}" @ \
          sleep 0.3 mousemove --window "${tibia_wid}" --sync "${SEARCH_RESULT_X}" "${SEARCH_RESULT_Y}" \
          sleep 0.3 click --window "${tibia_wid}" 1 sleep 0.1 click --window "${tibia_wid}" 1

  # retrieve the item
  if [[ "${item_count}" = "page" ]]; then
    xdotool mousemove --window "${tibia_wid}" --sync "${SEARCH_RETRIEVE_PAGE_X}" "${SEARCH_RETRIEVE_PAGE_Y}" \
            sleep 0.3 click --window "${tibia_wid}" 1 \
            sleep 0.3 key --window "${tibia_wid}" Escape
  else
    xdotool mousemove --window "${tibia_wid}" --sync "${SEARCH_RETRIEVE_X}" "${SEARCH_RETRIEVE_Y}" \
            sleep 0.3 click --window "${tibia_wid}" 1 \
            sleep 0.3 type --window "${tibia_wid}" --terminator @ "${item_count}" @ \
            sleep 0.3 mousemove --window "${tibia_wid}" "${SEARCH_RETRIEVE_OK_X}" "${SEARCH_RETRIEVE_OK_Y}" \
            sleep 0.3 click --window "${tibia_wid}" 1 \
            sleep 0.3 key --window "${tibia_wid}" Escape
  fi

  # set search menu back to original state and exit the search subwindow focus
  xdotool mousemove --window "${tibia_wid}" --sync "${SEARCH_BACK_X}" "${SEARCH_BACK_Y}" \
          sleep 0.3 click --window "${tibia_wid}" 1 \
          sleep 0.3 key --window "${tibia_wid}" Escape
}