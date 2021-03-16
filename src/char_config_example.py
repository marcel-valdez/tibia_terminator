#!/usr/bin/env python2.7

import char_configs.example_char_config as example
# To get the min average heal of your character use:
# http://www.tibia-stats.com/index.php?akcja=spellDmgCalc


HOTKEYS_CONFIG = {
    'exura': 'b',
    'exura_gran': 'g',
    'exura_sio': 't',
    'mana_potion': 'Home',
    'utani_hur': '4',
    'equip_ring': 'F6',
    'equip_amulet': 'F7',
    'eat_food': 'F8',
    'magic_shield': 'F9'
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