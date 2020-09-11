#!/usr/bin/env python2.7

import binascii


class MemoryReader:
    def __init__(self, proc_id, print_async=lambda x: None):
        self.proc_id = proc_id
        self.print_async = print_async

    def find_target_range(self, known_value_addr):
        target = int(known_value_addr, 16)
        maps_file = open("/proc/{}/maps".format(self.proc_id), 'r')

        # for each mapped region
        for line in maps_file.readlines():
            # Split the line into spaces
            splitter = line.split(" ")
            # region low of chunk
            region_low = int(splitter[0].split("-")[0], 16)
            # region high of chunk
            region_high = int(splitter[0].split("-")[1], 16)

            if target > region_low:
                if target < region_high:
                    return {
                        "region_low": region_low,
                        "region_high": region_high
                    }

    def find_value_address(
            self,
            heap_regions,
            offset_amount,
            hardcoded_value,
            hardcoded_value_size
    ):
        self.print_async("Scanning memory, this could take a few seconds....")
        region_low = heap_regions["region_low"]
        region_high = heap_regions["region_high"]
        # TODO: Make it possible to read a memory dump file instead of /proc/xxx/mem
        with open("/proc/{}/mem".format(self.proc_id), 'rb') as mem_file:
            # Goto the start address of our heap
            mem_file.seek(region_low)
            # Just a buffer so we know what address we are at currently
            search_signature_addr = region_low
            upper_hardcoded_value = hardcoded_value.upper()
            # Stop searching when we exit end of heap
            self.print_async("Starting search at: " +
                             hex(search_signature_addr))
            while search_signature_addr < region_high:
                search_signature_addr = search_signature_addr \
                    + hardcoded_value_size
                word = ""
                count = 0
                # Read every <hardcoded_value_size> bytes and put into a string
                while count < hardcoded_value_size:
                    count += 1
                    byte = binascii.hexlify(mem_file.read(1))
                    word = word + str(byte)

                if word.upper() == upper_hardcoded_value:
                    signature_addr_start = search_signature_addr \
                        - hardcoded_value_size
                    self.print_async(
                        "Signature found at - " + str(signature_addr_start)
                        + " (" + hex(signature_addr_start) + ")"
                    )
                    return signature_addr_start + offset_amount

    def read_address(self, address, size):
        mem_file = open("/proc/{}/mem".format(self.proc_id), 'rb')
        # seek to region start
        mem_file.seek(address)
        count = 0
        chunks = ""
        while count < size:
            count = count + 1
            chunk = binascii.hexlify(mem_file.read(1))
            chunks = chunks + str(chunk)
        # Split each byte and then reverse its order (but dont reverse the
        # actual byte)
        shifted_bytes = ("".join(map(
            str.__add__,
            chunks[-2::-2],
            chunks[-1::-2])))

        return (int(shifted_bytes, 16))

    def get_range(self, address):
        range = self.find_target_range(address)
        if range is None:
            raise Exception(
                "Did not find the memory range for address {}.".format(address)
            )
        else:
            self.print_async("low region: {} ({}), high region: {} ({})".format(
                range['region_low'], hex(range['region_low']),
                range['region_high'], hex(range['region_high']))
            )
        return range
