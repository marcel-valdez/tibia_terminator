#!/usr/bin/env python3.8
"""Keeps equipment always ON."""

import time

from typing import Callable

from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.reader.equipment_reader import RingName, AmuletName
from tibia_terminator.keeper.emergency_reporter import (
    EmergencyReporter,
    TankModeReporter,
)

# We throttle commands here and ask the client_interface
# to use 0 throttling.
DEFAULT_EQUIP_FREQ = 0.25
DEFAULT_EQUIP_EMERGENCY_FREQ = 0.25


class EquipmentMode:
    NORMAL = "normal"
    TANK = "tank"
    EMERGENCY = "emergency"


class EquipmentKeeper:
    def __init__(
        self,
        client: ClientInterface,
        emergency_reporter: EmergencyReporter,
        tank_mode_reporter: TankModeReporter,
        should_equip_amulet: bool,
        should_equip_ring: bool,
        should_eat_food: bool,
        equip_amulet_secs: float = DEFAULT_EQUIP_FREQ,
        equip_ring_secs: float = DEFAULT_EQUIP_FREQ,
    ):
        self.client = client
        self.emergency_reporter = emergency_reporter
        self.tank_mode_reporter = tank_mode_reporter
        self.should_equip_amulet = should_equip_amulet
        self.should_equip_ring = should_equip_ring
        self.should_eat_food = should_eat_food
        self.equip_amulet_secs = equip_amulet_secs
        self.equip_ring_secs = equip_ring_secs
        self.timestamps = {
            "food": 0.0
        }
        self.eat_food_counter = 0
        self.prev_mode = EquipmentMode.NORMAL
        self.normal_mode_manager = EquipmentModeManager(
            toggle_amulet_fn=self.client.equip_amulet,
            toggle_ring_fn=self.client.equip_ring,
            amulet_checker_fn=self.is_normal_amulet_on,
            ring_checker_fn=self.is_normal_ring_on,
            toggle_frequency_sec=DEFAULT_EQUIP_FREQ,
        )
        self.tank_mode_manager = EquipmentModeManager(
            toggle_amulet_fn=self.client.toggle_tank_amulet,
            toggle_ring_fn=self.client.toggle_tank_ring,
            amulet_checker_fn=self.is_tank_amulet_on,
            ring_checker_fn=self.is_tank_ring_on,
            toggle_frequency_sec=DEFAULT_EQUIP_FREQ,
        )
        self.emergency_mode_manager = EquipmentModeManager(
            toggle_amulet_fn=self.client.toggle_emergency_amulet,
            toggle_ring_fn=self.client.toggle_emergency_ring,
            amulet_checker_fn=self.is_emergency_amulet_on,
            ring_checker_fn=self.is_emergency_ring_on,
            toggle_frequency_sec=DEFAULT_EQUIP_FREQ,
        )

    def handle_status_change(self, char_status: CharStatus):
        next_mode = self.get_next_mode()
        if next_mode == EquipmentMode.EMERGENCY:
            self.handle_emergency_status_change(char_status)
            self.prev_mode = next_mode
            return
        elif self.prev_mode == EquipmentMode.EMERGENCY:
            if self.is_emergency_ring_on(char_status) or self.is_emergency_amulet_on(
                char_status
            ):
                self.handle_emergency_transition_change(char_status, next_mode)
            else:
                self.prev_mode = next_mode
            return

        if next_mode == EquipmentMode.TANK:  # implies prev_mode = NORMAL
            self.handle_tank_status_change(char_status)
            self.prev_mode = next_mode
        elif self.prev_mode == EquipmentMode.TANK:  # implies next_mode = NORMAL
            if self.is_tank_ring_on(char_status) or self.is_tank_amulet_on(char_status):
                self.handle_tank_transition_change(char_status)
            else:
                self.prev_mode = next_mode
        else:
            self.handle_normal_status_change(char_status)
            self.prev_mode = next_mode

    def handle_normal_status_change(self, char_status: CharStatus):
        self.normal_mode_manager.toggle_amulet_on(char_status)
        self.normal_mode_manager.toggle_ring_on(char_status)
        self.handle_eat_food()

    def handle_emergency_transition_change(
        self, char_status: CharStatus, next_mode: str
    ):
        toggled_amulet = self.emergency_mode_manager.toggle_amulet_off(char_status)
        if not toggled_amulet:
            if next_mode == EquipmentMode.TANK:
                self.tank_mode_manager.toggle_amulet_on(char_status)
            else:
                self.normal_mode_manager.toggle_amulet_on(char_status)

        toggled_ring = self.emergency_mode_manager.toggle_ring_off(char_status)
        if not toggled_ring:
            if next_mode == EquipmentMode.TANK:
                self.tank_mode_manager.toggle_ring_on(char_status)
            else:
                self.normal_mode_manager.toggle_ring_on(char_status)

    def handle_emergency_status_change(self, char_status: CharStatus):
        mode_manager_for_amulet = self.emergency_mode_manager
        if char_status.emergency_action_amulet == AmuletName.UNKNOWN:
            # Use tank -> normal amulets when we don't have emergency amulets
            if char_status.tank_action_amulet != AmuletName.UNKNOWN:
                mode_manager_for_amulet = self.tank_mode_manager
            else:
                mode_manager_for_amulet = self.normal_mode_manager
        mode_manager_for_amulet.toggle_amulet_on(char_status)

        mode_manager_for_ring = self.emergency_mode_manager
        if char_status.emergency_action_ring == RingName.UNKNOWN:
            # Use tank -> normal rings when we don't have emergency rings
            if char_status.tank_action_ring != AmuletName.UNKNOWN:
                mode_manager_for_ring = self.tank_mode_manager
            else:
                mode_manager_for_ring = self.normal_mode_manager
        mode_manager_for_ring.toggle_ring_on(char_status)

    def handle_tank_transition_change(self, char_status: CharStatus):
        toggled_amulet = self.tank_mode_manager.toggle_amulet_off(char_status)
        if not toggled_amulet:
            self.normal_mode_manager.toggle_amulet_on(char_status)

        toggled_ring = self.tank_mode_manager.toggle_ring_off(char_status)
        if not toggled_ring:
            self.normal_mode_manager.toggle_ring_on(char_status)

    def handle_tank_status_change(self, char_status: CharStatus):
        mode_manager_for_amulet = self.tank_mode_manager
        if char_status.tank_action_amulet == AmuletName.UNKNOWN:
            # Use normal amulets when we don't have tank amulets
            mode_manager_for_amulet = self.normal_mode_manager
        mode_manager_for_amulet.toggle_amulet_on(char_status)

        mode_manager_for_ring = self.tank_mode_manager
        if char_status.tank_action_ring == RingName.UNKNOWN:
            # Use normal rings when we don't have tank rings
            mode_manager_for_ring = self.normal_mode_manager
        mode_manager_for_ring.toggle_ring_on(char_status)

    def is_normal_amulet_on(self, char_status: CharStatus) -> bool:
        return char_status.equipped_amulet != AmuletName.EMPTY

    def is_tank_amulet_on(self, char_status: CharStatus):
        return (
            char_status.equipped_amulet == char_status.tank_action_amulet
            and char_status.tank_action_amulet != AmuletName.UNKNOWN
        )

    def is_emergency_amulet_on(self, char_status: CharStatus) -> bool:
        return (
            char_status.equipped_amulet == char_status.emergency_action_amulet
            and char_status.emergency_action_amulet != AmuletName.UNKNOWN
        )

    def is_normal_ring_on(self, char_status: CharStatus) -> bool:
        return char_status.equipped_ring != RingName.EMPTY

    def is_tank_ring_on(self, char_status: CharStatus):
        return (
            char_status.equipped_ring == char_status.tank_action_ring
            and char_status.tank_action_ring != RingName.UNKNOWN
        )

    def is_emergency_ring_on(self, char_status: CharStatus) -> bool:
        return (
            char_status.equipped_ring == char_status.emergency_action_ring
            and char_status.emergency_action_ring != RingName.UNKNOWN
        )

    def handle_eat_food(self):
        if self.should_eat_food and self.secs_since_eat_food() >= 60:
            self.eat_food()

    def secs_since_eat_food(self) -> float:
        return self.timestamp_secs() - self.timestamps["food"]

    def eat_food(self) -> None:
        self.eat_food_counter += 1
        if self.eat_food_counter == 4:
            self.timestamps["food"] = self.timestamp_secs()
            self.eat_food_counter = 0
        else:
            self.timestamps["food"] += 9

        self.client.eat_food()

    def timestamp_secs(self) -> float:
        return time.time()

    def get_next_mode(self) -> str:
        if self.emergency_reporter.is_in_emergency():
            return EquipmentMode.EMERGENCY
        if self.tank_mode_reporter.is_tank_mode_on():
            return EquipmentMode.TANK
        return EquipmentMode.NORMAL


class EquipmentModeManager:
    def __init__(
        self,
        toggle_amulet_fn: Callable[[int], None],
        toggle_ring_fn: Callable[[int], None],
        amulet_checker_fn: Callable[[CharStatus], bool],
        ring_checker_fn: Callable[[CharStatus], bool],
        toggle_frequency_sec: float,
        toggle_threshold_sec: float = 0.0,
    ):
        self.toggle_ring_fn = toggle_ring_fn
        self.toggle_amulet_fn = toggle_amulet_fn
        self.ring_checker_fn = ring_checker_fn
        self.amulet_checker_fn = amulet_checker_fn
        self.toggle_ring_fn = toggle_ring_fn
        self.toggle_frequency_sec = toggle_frequency_sec
        self.toggle_threshold_sec = toggle_threshold_sec
        self.amulet_equip_ts = 0.0
        self.ring_equip_ts = 0.0

    def toggle_amulet_on(self, char_status: CharStatus) -> bool:
        if not self.amulet_checker_fn(char_status):
            return self.toggle_amulet()
        return False

    def toggle_amulet_off(self, char_status: CharStatus) -> bool:
        if self.amulet_checker_fn(char_status):
            return self.toggle_amulet()
        return False

    def toggle_amulet(self) -> bool:
        now = self.timestamp_secs()
        if now - self.amulet_equip_ts >= self.toggle_frequency_sec:
            self.amulet_equip_ts = now
            self.toggle_amulet_fn(int(self.toggle_threshold_sec * 1000))
            return True
        return False

    def toggle_ring_on(self, char_status: CharStatus) -> bool:
        if not self.ring_checker_fn(char_status):
            return self.toggle_ring()
        return False

    def toggle_ring_off(self, char_status: CharStatus) -> bool:
        if self.ring_checker_fn(char_status):
            return self.toggle_ring()
        return False

    def toggle_ring(self) -> bool:
        now = self.timestamp_secs()
        if now - self.ring_equip_ts >= self.toggle_frequency_sec:
            self.ring_equip_ts = now
            self.toggle_ring_fn(int(self.toggle_threshold_sec * 1000))
            return True
        return False

    def secs_since_toggle_amulet(self) -> float:
        return self.timestamp_secs() - self.amulet_equip_ts

    def secs_since_toggle_ring(self) -> float:
        return self.timestamp_secs() - self.ring_equip_ts

    def timestamp_secs(self) -> float:
        return time.time()
