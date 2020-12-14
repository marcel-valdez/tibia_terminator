TOTAL_HP = 1000
TOTAL_MANA = 1000
BASE_SPEED = 100
UTANI_HUR_SPEED = 200
UTANI_GRAN_HUR_SPEED = 300


DEFAULT = {
    'total_hp': TOTAL_HP,
    'total_mana': TOTAL_MANA,

    # SPEED CONFIG
    # if speed is below base, then this will be recognized as paralysis
    # and we will increase priority of haste.
    'base_speed': BASE_SPEED,
    # will use utani hur whenever speed is below this
    'hasted_speed': UTANI_HUR_SPEED,

    # MANA CONFIG
    # whenever mana levels drop to 'mana_hi' it will use mana
    # potions until 'mana_lo'
    'mana_hi': TOTAL_MANA - 2000,
    'mana_lo': TOTAL_MANA - 1500,
    # critical mana at which we have to use a mana potion, even if missing hp
    # this will make it so that drinking mana potion competes with healing
    'critical_mana': 1500,
    # will heal whenever there is this much hp missing (min exura heal)
    # Slowly drink mana potions until this much is missing and only do it when
    # hp is at < 'heal_at_missing' and the char is hasted.
    # Tip: Make it 2.5x mana potion regen
    'downtime_mana': TOTAL_MANA - 920,

    # HP CONFIG
    # will cast heal *promptly* (250 ms) whenever this much HP is missing.
    'heal_at_missing': TOTAL_HP * 0.1,
    # will cast heal *with a delay* (2.5 s) whenever this much HP is missing.
    'downtime_heal_at_missing': TOTAL_HP * 0.025,
    # The numbers below are used to determine which heal spell to use,
    # depending on how much HP is missing.
    # average heal of exura
    'exura_heal': 50,
    # average heal of exura gran
    'exura_gran_heal': 100,
    # average heal of exura sio
    'exura_sio_heal': 300,
    # it will press the equip amulet key whenever the amulet slot is empty
    'should_equip_amulet': False,
    # it will press the equip ring key whenever the ring slot is *empty*
    'should_equip_ring': False,
    # it will press the eat food key every 60 seconds
    'should_eat_food': True,
    # valid types: None, 'emergency', 'permanent'
    'magic_shield_type': 'emergency',
    # it will refresh magic shield if it is below 1000 points
    'magic_shield_treshold': 1000
}
