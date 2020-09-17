#!/usr/bin/env python2.7


# To get the min average heal of your character use:
# http://www.tibia-stats.com/index.php?akcja=spellDmgCalc


DEMNOK = {
    'total_hp': 895,
    'total_mana': 4350,
    # if speed is below base, then this will be recognized as paralysis
    # and we will increase priority of haste.
    'base_speed': 284,
    # will use utani hur whenever speed is below this
    'hasted_speed': 437,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 100,
    'downtime_heal_at_missing': 50,
    # whenever mana levels drop by 'mana_at_missing_hi' it will use mana
    # potions until there is 'mana_at_missing_lo' missing mana
    'mana_at_missing_hi': 1600,
    'mana_at_missing_lo': 1100,
    # critical mana at which we have to use a mana potion, even if missing hp
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 1500,
    # Slowly drink mana potions until this much is missing and only do it when
    # hp is at < 'heal_at_missing' and the char is hasted.
    # Tip: Make it 2.5x mana potion regen
    'downtime_mana_missing': 700,
    # average heal of exura
    'exura_heal': 178,
    # average heal of exura gran
    'exura_gran_heal': 433,
    # average heal of exura sio
    'exura_sio_heal': 997
}

ULTIMATE = {
    'total_hp': 465,
    'total_mana': 1770,
    'base_speed': 193,
    # will use utani hur whenever speed is below this
    'hasted_speed': 232,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 65,
    'downtime_heal_at_missing': 35,
    # whenever mana levels drop by 'mana_at_missing_hi' it will use mana
    # potions until there is 'mana_at_missing_lo' missing mana
    'mana_at_missing_hi': 770,
    'mana_at_missing_lo': 400,
    # critical mana at which we have to use a mana potion, no matter what
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 500,
    # Slowly drink mana potions until this much is missing and only do it when
    # hp is at < 'heal_at_missing' and the char is hasted.
    # Tip: Make it 2.5x mana potion regen
    'downtime_mana_missing': 375,
    # average heal of exura
    'exura_heal': 110,
    # average heal of exura
    'exura_gran_heal': 279,
    # average heal of exura sio
    'exura_sio_heal': 649
}


TEZALOR = {
    'total_hp': 585,
    'total_mana': 2490,
    # this is used to determine if the char is paralized
    'base_speed': 195,
    # will use utani hur whenever speed is below this
    'hasted_speed': 260,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 60,
    'downtime_heal_at_missing': 50,
    # whenever mana levels drop by 'mana_at_missing_hi' it will drink mana
    # potions until there is 'mana_at_missing_lo' missing mana
    'mana_at_missing_hi': 1070,
    'mana_at_missing_lo': 600,
    # critical mana at which we have to use a mana potion, no matter what
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 810,
    # Use a mana potion until this much is missing and only do it when we're
    # nearly full HP and hasted
    # Tip: Make it 2.5x mana potion regen
    'downtime_mana_missing': 500,
    # average heal of exura
    'exura_heal': 140,
    # average heal of exura
    'exura_gran_heal': 355,
    # average heal of exura sio
    'exura_sio_heal': 828
}

HOTKEYS_CONFIG = {
    'exura': 'b',
    # average heal of exura
    'exura_gran': 'g',
    # average heal of exura sio
    'exura_sio': 't',
    'mana_potion': 'Home',
    'utani_hur': '4'
}

# Whenever you want to switch characters, you have to specify
# a different value in this file.
# TODO: Use a command line parameter to specify the name of the
# character to use, rather than hardcoding it in this file.
CHAR_CONFIG = DEMNOK
