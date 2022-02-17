#!/usr/bin/env python3.8

from tibia_terminator.interface.macro.macro import Macro
from tibia_terminator.keeper.emergency_reporter import (
    EmergencyReporter,
    TankModeReporter,
)


class StartEmergencyMacro(Macro):
    def __init__(
        self,
        emergency_reporter: EmergencyReporter,
        tank_mode_reporter: TankModeReporter,
        hotkey: str,
    ):
        super().__init__(hotkey, key_event_type="down")
        self.emergency_reporter = emergency_reporter
        self.tank_mode_reporter = tank_mode_reporter

    def _action(self, _=None):
        self.tank_mode_reporter.stop_tank_mode()
        self.emergency_reporter.start_emergency_override()


class StartTankModeMacro(Macro):
    def __init__(
        self,
        tank_mode_reporter: TankModeReporter,
        emergency_reporter: EmergencyReporter,
        hotkey: str,
    ):
        super().__init__(hotkey, key_event_type="down")
        self.tank_mode_reporter = tank_mode_reporter
        self.emergency_reporter = emergency_reporter

    def _action(self, _=None):
        self.emergency_reporter.stop_emergency_override()
        self.tank_mode_reporter.start_tank_mode()
