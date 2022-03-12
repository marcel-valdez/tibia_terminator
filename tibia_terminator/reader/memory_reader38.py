#!/usr/bin/env python3.8

from typing import Union

import ctypes


CTypesBuffer = Union[
    ctypes._SimpleCData, ctypes.Array, ctypes.Structure, ctypes.Union
]


class MemoryReader38:
    def __init__(self, proc_id, print_async=lambda x: None):
        self.proc_id = proc_id
        self.print_async = print_async
        self.mem_file = None

    def open(self):
        self.mem_file = open("/proc/{}/mem".format(self.proc_id), "rb")

    def close(self):
        self.mem_file.close()

    def read_address(self, address, size):
        if self.mem_file is None:
            raise Exception("Please open_mem_file before reading an address.")
        # seek to region start
        self.mem_file.seek(address)
        data = self.mem_file.read(size)
        chunks = data.hex()
        # Split each byte and then reverse its order (but dont reverse the
        # actual byte)
        shifted_bytes = "".join(map(str.__add__, chunks[-2::-2], chunks[-1::-2]))
        return int(shifted_bytes, 16)

    def read_address_ctype(
        self, address: int, ctype_buffer: CTypesBuffer
    ) -> int:
        if self.mem_file is None:
            raise Exception("Please open_mem_file before reading an address.")
        self.mem_file.seek(address)
        self.mem_file.readinto(ctype_buffer)
        return int(ctype_buffer.value)
