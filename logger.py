#!/usr/bin/env python2.7

import os
from multiprocessing import Pool

global DEBUG_PPOOL
DEBUG_PPOOL = None
global DEBUG_LEVEL
DEBUG_LEVEL = None

def init_debug_ppool():
    global DEBUG_PPOOL
    if DEBUG_PPOOL is None:
        DEBUG_PPOOL = Pool(processes=3)

def init_debug_level():
    global DEBUG_LEVEL
    if DEBUG_LEVEL is None:
        DEBUG_LEVEL = os.getenv("DEBUG", -1)

def set_debug_level(debug_level):
    global DEBUG_LEVEL
    DEBUG_LEVEL = debug_level

def get_debug_level():
    global DEBUG_LEVEL
    return DEBUG_LEVEL


def debug(msg, debug_level=0):
    if get_debug_level() >= debug_level:
        print(msg)

if __name__ != "__main__":
    init_debug_ppool()
    init_debug_level()