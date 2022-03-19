#!/usr/bin/env python3.8

from typing import Sequence

from tibia_terminator.interface.macro.macro import Macro
from tibia_terminator.keeper.emergency_reporter import (
    SimpleModeReporter,
)


class StartModeMacro(Macro):
    def __init__(
        self,
        mode_reporter: SimpleModeReporter,
        hotkey: str,
        exclusive_mode_reporters: Sequence[SimpleModeReporter] = (),
    ):
        super().__init__(hotkey, key_event_type="down")
        self.mode_reporter = mode_reporter
        self.exclusive_mode_reporters = exclusive_mode_reporters

    def _action(self, _=None):
        for exclusive_mode_reporter in self.exclusive_mode_reporters:
            exclusive_mode_reporter.stop_mode()
        self.mode_reporter.start_mode()
