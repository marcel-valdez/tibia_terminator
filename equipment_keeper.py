"""Keeps equipment always ON."""

import time

DEFAULT_EQUIP_FREQ = 0.5


class EquipmentKeeper:
    def __init__(self, client, should_equip_amulet, should_equip_ring,
                 should_eat_food, equip_amulet_secs=DEFAULT_EQUIP_FREQ,
                 equip_ring_secs=DEFAULT_EQUIP_FREQ):
        self.client = client
        self.should_equip_amulet = should_equip_amulet
        self.should_equip_ring = should_equip_ring
        self.should_eat_food = should_eat_food
        self.equip_amulet_secs = equip_amulet_secs
        self.equip_ring_secs = equip_ring_secs
        self.timestamps = {
            'ring': 0,
            'amulet': 0,
            'food': 0,
            'magic_shield': 0
        }
        self.eat_food_counter = 0

    def handle_status_change(self, char_status):
        if self.should_equip_amulet and \
           char_status.is_amulet_slot_empty and \
           self.secs_since_equip_amulet() >= \
           self.equip_amulet_secs:
            self.equip_amulet()

        if self.should_equip_ring and \
           char_status.is_ring_slot_empty and \
           self.secs_since_equip_ring() >= \
           self.equip_ring_secs:
            self.equip_ring()

        if self.should_eat_food and \
           self.secs_since_eat_food() >= 60:
            self.eat_food()

    def secs_since_equip_ring(self):
        return self.timestamp_secs() - self.timestamps['ring']

    def equip_ring(self):
        self.timestamps['ring'] = self.timestamp_secs()
        self.client.equip_ring()

    def secs_since_equip_amulet(self):
        return self.timestamp_secs() - self.timestamps['amulet']

    def equip_amulet(self):
        self.timestamps['amulet'] = self.timestamp_secs()
        self.client.equip_amulet()

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
