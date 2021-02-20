#!/usr/bin/env python2.7

import queue
import subprocess
import threading
import time
from typing import Dict

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
    def types():
        return [CommandType.HEAL_SPELL, CommandType.EQUIP_ITEM,
                CommandType.USE_ITEM, CommandType.UTILITY_SPELL]


class Command():
    def __init__(self, throttle_key, throttle_ms, hotkey):
        self.throttle_key = throttle_key
        self.throttle_ms = throttle_ms
        self.hotkey = hotkey


class CommandSender(threading.Thread):
    def __init__(self, tibia_wid, logger: StatsLogger, only_monitor):
        super().__init__(daemon=True)
        self.tibia_wid = tibia_wid
        self.cmd_queue = queue.Queue()
        self.stopped = False
        self.logger = logger
        self.only_monitor = only_monitor
        self.last_cmd_ts = 0

    def send(self, command):
        self.cmd_queue.put(command)

    def stop(self):
        self.stopped = True

    def _send_keystroke(self, hotkey):
        subprocess.Popen([
            "/usr/bin/xdotool", "key", "--window",
            str(self.tibia_wid),
            str(hotkey)
        ])

    def __log_cmd(self, cmd):
        msg = f'[send_keystroke] {cmd.throttle_key} ({cmd.throttle_ms}): {cmd.hotkey}'
        self.logger.log_action(0, msg)

    def __throttle(self, throttle_ms=250):
        """Throttles an action.
        Returns:

            bool: False if the action should be throttled (not executed),
                    True otherwise.
        """
        return timestamp_ms() - self.last_cmd_ts >= throttle_ms

    def run(self):
        while not self.stopped:
            if self.cmd_queue.qsize() > 0:
                cmd = self.cmd_queue.get()
                if self.__throttle(cmd.throttle_ms):
                    self.last_cmd_ts = timestamp_ms()
                    if not self.only_monitor:
                        self._send_keystroke(cmd.hotkey)
                    self.__log_cmd(cmd)
            else:
                # sleep 10 ms
                time.sleep(0.01)


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
        self.cmd_senders[cmd.throttle_key].send(cmd)

    @staticmethod
    def gen_cmd_senders(tibia_wid: str, logger: StatsLogger, only_monitor: bool) -> Dict[str, CommandSender]:
        cmd_senders = {}
        for cmd_type in CommandType.types():
            cmd_senders[cmd_type] = CommandSender(
                tibia_wid, logger, only_monitor)

        return cmd_senders


class ClientInterface:
    def __init__(self, hotkeys_config, logger=None,
                 cmd_processor: CommandProcessor = None):
        self.hotkeys_config = hotkeys_config
        self.logger = logger
        self.cmd_processor = cmd_processor

    def send_keystroke_async(self, throttle_key: str, throttle_ms: int, hotkey: str):
        self.cmd_processor.send(
            Command(throttle_key, throttle_ms, hotkey))

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


class FakeLogger():
    def log_action(self, debug_level, msg):
        print(f'{debug_level}, {msg}')


class FakeCommandSender(CommandSender):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_keystroke(self, hotkey):
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
