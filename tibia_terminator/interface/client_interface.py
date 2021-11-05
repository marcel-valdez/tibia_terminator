#!/usr/bin/env python3.8

import queue
import subprocess
import threading
import time

from enum import Enum
from typing import Dict, List, Callable, Tuple
from random import randint
from collections import deque

from tibia_terminator.common.logger import StatsLogger
from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig


def timestamp_ms():
    return int(round(time.time() * 1000))



class ThrottleBehavior(Enum):
    # DEFAULT = DROP
    DEFAULT = 1
    # The command should be dropped if it is throttled.
    DROP = 1
    # The command should be requeued at the back of the queue if it is throttled.
    REQUEUE_BACK = 2
    # The command should be requeued at the front of the queue if it is throttled.
    REQUEUE_TOP = 3
    # The command should be executed and ignore throttle (this can be achieved with
    # a throttle_ms value of 0), this should very rarely be used.
    FORCE = 4


class CommandType:
    HEAL_SPELL = "heal_spell"
    EQUIP_ITEM = "equip_item"
    USE_ITEM = "use_item"
    UTILITY_SPELL = "utility_spell"

    @staticmethod
    def types() -> List[str]:
        return [
            CommandType.HEAL_SPELL,
            CommandType.EQUIP_ITEM,
            CommandType.USE_ITEM,
            CommandType.UTILITY_SPELL,
        ]


class CommandProfile:
    type: CommandType = None
    cmd_id: str = None
    behavior: ThrottleBehavior = None

    def __init__(
        self,
        cmd_type: CommandType,
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        self.cmd_type = cmd_type
        self.throttle_behavior = throttle_behavior
        self.cmd_id = cmd_id


class Command:
    def __init__(
        self,
        cmd_type: str,
        throttle_ms: int,
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        self.profile = CommandProfile(
            cmd_type, cmd_id or str(randint(0, 10000)), throttle_behavior
        )
        self.throttle_ms = throttle_ms

    @property
    def cmd_id(self):
        return self.profile.cmd_id

    @property
    def cmd_type(self):
        return self.profile.cmd_type

    @property
    def throttle_behavior(self):
        return self.profile.throttle_behavior

    def _send(self, tibia_wid):
        raise Exception("Needs to be implemented by subclass")

    def __str__(self):
        return (
            f"Command(cmd_type: {self.cmd_type}, "
            f"throttle_ms: {self.throttle_ms}, "
            f"cmd_id: {self.cmd_id}, "
            f"throttle_behavior: {self.throttle_behavior})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Command):
            return False

        return (
            other.cmd_id == self.cmd_id
            and other.cmd_type == self.cmd_type
            and self.throttle_behavior is other.throttle_behavior
            and self.throttle_ms == other.throttle_ms
        )

    def __hash__(self) -> int:
        return hash(
            tuple(self.cmd_id, self.cmd_type, self.throttle_behavior, self.throttle_ms)
        )


class KeeperHotkeyCommand(Command):
    """Hotkey command issued by one of Terminator's keepers."""

    def __init__(
        self,
        cmd_type: str,
        throttle_ms: int,
        hotkey: str,
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        super().__init__(cmd_type, throttle_ms, cmd_id, throttle_behavior)
        self.hotkey = hotkey

    def _send(self, tibia_wid):
        # TODO: Figure out how to send keys to a specific window (as opposed to the entire desktop)
        # ithout using xdotool; sending keys through xdotool is inefficient since it creates an
        # entire new process to do so.
        # TODO: We may need windows-specific implementations for this. See: pywinauto
        subprocess.Popen(
            ["/usr/bin/xdotool", "key", "--window", str(tibia_wid), self.hotkey]
        )

    def __str__(self):
        cmd_id = self.cmd_id or "N/A"
        return (
            f"[keystroke] {self.cmd_type} {cmd_id} ({self.throttle_ms}): {self.hotkey}"
        )


class MacroCommand(Command):
    def __init__(
        self,
        cmd_type: str,
        throttle_ms: int,
        macro_fn: Callable[[str], None],
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        super().__init__(cmd_type, throttle_ms, cmd_id, throttle_behavior)
        self.macro_fn = macro_fn

    def _send(self, tibia_wid):
        self.macro_fn(str(tibia_wid))

    def __str__(self):
        cmd_id = self.cmd_id or "N/A"
        return f"[macro] {self.cmd_type} {cmd_id} ({self.throttle_ms})"


class CommandSender(threading.Thread):
    NOOP_COMMAND = Command("noop", 0, "noop_id", ThrottleBehavior.FORCE)
    STOP_COMMAND = Command("stop", 0, "stop_id", ThrottleBehavior.FORCE)

    def __init__(self, tibia_wid, logger: StatsLogger, only_monitor: bool):
        super().__init__(daemon=True)
        self.tibia_wid = tibia_wid
        self.cmd_queue = queue.Queue()
        self.logger = logger
        self.only_monitor = only_monitor
        self.last_cmd_ts = 0
        self.prev_requeued_cmd: Command = CommandSender.NOOP_COMMAND
        self.retry_queue = deque()

    def send(self, command: Command):
        self.cmd_queue.put_nowait(command)

    def stop(self):
        self.cmd_queue.put_nowait(CommandSender.STOP_COMMAND)

    def __log_cmd(self, cmd: Command):
        self.logger.log_action(0, str(cmd))

    def __throttle(self, throttle_ms: int = 250) -> Tuple[bool, int]:
        """Throttles an action.
        Returns:

            bool: False if the action should be throttled (not executed),
                    True otherwise.
        """
        elapsed_ms = timestamp_ms() - self.last_cmd_ts
        return elapsed_ms >= throttle_ms

    def issue_cmd(self, command: Command) -> None:
        if not self.only_monitor:
            command._send(self.tibia_wid)
        self.last_cmd_ts = timestamp_ms()
        self.__log_cmd(command)

    def is_cmd_requeued(self, command: Command) -> bool:
        for retry_cmd in self.retry_queue:
            if retry_cmd.cmd_id == command.cmd_id:
                return True
        return False

    def requeue_back(self, command: Command) -> None:
        if (
            self.prev_requeued_cmd is command
            or self.prev_requeued_cmd.cmd_id == command.cmd_id
        ):
            return
        # Do not requeue if the queue is too large
        if self.cmd_queue.qsize() >= 10:
            return

        if self.cmd_queue.qsize() > 0:
            next_cmd: Command = self.cmd_queue.get_nowait()
            self.retry_queue.append(next_cmd)
            if next_cmd.cmd_id == command.cmd_id:
                return

        # Do *not* requeue more than one instance of a command
        if not self.is_cmd_requeued(command):
            self.cmd_queue.put_nowait(command)
            self.prev_requeued_cmd = command

    def requeue_front(self, command: Command) -> None:
        if (
            self.prev_requeued_cmd is command
            or self.prev_requeued_cmd.cmd_id == command.cmd_id
        ):
            return

        # No more than 10 commands in the retry queue
        if len(self.retry_queue) >= 10:
            return

        if not self.is_cmd_requeued(command):
            self.retry_queue.append(command)
            self.prev_requeued_cmd = command

    # TODO: Test this method individually with a unit test
    def fetch_next_cmd(self) -> Command:
        cmd: Command = CommandSender.NOOP_COMMAND
        if len(self.retry_queue) > 0:
            cmd: Command = self.retry_queue.pop()
        else:
            cmd: Command = self.cmd_queue.get()

        if self.__throttle(cmd.throttle_ms):
            # If an instance last requeued command succeeds to execute,
            # reset the previous requed command state.
            if cmd.cmd_id == self.prev_requeued_cmd.cmd_id:
                self.prev_requeued_cmd = CommandSender.NOOP_COMMAND
            return cmd
        else:
            if cmd.throttle_behavior == ThrottleBehavior.DROP:
                return CommandSender.NOOP_COMMAND
            elif cmd.throttle_behavior == ThrottleBehavior.FORCE:
                return cmd
            elif cmd.throttle_behavior == ThrottleBehavior.REQUEUE_BACK:
                self.requeue_back(cmd)
            elif cmd.throttle_behavior == ThrottleBehavior.REQUEUE_TOP:
                self.requeue_front(cmd)
        return CommandSender.NOOP_COMMAND

    def run(self):
        while True:
            cmd = self.fetch_next_cmd()
            if cmd is CommandSender.NOOP_COMMAND:
                continue
            elif cmd is CommandSender.STOP_COMMAND:
                break
            else:
                self.issue_cmd(cmd)


class CommandProcessor:
    def __init__(
        self,
        tibia_wid: str,
        logger: StatsLogger,
        only_monitor: bool,
        cmd_senders: Dict[str, CommandSender] = None,
    ):
        self.cmd_senders = cmd_senders or CommandProcessor.gen_cmd_senders(
            tibia_wid, logger, only_monitor
        )
        self.started = False
        self.stopped = False

    def start(self):
        if self.stopped:
            raise Exception(
                "This command processor has already been "
                "stopped. Create a new one and start it."
            )

        if not self.started:
            for sender in self.cmd_senders.values():
                sender.start()
            self.started = True

    def stop(self):
        if not self.started:
            raise Exception("This command processor has not been started yet.")

        if not self.stopped:
            for sender in self.cmd_senders.values():
                sender.stop()
            self.stopped = True

    def send(self, cmd: Command):
        self.cmd_senders[cmd.cmd_type].send(cmd)

    @staticmethod
    def gen_cmd_senders(
        tibia_wid: str, logger: StatsLogger, only_monitor: bool
    ) -> Dict[str, CommandSender]:
        cmd_senders = {}
        for cmd_type in CommandType.types():
            cmd_senders[cmd_type] = CommandSender(tibia_wid, logger, only_monitor)

        return cmd_senders


class ClientInterface:
    def __init__(
        self,
        hotkeys_config: HotkeysConfig,
        logger: StatsLogger = None,
        cmd_processor: CommandProcessor = None,
    ):
        self.hotkeys_config = hotkeys_config
        self.logger = logger
        self.cmd_processor = cmd_processor

    def send_keystroke_async(
        self,
        cmd_type: str,
        throttle_ms: int,
        hotkey: str,
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        self.cmd_processor.send(
            KeeperHotkeyCommand(
                cmd_type, throttle_ms, hotkey, cmd_id, throttle_behavior
            )
        )

    def cast_minor_heal(
        self,
        throttle_ms: int,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        self.logger.log_action(2, f"cast_minor_heal {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.HEAL_SPELL,
            throttle_ms,
            self.hotkeys_config.minor_heal,
            cmd_id="MINOR_HEAL",
            throttle_behavior=throttle_behavior,
        )

    def cast_medium_heal(
        self,
        throttle_ms: int,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        self.logger.log_action(2, f"cast_medium_heal {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.HEAL_SPELL,
            throttle_ms,
            self.hotkeys_config.medium_heal,
            cmd_id="MEDIUM_HEAL",
            throttle_behavior=throttle_behavior,
        )

    def cast_greater_heal(
        self,
        throttle_ms: int,
        # Requeue greater heal at the front, its important!
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.REQUEUE_TOP,
    ):
        self.logger.log_action(2, f"cast_greater_heal {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.HEAL_SPELL,
            throttle_ms,
            self.hotkeys_config.greater_heal,
            cmd_id="GREATER_HEAL",
            throttle_behavior=throttle_behavior,
        )

    def drink_mana(
        self,
        throttle_ms: int,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DROP,
    ):
        self.logger.log_action(2, f"drink_mana {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.USE_ITEM,
            throttle_ms,
            self.hotkeys_config.mana_potion,
            cmd_id="DRINK_MANA",
            throttle_behavior=throttle_behavior,
        )

    def cast_haste(
        self,
        throttle_ms: int,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DROP,
    ):
        self.logger.log_action(2, f"cast_haste {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.UTILITY_SPELL,
            throttle_ms,
            self.hotkeys_config.haste,
            cmd_id="HASTE",
            throttle_behavior=throttle_behavior,
        )

    def equip_ring(
        self,
        throttle_ms: int = 250,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DROP,
    ):
        self.logger.log_action(2, f"equip_ring {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.EQUIP_ITEM,
            throttle_ms,
            self.hotkeys_config.equip_ring,
            cmd_id="EQUIP_RING",
            throttle_behavior=throttle_behavior,
        )

    def toggle_emergency_ring(
        self,
        throttle_ms: int = 250,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DROP,
    ):
        self.logger.log_action(2, f"toggle_emergency_ring {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.EQUIP_ITEM,
            throttle_ms,
            self.hotkeys_config.toggle_emergency_ring,
            cmd_id="TOGGLE_EMERGENCY_RING",
            throttle_behavior=throttle_behavior,
        )

    def equip_amulet(
        self,
        throttle_ms: int = 250,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DROP,
    ):
        self.logger.log_action(2, f"equip_amulet {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.EQUIP_ITEM,
            throttle_ms,
            self.hotkeys_config.equip_amulet,
            cmd_id="EQUIP_AMULET",
            throttle_behavior=throttle_behavior,
        )

    def toggle_emergency_amulet(
        self,
        throttle_ms: int = 250,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DROP,
    ):
        self.logger.log_action(2, f"toggle_emergency_amulet {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.EQUIP_ITEM,
            throttle_ms,
            self.hotkeys_config.toggle_emergency_amulet,
            cmd_id="TOGGLE_EMERGENCY_AMULET",
            throttle_behavior=throttle_behavior,
        )

    def eat_food(
        self,
        throttle_ms: int = 250,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.REQUEUE_BACK,
    ):
        self.logger.log_action(2, f"eat_food {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.USE_ITEM,
            throttle_ms,
            self.hotkeys_config.eat_food,
            cmd_id="EAT_FOOD",
            throttle_behavior=throttle_behavior,
        )

    def cast_magic_shield(
        self,
        throttle_ms: int = 250,
        # Requeue magic shield at the top of the queue every time
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.REQUEUE_TOP,
    ):
        self.logger.log_action(2, f"cast_magic_shield {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.UTILITY_SPELL,
            throttle_ms,
            self.hotkeys_config.magic_shield,
            cmd_id="MAGIC_SHIELD",
            throttle_behavior=throttle_behavior,
        )

    def cancel_magic_shield(
        self,
        throttle_ms: int = 250,
        # It is important that the cancel magic shield happens, therefore we requeue,
        # but it should be put behind any other pending actions
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.REQUEUE_BACK,
    ):
        self.logger.log_action(2, f"cancel_magic_shield {throttle_ms} ms")
        self.send_keystroke_async(
            CommandType.UTILITY_SPELL,
            throttle_ms,
            self.hotkeys_config.cancel_magic_shield,
            cmd_id="CANCEL_MAGIC_SHIELD",
            throttle_behavior=throttle_behavior,
        )

    def execute_macro(
        self,
        macro_fn: Callable[[str], None],
        cmd_type: str,
        throttle_ms: int = 125,
        cmd_id: str = None,
        throttle_behavior: ThrottleBehavior = ThrottleBehavior.DEFAULT,
    ):
        self.logger.log_action(2, f"execute_macro {throttle_ms} ms")
        self.cmd_processor.send(
            MacroCommand(cmd_type, throttle_ms, macro_fn, cmd_id, throttle_behavior)
        )


class FakeLogger:
    def log_action(self, debug_level: int, msg: str):
        print(f"{debug_level}, {msg}")


class FakeCommandSender(CommandSender):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_keystroke(self, hotkey: str):
        print(f"_send_keystroke {hotkey}")


def main():
    hotkeys = {
        "minor_heal": "exura_key",
        "medium_heal": "exura_gran_key",
        "greater_heal": "exura_sio_key",
        "mana_potion": "mana_key",
        "haste": "haste_key",
        "equip_ring": "ring_key",
        "equip_amulet": "equip_amulet_key",
        "toggle_emergency_ring": "emergency_ring_key",
        "toggle_emergency_amulet": "emergency_amulet_key",
        "eat_food": "eat_key",
        "magic_shield": "shield_on_key",
        "cancel_magic_shield": "shield_off_key",
        "loot": "loot_key",
        "start_emergency": "start_emergency_key",
        "cancel_emergency": "cancel_emergency_key",
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
            ),
        },
    )
    client_interface = ClientInterface(
        HotkeysConfig(**hotkeys), fake_logger, cmd_processor
    )
    cmd_processor.start()
    method_names = [
        "cast_minor_heal",
        "cast_medium_heal",
        "cast_greater_heal",
        "drink_mana",
        "cast_haste",
        "equip_ring",
        "toggle_emergency_ring",
        "equip_amulet",
        "toggle_emergency_amulet",
        "eat_food",
        "cast_magic_shield",
        "cancel_magic_shield",
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
