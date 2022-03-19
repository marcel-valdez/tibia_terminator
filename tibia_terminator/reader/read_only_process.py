#!/usr/bin/env python3.8

from typing import List, IO, NamedTuple, Optional, Mapping, Any
from ctypes import sizeof, c_byte
from traceback import format_exc
from enum import Enum

import copy
import logging
import re
import os

from mem_edit import Process
from mem_edit.utils import (
    ctypes_buffer_t,
    search_buffer,
    search_buffer_verbatim,
    ctypes_equal,
)

logger = logging.getLogger(__name__)


class MemRegionType(Enum):
    EXE = 0
    CODE = 1
    HEAP = 2
    STACK = 3


class MemRegion(NamedTuple):
    start: int
    end: int
    read: bool
    write: bool
    execute: bool
    private: bool
    shared: bool
    offset: int
    dev_major: int
    dev_minor: int
    inode: int
    filename: str
    load_address: Optional[int] = None
    region_type: Optional[MemRegionType] = None

    @property
    def size(self) -> int:
        return self.end - self.start

    @property
    def has_filename(self) -> bool:
        return self.filename is not None and len(self.filename) > 0

    def copy(self, **updates: Mapping[str, Any]):
        data = self._asdict()
        data.update(updates)
        return MemRegion(**data)


MAP_ENTRY_REGEX_STR = (
    "(?P<start>[0-9a-f]+)-(?P<end>[0-9a-f]+)\\s"
    "(?P<read>[r-])(?P<write>[w-])(?P<exec>[x-])(?P<private>[ps-])\\s"
    "(?P<offset>[0-9a-f]+)\\s"
    "(?P<dev_major>[0-9a-f]+):(?P<dev_minor>[0-9a-f]+)\\s+"
    "(?P<inode>[0-9a-f]+)\\s*"
    "(?P<filename>.*)"
)
MAP_ENTRY_PARSER = re.compile(MAP_ENTRY_REGEX_STR)


class ReadOnlyProcess(Process):
    pid: int = None
    mem: Optional[IO] = None

    def __init__(self, pid: int):
        self.pid = pid
        self.mem: Optional[IO] = None

    def __enter__(self, *args, **kwargs) -> 'ReadOnlyProcess':
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def open(self):
        if not self.mem and not self.pid:
            raise Exception("Process is already closed.")
        self.mem = open("/proc/{}/mem".format(self.pid), mode="rb")

    def close(self):
        self.pid = None
        self.mem.close()
        self.mem = None

    def write_memory(self, base_address: int, write_buffer: ctypes_buffer_t):
        raise Exception("Write not supported by ReadOnlyProcess")

    def read_memory(
        self, base_address: int, read_buffer: ctypes_buffer_t
    ) -> ctypes_buffer_t:
        try:
            self.mem.seek(base_address)
            self.mem.readinto(read_buffer)
        except OSError as ex:
            logging.error(
                "Error while reading a %s of size %s from address %s to %s",
                type(read_buffer),
                sizeof(type(read_buffer)),
                hex(base_address),
                hex(base_address + sizeof(type(read_buffer))),
            )
            raise ex
        return read_buffer

    def parse_memory_map_entry(self, entry: str) -> MemRegion:
        result = MAP_ENTRY_PARSER.match(entry.strip())
        if result:
            return MemRegion(
                start=int(result.group("start").strip(), 16),
                end=int(result.group("end").strip(), 16),
                read=result.group("read").strip() == "r",
                write=result.group("write").strip() == "w",
                execute=result.group("exec").strip() == "x",
                private=result.group("private").strip() == "p",
                shared=result.group("private").strip() == "s",
                offset=int(result.group("offset").strip(), 16),
                dev_major=int(result.group("dev_major").strip(), 16),
                dev_minor=int(result.group("dev_minor").strip(), 16),
                inode=int(result.group("inode").strip()),
                filename=result.group("filename").strip(),
            )

        raise Exception(f"Unable to parse memory map entry: {entry}")

    def list_mapped_regions(self, writeable_only: bool = True) -> List[MemRegion]:
        regions = []
        code_regions = 0
        prev_end = None
        is_exe = False
        exe_regions = 0
        exe_load = None
        exe_name = os.path.realpath(f"/proc/{self.pid}/exe")
        binary_name = ""
        load_addr = None
        region_type = None
        with open("/proc/{}/maps".format(self.pid), "r") as memory_map:
            for map_entry_str in memory_map:
                mem_region = self.parse_memory_map_entry(map_entry_str)
                if code_regions > 0:
                    if (
                        mem_region.execute
                        or (
                            binary_name in mem_region.filename
                            and (
                                mem_region.has_filename or mem_region.start != prev_end
                            )
                        )
                        or code_regions >= 4
                    ):
                        code_regions = 0
                        is_exe = False
                        if exe_regions > 1:
                            exe_regions = 0
                    else:
                        code_regions += 1
                        if is_exe:
                            exe_regions += 1

                if code_regions == 0:
                    if mem_region.execute and mem_region.has_filename:
                        code_regions += 1
                        if exe_name in mem_region.filename:
                            exe_regions = 1
                            exe_load = mem_region.start
                            is_exe = True
                        binary_name = mem_region.filename
                    elif exe_regions == 1 and exe_name in mem_region.filename:
                        exe_regions += 1
                        code_regions = exe_regions
                        load_addr = exe_load
                        is_exe = True
                        binary_name = mem_region.filename

                    if exe_regions < 2:
                        load_addr = mem_region.start

                prev_end = mem_region.end

                # game variables are not stored here
                if "BattlEye" in mem_region.filename:
                    continue

                # consistently fails to be read
                if "anon_inode:" in mem_region.filename:
                    continue

                if (
                    (mem_region.write and writeable_only)
                    and mem_region.read
                    and mem_region.size > 0
                ):
                    if is_exe:
                        region_type = MemRegionType.EXE
                    elif code_regions > 0:
                        region_type = MemRegionType.CODE
                    elif "[heap]" in mem_region.filename:
                        region_type = MemRegionType.HEAP
                    elif "[stack]" in mem_region.filename:
                        region_type = MemRegionType.STACK

                    mem_region.copy(
                        region_type=region_type,
                        load_address=load_addr
                    )
                    regions.append(mem_region)

        return regions

    def search_addresses(
        self,
        addresses: List[int],
        needle_buffer: ctypes_buffer_t,
        verbatim: bool = True,
    ) -> List[int]:
        """
        Search for the provided value at each of the provided addresses, and return the addresses
          where it is found.

        Args:
            addresses: List of addresses which should be probed.
            needle_buffer: The value to search for. This should be a `ctypes` object of the same
                sorts as used by `.read_memory(...)`, which will be compared to the contents of
                memory at each of the given addresses.
            verbatim: If `True`, perform bitwise comparison when searching for `needle_buffer`.
                If `False`, perform `utils.ctypes_equal`-based comparison. Default `True`.

        Returns:
            List of addresses where the `needle_buffer` was found.
        """
        found = []
        read_buffer = copy.copy(needle_buffer)

        if verbatim:
            def compare(a, b):
                return bytes(a) == bytes(b)

        else:
            compare = ctypes_equal

        for address in addresses:
            self.read_memory(address, read_buffer)
            if compare(needle_buffer, read_buffer):
                found.append(address)
        return found

    def search_all_memory(
        self,
        needle_buffer: ctypes_buffer_t,
        writeable_only: bool = True,
        verbatim: bool = True,
    ) -> List[MemRegion]:
        """
        Search the entire memory space accessible to the process for the provided value.

        Args:
            needle_buffer: The value to search for. This should be a ctypes object of the same
                sorts as used by `.read_memory(...)`, which will be compared to the contents of
                memory at each accessible address.
            writeable_only: If `True`, only search regions where the process has write access.
                Default `True`.
            verbatim: If `True`, perform bitwise comparison when searching for `needle_buffer`.
                If `False`, perform `utils.ctypes_equal-based` comparison. Default `True`.

        Returns:
            List of addresses where the `needle_buffer` was found.
        """
        found = []
        if verbatim:
            search = search_buffer_verbatim
        else:
            search = search_buffer

        for map_region in self.list_mapped_regions(writeable_only):
            try:
                region_buffer = (c_byte * (map_region.end - map_region.start))()
                self.read_memory(map_region.start, region_buffer)
                found += [
                    offset + map_region.start
                    for offset in search(needle_buffer, region_buffer)
                ]
            except OSError as error:
                logger.warning("Error: %s", error)
                logger.warning("Traceback: %s", format_exc())
                logger.warning("Failed to read map region: %s", map_region)
        return found
