#!/usr/bin/env python3.8


from macro import Macro

pyautogui.PAUSE = 0.02


class StartEmergencyMacro(Macro):
    def __init__(self, emergency_reporter: EmergencyReporter, hotkey: str):
        super().__init__(hotkey)
        self.emergency_reporter = emergency_reporter

    def _action(self):
        self.emergency_reporter.start_emergency()
