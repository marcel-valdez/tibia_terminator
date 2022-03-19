#!/usr/bin/env python3.8

from tibia_terminator.interface.macro.macro import Macro
from tibia_terminator.keeper.emergency_reporter import SimpleModeReporter


class CancelModeMacro(Macro):
    def __init__(self, mode_reporter: SimpleModeReporter, hotkey: str):
        super().__init__(hotkey, key_event_type='down')
        self.mode_reporter = mode_reporter

    def _action(self, _=None):
        self.mode_reporter.stop_mode()
