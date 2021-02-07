#!/usr/bin/env python2.7

import char_configs.demnok_char_config as demnok
import char_configs.ultimate_char_config as ultimate
import char_configs.tezalor_char_config as tezalor
import char_configs.saekade_char_config as saekade
import char_configs.imfereal_char_config as imfereal
import char_configs.dio_sempai_config as dio_sempai

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
    'loot': 'v'
}

# Whenever you want to switch characters, you have to specify
# a different value in this file.
# TODO: Read the char's name and use that to load the correct
# character configuration.
CHAR_CONFIGS = [
    {
        "name": "tezalor.tezalor_th_softboots_roh()",
        "config": tezalor.tezalor_th_softboots_roh()
    },
    {
        "name": "tezalor.tezalor_th_defensive()",
        "config": tezalor.tezalor_th_defensive()
    },
    {
        "name": "tezalor.UTAMO_TEAM",
        "config": tezalor.UTAMO_TEAM
    },
    {
        "name": "tezalor.ISSAVI_UTAMO",
        "config": tezalor.ISSAVI_UTAMO
    },
    {
        "name": "tezalor.UTAMO_SOLO_RUN",
        "config": tezalor.UTAMO_SOLO_RUN
    },
    {
        "name": "tezalor.MOBS_NO_UTAMO",
        "config": tezalor.MOBS_NO_UTAMO,
    },
    {
        "name": "tezalor.HARDCORE_MOBS_NO_UTAMO",
        "config": tezalor.HARDCORE_MOBS_NO_UTAMO
    },
    {
        "name": "demnok.ISSAVI_UTAMO",
        "config": demnok.ISSAVI_UTAMO
    },
    {
        "name": "demnok.ISSAVI_NO_UTAMO",
        "config": demnok.ISSAVI_NO_UTAMO
    },
    {
        "name": "demnok.SOLO_HUNT",
        "config": demnok.SOLO_HUNT
    },
    {
        "name": "imfereal.DEFAULT",
        "config": imfereal.DEFAULT
    },
    {
        "name": "saekade.MOBS_NO_UTAMO",
        "config": saekade.MOBS_NO_UTAMO
    },
    {
        "name": "saekade.ISSAVI",
        "config": saekade.ISSAVI
    },
    {
        "name": "ultimate.TEAMHUNT",
        "config": ultimate.TEAMHUNT
    },
    {
        "name": "dio_sempai.SOLO_HUNT_MOBS",
        "config": dio_sempai.SOLO_HUNT_MOBS
    },
    {
        "name": "dio_sempai.ISSAVI",
        "config": dio_sempai.ISSAVI
    }
]