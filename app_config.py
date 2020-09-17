# This value is obtained by running scanmem on the tibia process
MEM_CONFIG = {
  'mana_memory_address': '548c050',  # [I32 I16 ]
  'speed_memory_address':  '92acd90',  # [I16 ]
  # The HP memory address can be reliably calculated based on the
  # mana memory address.
  'hp_memory_address': None  # [I32 I16 ]
}
