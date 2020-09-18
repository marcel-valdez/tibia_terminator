# This value is obtained by running scanmem on the tibia process
MEM_CONFIG = {
  # PID of Tibia process
  'pid': 3400,
  'mana_memory_address': '548c050',  # [I32 I16 ]
  'speed_memory_address':  'e955c80',  # [I16 ]
  'soul_points_memory_address': '452af58',
  # The HP memory address can be reliably calculated based on the
  # mana memory address.
  'hp_memory_address': None  # [I32 I16 ]
}
