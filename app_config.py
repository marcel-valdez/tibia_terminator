""""These values are obtained by running scanmem on the tibia process."""
MEM_CONFIG = {
    # PID of Tibia process
    'default_pid': 15922,
    '14591': {
        'mana_memory_address': '4350480',  # [I32 I16 ]
        'speed_memory_address': 'b722ec0',  # [I16 ]
        'soul_points_memory_address': '3718608',
        # The HP memory address can be reliably calculated based on the
        # mana memory address.
        # Not required, since it can be calculated.
        'hp_memory_address': None,  # [I32 I16 ]
        # from the addresses that match max to min values of magic shield, the
        # one that keeps track of current shield points is the one in the middle
        # that has another address matching +2 positions ahead of it.
        'magic_shield_memory_address': None  # [I16 ]
    },
    '21921': {
        'mana_memory_address': '44b5670',  # [I32 I16 ]
        'speed_memory_address': '79d9410',  # [I16 ]
        'soul_points_memory_address': '4814588',
        # The HP memory address can be reliably calculated based on the
        # mana memory address.
        # Not required, since it can be calculated.
        'hp_memory_address': None,  # [I32 I16 ]
        'magic_shield_memory_address': None
    }
}
