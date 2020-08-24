#!/usr/bin/env python2.7

import random
import argparse
import sys
import binascii
import time
import subprocess

from multiprocessing import Pool


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('pid', help='The PID of Tibia')
parser.add_argument('--no_mana_hp',
                    help='Do not monitor mana & hp.',
                    action='store_true')
parser.add_argument('--no_speed',
                    help='Do not monitor speed.',
                    action='store_true')
parser.add_argument('--only_monitor',
                    help='Only print stat changes, no action taken',
                    action='store_true')
PPOOL = None

DEMNOK = {
    'total_hp': 630,
    'total_mana': 2730,
    'base_speed': 205,
    # will use utani hur whenever speed is below this
    'desired_speed': 241,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 100,
    # will use a mana potion whenever there is this much mana missing
    'mana_at_missing': 1000,
    # average heal of exura
    'exura_heal': 137,
    'exura_key': 'b',
    # average heal of exura gran
    'exura_gran_heal': 342,
    'exura_gran_key': 'g',
    # average heal of exura sio
    'exura_sio_heal': 790,
    'exura_sio_key': 't',
    'mana_potion_recover': 200,
    'mana_potion_key': 'Home',
    'utani_hur_key': '4',
    'utani_gran_hur_key': '5'
}

# To get the min average heal of your character use:
# http://www.tibia-stats.com/index.php?akcja=spellDmgCalc
ULTIMATE = {
    'total_hp': 420,
    'total_mana': 1410,
    'base_speed': 160,
    # will use utani hur whenever speed is below this
    'desired_speed': 200,
    # will heal whenever there is this much hp missing (min exura heal)
    'heal_at_missing': 88,
    # will use a mana potion whenever there is this much mana missing
    'mana_at_missing': 410,
    # average heal of exura
    'exura_heal': 100,
    'exura_key': 'b',
    # average heal of exura
    'exura_gran_heal': 255,
    'exura_gran_key': 'g',
    # average heal of exura sio
    'exura_sio_heal': 595,
    'exura_sio_key': 't',
    'mana_potion_recover': 100,
    'mana_potion_key': 'Home',
    'utani_hur_key': '4',
    'utani_gran_hur_key': '5'
}

CHAR = DEMNOK

# this value is obtained by running scanmem on the tibia process
MANA_MEMORY_ADDRESS = "5244f00"  # [I32 I16 ]
HP_MEMORY_ADDRESS = "51dbf78"   # [I32 I16 ]

# common value
# 187c810100000000, line: 2038 out of 2048
# 2038 * 8 = 16304, 2048 * 8 = 16384
# 16384 - 16304 = 80 (0x50)
SPEED_MEMORY_ADDRESS = "c41aff0"  # (ultimate) "97e9f10" # (demnok) "9237b70"
SPEED_HARDCODED_OFFSET_VALUE = (
    # 18 7c 81 01 00 00 00 00
    "187c810100000000"
)
SPEED_HARDCODED_OFFSET_VALUE_SIZE = len(SPEED_HARDCODED_OFFSET_VALUE) / 2
# 88 (0x58)
SPEED_OFFSET_AMOUNT = 88

MANA_HARDCODED_OFFSET_VALUE = (
    "824994C7F27F00002E0070006E006700"
    "A0000000000000006100000000000000"
)
MANA_HARDCODED_OFFSET_VALUE_SIZE = len(MANA_HARDCODED_OFFSET_VALUE) / 2
MANA_OFFSET_AMOUNT = 23040


class ManaKeeper:

    def __init__(self,
                 proc_id,
                 tibia_wid,
                 enable_mana_hp=True,
                 enable_speed=True,
                 only_monitor=False):
        # proc_id should be int
        self.__proc_id = proc_id
        self.tibia_wid = tibia_wid
        self.enable_speed = enable_speed
        self.enable_mana_hp = enable_mana_hp
        self.only_monitor = only_monitor

    def find_target_range(self, known_value_addr):
        target = int(known_value_addr, 16)
        maps_file = open("/proc/{}/maps".format(self.__proc_id), 'r')

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
        print_async("Scanning memory, this could take a few seconds....")
        region_low = heap_regions["region_low"]
        region_high = heap_regions["region_high"]
        # TODO: Make it possible to read a memory dump file instead of /proc/xxx/mem
        with open("/proc/{}/mem".format(self.__proc_id), 'rb') as mem_file:
            # Goto the start address of our heap
            mem_file.seek(region_low)
            # Just a buffer so we know what address we are at currently
            search_signature_addr = region_low
            upper_hardcoded_value = hardcoded_value.upper()
            # Stop searching when we exit end of heap
            print_async("Starting search at: " + hex(search_signature_addr))
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
                    print_async(
                        "Signature found at - " + str(signature_addr_start)
                        + " (" + hex(signature_addr_start) + ")"
                    )
                    return signature_addr_start + offset_amount

    def read_address(self, address, size):
        mem_file = open("/proc/{}/mem".format(self.__proc_id), 'rb')
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
            print_async("low region: {} ({}), high region: {} ({})".format(
                range['region_low'], hex(range['region_low']),
                range['region_high'], hex(range['region_high']))
            )
        return range

    def monitor_char(self):
        mana_address = None
        hp_address = None
        if self.enable_mana_hp:
            print_async("Searching mana value address...")
            mana_address = int(MANA_MEMORY_ADDRESS, 16)
            #mana_range = self.get_range(MANA_MEMORY_ADDRESS)
            #mana_address = self.find_value_address(
            #    mana_range,
            #    MANA_OFFSET_AMOUNT,
            #    MANA_HARDCODED_OFFSET_VALUE,
            #    MANA_HARDCODED_OFFSET_VALUE_SIZE
            #)
            if mana_address is None:
                raise Exception("Could not find the mana memory address. The "
                  "hardcoded offset is stale.")
            hp_address = mana_address - 8
            print_async(
                "Mana memory address is - " + str(mana_address)
                + " (" + hex(mana_address) + ")"
            )
            print_async(
                "HP memory address is - " + str(hp_address)
                + " (" + hex(hp_address) + ")"
            )

        if self.enable_speed:
            print_async("Searching speed value address...")
            speed_address = int(SPEED_MEMORY_ADDRESS, 16)
#            speed_range = self.get_range(SPEED_MEMORY_ADDRESS)
#            speed_address = self.find_value_address(
#                speed_range,
#                SPEED_OFFSET_AMOUNT,
#                SPEED_HARDCODED_OFFSET_VALUE,
#                SPEED_HARDCODED_OFFSET_VALUE_SIZE
#            )
            if speed_address is None:
                raise Exception("Could not find the speed memory address. The "
                  "hardcoded offset is stale.")

            print_async(
                "Speed memory address is - " + str(speed_address)
                + " (" + hex(speed_address) + ")"
            )

        prev_mana_value = -1
        prev_hp_value = -1
        prev_speed_value = -1
        while True:
            if self.enable_mana_hp:
                mana_value = self.read_address(mana_address, 4)
                self.handle_mana_change(mana_value)
                if mana_value != prev_mana_value:
                    prev_mana_value = mana_value
                    print_async("Mana: {}".format(str(mana_value)))

                hp_value = self.read_address(hp_address, 4)
                self.handle_hp_change(hp_value)
                if hp_value != prev_hp_value:
                    prev_hp_value = hp_value
                    print_async("HP: {}".format(str(hp_value)))

            if self.enable_speed:
                speed_value = self.read_address(speed_address, 2)
                self.handle_speed_change(speed_value)
                if speed_value != prev_speed_value:
                    prev_speed_value = speed_value
                    print_async("Speed: {}".format(str(speed_value)))

            time.sleep(0.1)

    def handle_hp_change(self, hp):
        missing_hp = CHAR['total_hp'] - hp
        if missing_hp >= CHAR['heal_at_missing']:
            if missing_hp <= CHAR['exura_heal']:
                print_async('Exura!')
                self.send_keystroke(CHAR['exura_key'])
            elif missing_hp <= CHAR['exura_gran_heal']:
                print_async('Exura Gran!')
                self.send_keystroke(CHAR['exura_gran_key'])
            else:
                self.send_keystroke(CHAR['exura_sio_key'])
                print_async('Exura sio!')

    def handle_mana_change(self, mana):
        missing_mana = CHAR['total_mana'] - mana
        if missing_mana >= CHAR['mana_at_missing']:
            print_async('Use mana potion!')
            self.send_keystroke(CHAR['mana_potion_key'])

    def handle_speed_change(self, speed):
        if speed < CHAR['desired_speed']:
            print_async('Use utani hur!')
            self.send_keystroke(CHAR['utani_hur_key'])

    def send_keystroke(self, key):
        delay = random.randint(75, 125)
        # there will be a random delay between 75ms and 150ms
        time.sleep(delay / 1000)
        # asynchronously send the keystroke
        if not self.only_monitor:
            subprocess.Popen([
                "/usr/bin/xdotool", "key",
                "--window", str(self.tibia_wid),
                str(key)
            ])


def get_tibia_wid():
    wid = subprocess.check_output([
        "/usr/bin/xdotool", "search", "--class", "Tibia"
    ], stderr=subprocess.STDOUT)
    print_async('tibia wid:' + str(wid))
    return wid

def fprint(fargs):
    print(fargs)

def print_async(*pargs):
    if PPOOL is None:
        print(pargs)
    else:
        PPOOL.apply_async(fprint, tuple(pargs))


def main(pid, no_mana_hp, no_speed, only_monitor):
    if pid is None or pid == "":
        raise Exception("PID is required, you may use psgrep -a -l bin/Tibia "
                        "to find the process id")

    mana_keeper = ManaKeeper(pid,
                             get_tibia_wid(),
                             not no_mana_hp,
                             not no_speed,
                             only_monitor)
    mana_keeper.monitor_char()


if __name__ == "__main__":
    args = parser.parse_args()
    PPOOL = Pool(processes=3)
    main(args.pid, args.no_mana_hp, args.no_speed, args.only_monitor)
