""""These values are obtained by running scanmem on the tibia process."""
MEM_CONFIG = {
    # PID of Tibia process
    'default_pid': 12345,
    # Default tibia process PID
    '12345': {
        'mana_memory_address': '4350480',  # [I32 I16 ]
        'speed_memory_address': 'a6c1a10',  # [I16 ]
        'soul_points_memory_address': '3718608',
        # The HP memory address can be reliably calculated based on the
        # mana memory address.
        # Not required, since it can be calculated.
        'hp_memory_address': None  # [I32 I16 ]
    },
    # Secondary tibia process PID
    '67890': {
        'mana_memory_address': '5d547d0',  # [I32 I16 ]
        'speed_memory_address': 'b75c0b0',  # [I16 ]
        'soul_points_memory_address': '4d62e08',
        # The HP memory address can be reliably calculated based on the
        # mana memory address.
        # Not required, since it can be calculated.
        'hp_memory_address': None  # [I32 I16 ]
    }
}
