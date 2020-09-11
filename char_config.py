#!/usr/bin/env python2.7


# To get the min average heal of your character use:
# http://www.tibia-stats.com/index.php?akcja=spellDmgCalc


DEMNOK = {
    'total_hp': 725,
    'total_mana': 3330,
    # if speed is below base, then this will be recognized as paralysis
    # and we will increase priority of haste.
    'base_speed': 225,
    # will use utani hur whenever speed is below this
    'hasted_speed': 275,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 100,
    'downtime_heal_at_missing': 50,
    # whenever mana levels drop by 'mana_at_missing_hi' it will use mana
    # potions until there is 'mana_at_missing_lo' missing mana
    'mana_at_missing_hi': 1500,
    'mana_at_missing_lo': 1000,
    # critical mana at which we have to use a mana potion, even if missing hp
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 1000,
    # Slowly drink mana potions until this much is missing and only do it when
    # hp is at < 'heal_at_missing' and the char is hasted.
    'downtime_mana_missing': 500,
    # average heal of exura
    'exura_heal': 137,
    # average heal of exura gran
    'exura_gran_heal': 342,
    # average heal of exura sio
    'exura_sio_heal': 790
}

ULTIMATE = {
    'total_hp': 435,
    'total_mana': 1620,
    'base_speed': 160,
    # will use utani hur whenever speed is below this
    'hasted_speed': 205,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 65,
    'downtime_heal_at_missing': 35,
    # whenever mana levels drop by 'mana_at_missing_hi' it will use mana
    # potions until there is 'mana_at_missing_lo' missing mana
    'mana_at_missing_hi': 720,
    'mana_at_missing_lo': 400,
    # critical mana at which we have to use a mana potion, no matter what
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 550,
    # Slowly drink mana potions until this much is missing and only do it when
    # hp is at < 'heal_at_missing' and the char is hasted.
    'downtime_mana_missing': 200,
    # average heal of exura
    'exura_heal': 100,
    # average heal of exura
    'exura_gran_heal': 255,
    # average heal of exura sio
    'exura_sio_heal': 595
}


TEZALOR = {
    'total_hp': 385,
    'total_mana': 1290,
    # this is used to determine if the char is paralized
    'base_speed': 147,
    # will use utani hur whenever speed is below this
    'hasted_speed': 190,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 55,
    'downtime_heal_at_missing': 30,
    # whenever mana levels drop by 'mana_at_missing_hi' it will drink mana
    # potions until there is 'mana_at_missing_lo' missing mana
    'mana_at_missing_hi': 650,
    'mana_at_missing_lo': 300,
    # critical mana at which we have to use a mana potion, no matter what
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 500,
    # Use a mana potion until this much is missing and only do it when we're
    # nearly full HP and hasted
    'downtime_mana_missing': 200,
    # average heal of exura
    'exura_heal': 60,
    # average heal of exura
    'exura_gran_heal': 160,
    # average heal of exura sio
    'exura_sio_heal': 373
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

CHAR_CONFIG = DEMNOK
