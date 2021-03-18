#!/usr/bin/env python3.8

from interface.macro.macro import Macro
from keeper.emergency_reporter import EmergencyReporter


class StartEmergencyMacro(Macro):
    def __init__(self, emergency_reporter: EmergencyReporter, hotkey: str):
        super().__init__(hotkey, key_event_type='down')
        self.emergency_reporter = emergency_reporter

    def _action(self):
        self.emergency_reporter.start_emergency_override()
