#!/usr/bin/env python3.8

import queue
import subprocess
import threading
import time
from typing import Dict, List, Callable

from logger import ActionLogEntry, StatsLogger, debug, get_debug_level
from random import randint


def timestamp_ms():
    return int(round(time.time() * 1000))


class CommandType():
    HEAL_SPELL = 'heal_spell'
    EQUIP_ITEM = 'equip_item'
    USE_ITEM = 'use_item'
    UTILITY_SPELL = 'utility_spell'

    @staticmethod
    def types() -> List[str]:
        return [CommandType.HEAL_SPELL, CommandType.EQUIP_ITEM,
                CommandType.USE_ITEM, CommandType.UTILITY_SPELL]


class Command():
    def __init__(self, cmd_type: str, throttle_ms: int):
        self.cmd_type = cmd_type
        self.throttle_ms = throttle_ms

    def _send(self, tibia_wid):
        raise Exception("Needs to be implemented by subclass")

class KeeperHotkeyCommand(Command):
    """Hotkey command issued by one of Terminator's keepers."""

    def __init__(self, cmd_type: str, throttle_ms: int, hotkey: str):
        super().__init__(cmd_type, throttle_ms)
        self.hotkey = hotkey

    def _send(self, tibia_wid):
        subprocess.Popen([
            "/usr/bin/xdotool", "key", "--window",
            str(tibia_wid),
            self.hotkey
        ])

    def __str__(self):
        return f'[keystroke] {self.cmd_type} ({self.throttle_ms}): {self.hotkey}'


class MacroCommand(Command):
    def __init__(self, cmd_type: str, throttle_ms: int, macro_fn: Callable[[str], None]):
        super().__init__(cmd_type, throttle_ms)
        self.macro_fn = macro_fn

    def _send(self, tibia_wid):
        self.macro_fn(str(tibia_wid))

    def __str__(self):
        return f'[macro] {self.cmd_type} ({self.throttle_ms})'


class CommandSender(threading.Thread):

    STOP_COMMAND = Command('stop', 0)

    def __init__(self, tibia_wid, logger: StatsLogger, only_monitor: bool):
        super().__init__(daemon=True)
        self.tibia_wid = tibia_wid
        self.cmd_queue = queue.Queue()
        self.logger = logger
        self.only_monitor = only_monitor
        self.last_cmd_ts = 0

    def send(self, command: Command):
        self.cmd_queue.put_nowait(command)

    def stop(self):
        self.cmd_queue.put_nowait(CommandSender.STOP_COMMAND)

    def __log_cmd(self, cmd: Command):
        self.logger.log_action(0, str(cmd))

    def __throttle(self, throttle_ms: int=250):
        """Throttles an action.
        Returns:

            bool: False if the action should be throttled (not executed),
                    True otherwise.
        """
        return timestamp_ms() - self.last_cmd_ts >= throttle_ms

    def run(self):
        while True:
            cmd = self.cmd_queue.get()
            if cmd == CommandSender.STOP_COMMAND:
                break
            elif self.__throttle(cmd.throttle_ms):
                self.last_cmd_ts = timestamp_ms()
                if not self.only_monitor:
                    cmd._send(self.tibia_wid)
                self.__log_cmd(cmd)


class CommandProcessor():
    def __init__(self, tibia_wid: str, logger: StatsLogger, only_monitor: bool,
                 cmd_senders: Dict[str, CommandSender] = None):
        self.cmd_senders = cmd_senders or CommandProcessor.gen_cmd_senders(
            tibia_wid, logger, only_monitor)
        self.started = False
        self.stopped = False

    def start(self):
        if self.stopped:
            raise Exception('This command processor has already been '
                            'stopped. Create a new one and start it.')

        if not self.started:
            for sender in self.cmd_senders.values():
                sender.start()
            self.started = True

    def stop(self):
        if not self.started:
            raise Exception('This command processor has not been started yet.')

        if not self.stopped:
            for sender in self.cmd_senders.values():
                sender.stop()
            self.stopped = True

    def send(self, cmd: Command):
        self.cmd_senders[cmd.cmd_type].send(cmd)

    @staticmethod
    def gen_cmd_senders(tibia_wid: str, logger: StatsLogger, only_monitor: bool) -> Dict[str, CommandSender]:
        cmd_senders = {}
        for cmd_type in CommandType.types():
            cmd_senders[cmd_type] = CommandSender(
                tibia_wid, logger, only_monitor)

        return cmd_senders


class ClientInterface:
    def __init__(self, hotkeys_config, logger: StatsLogger=None,
                 cmd_processor: CommandProcessor = None):
        self.hotkeys_config = hotkeys_config
        self.logger = logger
        self.cmd_processor = cmd_processor

    def send_keystroke_async(self, cmd_type: str, throttle_ms: int, hotkey: str):
        self.cmd_processor.send(
            KeeperHotkeyCommand(cmd_type, throttle_ms, hotkey))

    def cast_exura(self, throttle_ms: int):
        self.logger.log_action(2, f'cast_exura {throttle_ms} ms')
        self.send_keystroke_async(CommandType.HEAL_SPELL, throttle_ms,
                                  self.hotkeys_config['exura'])

    def cast_exura_gran(self, throttle_ms: int):
        self.logger.log_action(2, f'cast_exura_gran {throttle_ms} ms')
        self.send_keystroke_async(CommandType.HEAL_SPELL, throttle_ms,
                                  self.hotkeys_config['exura_gran'])

    def cast_exura_sio(self, throttle_ms: int):
        self.logger.log_action(2, f'cast_exura_sio {throttle_ms} ms')
        self.send_keystroke_async(CommandType.HEAL_SPELL, throttle_ms,
                                  self.hotkeys_config['exura_sio'])

    def drink_mana(self, throttle_ms: int):
        self.logger.log_action(2, f'drink_mana {throttle_ms} ms')
        self.send_keystroke_async(CommandType.USE_ITEM, throttle_ms,
                                  self.hotkeys_config['mana_potion'])

    def cast_haste(self, throttle_ms: int):
        self.logger.log_action(2, f'cast_haste {throttle_ms} ms')
        self.send_keystroke_async(CommandType.UTILITY_SPELL, throttle_ms,
                                  self.hotkeys_config['utani_hur'])

    def equip_ring(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'equip_ring {throttle_ms} ms')
        self.send_keystroke_async(CommandType.EQUIP_ITEM, throttle_ms,
                                  self.hotkeys_config['equip_ring'])

    def toggle_emergency_ring(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'toggle_emergency_ring {throttle_ms} ms')
        self.send_keystroke_async(CommandType.EQUIP_ITEM, throttle_ms,
                                  self.hotkeys_config['toggle_emergency_ring'])

    def equip_amulet(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'equip_amulet {throttle_ms} ms')
        self.send_keystroke_async(CommandType.EQUIP_ITEM, throttle_ms,
                                  self.hotkeys_config['equip_amulet'])

    def toggle_emergency_amulet(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'toggle_emergency_amulet {throttle_ms} ms')
        self.send_keystroke_async(CommandType.EQUIP_ITEM, throttle_ms,
                                  self.hotkeys_config[
                                      'toggle_emergency_amulet'])

    def eat_food(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'eat_food {throttle_ms} ms')
        self.send_keystroke_async(CommandType.USE_ITEM, throttle_ms,
                                  self.hotkeys_config['eat_food'])

    def cast_magic_shield(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'cast_magic_shield {throttle_ms} ms')
        self.send_keystroke_async(CommandType.UTILITY_SPELL, throttle_ms,
                                  self.hotkeys_config['magic_shield'])

    def cancel_magic_shield(self, throttle_ms: int = 250):
        self.logger.log_action(2, f'cancel_magic_shield {throttle_ms} ms')
        self.send_keystroke_async(CommandType.UTILITY_SPELL, throttle_ms,
                                  self.hotkeys_config['cancel_magic_shield'])

    def execute_macro(self, macro_fn: Callable[[str], None], cmd_type: str, throttle_ms: int = 125):
        self.logger.log_action(2, f'execute_macro {throttle_ms} ms')
        self.cmd_processor.send(MacroCommand(cmd_type, throttle_ms, macro_fn))


class FakeLogger():
    def log_action(self, debug_level: int, msg: str):
        print(f'{debug_level}, {msg}')


class FakeCommandSender(CommandSender):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_keystroke(self, hotkey: str):
        print(f'_send_keystroke {hotkey}')


def main():
    hotkeys = {
        'exura': 'exura_key',
        'exura_gran': 'exura_gran_key',
        'exura_sio': 'exura_sio_key',
        'mana_potion': 'mana_key',
        'utani_hur': 'haste_key',
        'equip_ring': 'ring_key',
        'equip_amulet': 'equip_amulet_key',
        'toggle_emergency_ring': 'emergency_ring_key',
        'toggle_emergency_amulet': 'emergency_amulet_key',
        'eat_food': 'eat_key',
        'magic_shield': 'shield_on_key',
        'cancel_magic_shield': 'shield_off_key'
    }

    fake_logger = FakeLogger()
    cmd_processor = CommandProcessor(
        tibia_wid="fake_tibia_wid",
        logger=fake_logger,
        only_monitor=False,
        cmd_senders={
            CommandType.EQUIP_ITEM: FakeCommandSender(
                "fake_tibia_wid", fake_logger, False
            ),
            CommandType.HEAL_SPELL: FakeCommandSender(
                "fake_tibia_wid", fake_logger, False
            ),
            CommandType.USE_ITEM: FakeCommandSender(
                "fake_tibia_wid", fake_logger, False
            ),
            CommandType.UTILITY_SPELL: FakeCommandSender(
                "fake_tibia_wid", fake_logger, False
            )
        }
    )
    client_interface = ClientInterface(hotkeys, fake_logger, cmd_processor)
    cmd_processor.start()
    method_names = [
        'cast_exura',
        'cast_exura_gran',
        'cast_exura_sio',
        'drink_mana',
        'cast_haste',
        'equip_ring',
        'toggle_emergency_ring',
        'equip_amulet',
        'toggle_emergency_amulet',
        'eat_food',
        'cast_magic_shield',
        'cancel_magic_shield'
    ]

    try:
        while True:
            cmd_index = randint(0, len(method_names) - 1)
            cmd_name = method_names[cmd_index]
            throttle_ms = randint(125, 500)
            getattr(client_interface, cmd_name)(throttle_ms)
            # sleep 100 ms
            time.sleep(0.1)
    finally:
        cmd_processor.stop()


if __name__ == "__main__":
    main()
