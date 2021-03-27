#!/usr/bin/env python3.8

import argparse
import keyboard
import pyautogui
import commentjson
import time


from typing import Dict, Any, Callable, List
from tibia_terminator.schemas.directional_macro_config_schema import (
    DirectionalMacroConfigSchema, DirectionalMacroConfig)
from tibia_terminator.interface.macro.macro import (Macro, parse_hotkey,
                                                    to_issuable)

parser = argparse.ArgumentParser(description='Test a directional macro.')
parser.add_argument("json_config_file",
                    type=str,
                    help=("Path to JSON config for a directional macro, "
                          "see tibia_terminator/tests/interface/macro/"
                          "test_directional_macro_config.json"))


class PairMacro(Macro):
    to_key_params: List[str] = None
    rotation_fn: Callable[[], str]

    def __init__(self, from_key: str, to_key: str,
                 rotation_fn: Callable[[], str], throttle_fn: Callable[[],
                                                                       bool]):
        # We use keydown in order to trigger the spell almost as one action,
        # but within Tibia's key-processing limit.
        super().__init__(from_key, key_event_type="down")
        self.rotation_fn = rotation_fn
        self.throttle_fn = throttle_fn
        if to_key is not None:
            self.to_key_params = to_issuable(parse_hotkey(to_key)).to_list()
        else:
            self.to_key_params = None

    def _action(self):
        # Note that this may not work so well when the directional hotkeys
        # keys do not match the actual Tibia directional hotkeys.
        if self.throttle_fn():
            rotation_key_params = self.rotation_fn()
            if self.to_key_params is not None:
                time.sleep(0.02)
                pyautogui.hotkey(*self.to_key_params)
            # TODO: sometimes (10%~) it triggers before the char rotates in
            #       Concorda when doing heavy movement.
            time.sleep(0.045)
            pyautogui.hotkey(*rotation_key_params)


DIRECTIONAL_MACRO_THROTTLE_SEC = 0.0937  # prev: 0.0625


class DirectionalMacro():
    __macros: List[PairMacro]
    __rotation_counter: int = 0
    __last_timestamp_sec: float = 0
    __rotation_params: List[List[str]]
    __rotation_threshold_sec: int = 60

    def __init__(self, config: Dict[str, Any]):
        _config = DirectionalMacroConfigSchema().load(config)
        self.__macros = []
        self.__rotation_params = self.gen_rotation_params(_config)
        self.__macros = self.gen_pair_macros(_config)
        self.__rotation_threshold_sec = _config.rotation_threshold_secs
        self.__last_timestamp_sec = 0

    def gen_pair_macros(self,
                        config: DirectionalMacroConfig) -> List[PairMacro]:
        macros = []
        for from_key, to_key in config.direction_pairs:
            macros.append(
                PairMacro(from_key, to_key, self.__gen_rotation,
                          self.__throttle))
        return macros

    def gen_rotation_params(self,
                            config: DirectionalMacroConfig) -> List[List[str]]:
        rotation_params = []
        for hotkey in config.spell_key_rotation:
            rotation_params.append(to_issuable(parse_hotkey(hotkey)).to_list())
        return rotation_params

    def __gen_rotation(self) -> List[str]:
        if self.__rotation_counter == len(self.__rotation_params) or (
                time.time() - self.__last_timestamp_sec >
                self.__rotation_threshold_sec):
            self.__rotation_counter = 0
        next_key_params = self.__rotation_params[self.__rotation_counter]
        self.__rotation_counter += 1
        return next_key_params

    def __throttle(self) -> bool:
        now = time.time()
        if (now - self.__last_timestamp_sec) > DIRECTIONAL_MACRO_THROTTLE_SEC:
            self.__last_timestamp_sec = now
            return True
        else:
            return False

    def hook_hotkey(self, *args, **kwargs):
        for macro in self.__macros:
            macro.hook_hotkey(*args, **kwargs)

    def unhook_hotkey(self, *args, **kwargs):
        for macro in self.__macros:
            macro.unhook_hotkey(*args, **kwargs)


def main(args):
    macros = []
    json_config = None
    with open(args.json_config_file, 'r') as f:
        json_config = commentjson.load(f)

    if not isinstance(json_config, list):
        json_config = [json_config]

    for directional_config in json_config:
        macro = DirectionalMacro(directional_config)
        print("Mapping pairs:")
        for from_key, to_key in directional_config["direction_pairs"]:
            print(f"  {from_key} => {to_key}")
        print("Spell rotation:")
        for rotation in directional_config["spell_key_rotation"]:
            print(f"  {rotation}")
        macro.hook_hotkey()
        macros.append(macro)

    try:
        print('Press [Enter] to exit.')
        keyboard.wait('enter')
    finally:
        for macro in macros:
            macro.unhook_hotkey()


if __name__ == '__main__':
    main(parser.parse_args())
