#!/usr/bin/env python3.8
"""Keeps equipment always ON."""

import time
from equipment_reader import (RingName, AmuletName)

# We throttle commands here and ask the client_interface
# to use 0 throttling.
DEFAULT_EQUIP_FREQ = 0.5
DEFAULT_EQUIP_EMERGENCY_FREQ = 0.5


class EquipmentMode:
    NORMAL = 'normal'
    EMERGENCY = 'emergency'


class EquipmentKeeper:
    def __init__(self, client, emergency_reporter,
                 should_equip_amulet, should_equip_ring, should_eat_food,
                 equip_amulet_secs=DEFAULT_EQUIP_FREQ,
                 equip_ring_secs=DEFAULT_EQUIP_FREQ):
        self.client = client
        self.emergency_reporter = emergency_reporter
        self.should_equip_amulet = should_equip_amulet
        self.should_equip_ring = should_equip_ring
        self.should_eat_food = should_eat_food
        self.equip_amulet_secs = equip_amulet_secs
        self.equip_ring_secs = equip_ring_secs
        self.timestamps = {
            'ring': 0,
            'emergency_ring': 0,
            'amulet': 0,
            'emergency_amulet': 0,
            'food': 0
        }
        self.eat_food_counter = 0
        self.prev_mode = EquipmentMode.NORMAL

    def handle_status_change(self, char_status):
        next_mode = self.get_next_mode()
        if next_mode == EquipmentMode.EMERGENCY:
            self.handle_emergency_status_change(char_status)
            self.prev_mode = next_mode
        elif (next_mode == EquipmentMode.NORMAL and
              self.prev_mode == EquipmentMode.EMERGENCY and
              (self.is_emergency_ring_on(char_status) or
               self.is_emergency_amulet_on(char_status))):
            self.handle_emergency_transition_change(char_status)
        else:
            self.handle_normal_status_change(char_status)
            self.prev_mode = next_mode

    def handle_emergency_transition_change(self, char_status):
        # stay emergency mode until emergency equipment is off
        if self.is_emergency_ring_on(char_status):
            if self.secs_since_toggle_emergency_ring() >= DEFAULT_EQUIP_EMERGENCY_FREQ:
                self.toggle_emergency_ring()
            elif self.secs_since_equip_ring() >= DEFAULT_EQUIP_FREQ:
                self.equip_ring()

        if self.is_emergency_amulet_on(char_status):
            if self.secs_since_toggle_emergency_amulet() >= DEFAULT_EQUIP_EMERGENCY_FREQ:
                self.toggle_emergency_amulet()
            elif self.secs_since_equip_amulet() >= DEFAULT_EQUIP_FREQ:
                self.equip_amulet()

    def handle_emergency_status_change(self, char_status):
        if char_status.emergency_action_amulet == AmuletName.UNKNOWN:
            # Use normal amulets when we don't have emergency amulets
            self.handle_equip_amulet_normal(char_status)
        elif (not self.is_emergency_amulet_on(char_status) and
            self.secs_since_toggle_emergency_amulet() >=
                DEFAULT_EQUIP_EMERGENCY_FREQ):
            self.toggle_emergency_amulet()

        if char_status.emergency_action_ring == RingName.UNKNOWN:
            # Use normal rings when we don't have emergency rings
            self.handle_equip_ring_normal(char_status)
        elif (not self.is_emergency_ring_on(char_status) and
            self.secs_since_toggle_emergency_ring() >=
                DEFAULT_EQUIP_EMERGENCY_FREQ):
            self.toggle_emergency_ring()

    def is_emergency_ring_on(self, char_status):
        return (char_status.equipped_ring ==
            char_status.emergency_action_ring and
            char_status.emergency_action_ring != RingName.UNKNOWN)

    def is_emergency_amulet_on(self, char_status):
        return (char_status.equipped_amulet ==
            char_status.emergency_action_amulet and
            char_status.emergency_action_amulet != AmuletName.UNKNOWN)

    def handle_normal_status_change(self, char_status):
        self.handle_equip_amulet_normal(char_status)
        self.handle_equip_ring_normal(char_status)
        self.handle_eat_food(char_status)

    def handle_equip_amulet_normal(self, char_status):
        if (self.should_equip_amulet and char_status.is_amulet_slot_empty and
           self.secs_since_equip_amulet() >= self.equip_amulet_secs):
            self.equip_amulet()

    def handle_equip_ring_normal(self, char_status):
        if (self.should_equip_ring and char_status.is_ring_slot_empty and
           self.secs_since_equip_ring() >= self.equip_ring_secs):
            self.equip_ring()

    def handle_eat_food(self, char_status):
        if self.should_eat_food and self.secs_since_eat_food() >= 60:
            self.eat_food()

    def secs_since_equip_ring(self):
        return self.timestamp_secs() - self.timestamps['ring']

    def equip_ring(self):
        self.timestamps['ring'] = self.timestamp_secs()
        self.client.equip_ring(0)

    def toggle_emergency_ring(self):
        self.timestamps['emergency_ring'] = self.timestamp_secs()
        self.client.toggle_emergency_ring(0)

    def secs_since_toggle_emergency_ring(self):
        return self.timestamp_secs() - self.timestamps['emergency_ring']

    def secs_since_equip_amulet(self):
        return self.timestamp_secs() - self.timestamps['amulet']

    def equip_amulet(self):
        self.timestamps['amulet'] = self.timestamp_secs()
        self.client.equip_amulet(0)

    def toggle_emergency_amulet(self):
        self.timestamps['emergency_amulet'] = self.timestamp_secs()
        self.client.toggle_emergency_amulet(0)

    def secs_since_toggle_emergency_amulet(self):
        return self.timestamp_secs() - self.timestamps['emergency_amulet']

    def secs_since_eat_food(self):
        return self.timestamp_secs() - self.timestamps['food']

    def eat_food(self):
        self.eat_food_counter += 1
        if self.eat_food_counter == 4:
            self.timestamps['food'] = self.timestamp_secs()
            self.eat_food_counter = 0
        else:
            self.timestamps['food'] += 9

        self.client.eat_food()

    def timestamp_secs(self):
        return time.time()

    def get_next_mode(self):
        if self.emergency_reporter.in_emergency:
            return EquipmentMode.EMERGENCY
        else:
            return EquipmentMode.NORMAL
