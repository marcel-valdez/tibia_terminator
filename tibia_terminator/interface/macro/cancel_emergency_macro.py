#!/usr/bin/env python3.8

from tibia_terminator.interface.macro.macro import Macro
from tibia_terminator.keeper.emergency_reporter import EmergencyReporter


class CancelEmergencyMacro(Macro):
    def __init__(self, emergency_reporter: EmergencyReporter, hotkey: str):
        super().__init__(hotkey, key_event_type='down')
        self.emergency_reporter = emergency_reporter

    def _action(self):
        self.emergency_reporter.stop_emergency_override()
