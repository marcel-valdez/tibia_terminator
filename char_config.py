#!/usr/bin/env python3.8

import char_configs.example_char_config as example

# To get the min average heal of your character use:
# http://www.tibia-stats.com/index.php?akcja=spellDmgCalc


HOTKEYS_CONFIG = {
    'exura': 'b',
    'exura_gran': 'g',
    'exura_sio': 't',
    'mana_potion': 'Home',
    'utani_hur': '6',
    'equip_ring': 'F6',
    'equip_amulet': 'F7',
    'eat_food': 'F8',
    'magic_shield': 'F9',
    'cancel_magic_shield': 'F10',
    'loot': 'v',
    'toggle_emergency_amulet': 'F1',
    'toggle_emergency_ring': 'F2',
}

# Whenever you want to switch characters, you have to specify
# a different value in this file.
# TODO: Read the char's name and use that to load the correct
# character configuration.
CHAR_CONFIGS = [
    {
        "name": "example.DEFAULT",
        "config": example.DEFAULT
    }
]
