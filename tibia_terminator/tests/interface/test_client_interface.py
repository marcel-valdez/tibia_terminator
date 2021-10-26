#!/usr/bin/env python3.8

import unittest

import tibia_terminator.interface.client_interface as sut

from tibia_terminator.interface.client_interface import (
    Command,
    ThrottleBehavior,
    CommandSender,
)
from unittest import TestCase
from typing import List


class FakeStatsLogger:
    def log_action(self, debug_level: int, msg: str) -> None:
        pass


class FakeCommand(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send(self, tibia_wid: str) -> None:
        pass


class TestClientInterface(TestCase):

    test_cmd_type: str
    default_test_cmd_id: str
    timestamps: List[int]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_cmd_type = "_test_cmd_type_"
        self.default_test_cmd_id = "_test_cmd_id_"
        self.timestamps = []

    def setUp(self) -> None:
        def next_timestamp():
            if len(self.timestamps) > 0:
                return self.timestamps.pop()
            else:
                return 0

        sut.timestamp_ms = next_timestamp

    def make_target(self):
        return CommandSender("_test_tibia_wid_", FakeStatsLogger(), False)

    def make_cmd(
        self,
        throttle_behavior: ThrottleBehavior,
        throttle_ms: int = 0,
        cmd_id: str = None,
    ) -> Command:
        return FakeCommand(
            cmd_type=self.test_cmd_type,
            throttle_ms=throttle_ms,
            cmd_id=cmd_id or self.default_test_cmd_id,
            throttle_behavior=throttle_behavior,
        )

    def test_fetch_next_cmd_forced_throttle(self) -> None:
        # given that a single forced command is given
        input_cmd = self.make_cmd(ThrottleBehavior.FORCE)
        # when the next command is fetched
        # then the forced command is issued
        self.check_fetch_next_cmd([input_cmd], input_cmd, [0, 1])

    def test_fetch_next_cmd_forced_throttle_1000ms(self) -> None:
        # given that a single forced command is given
        input_cmd_1 = self.make_cmd(ThrottleBehavior.FORCE)
        input_cmd_2 = self.make_cmd(ThrottleBehavior.FORCE)
        # when the next command is fetched
        # then the forced command is issued
        self.check_fetch_next_cmd([input_cmd_1, input_cmd_2], input_cmd_2, [0, 1, 2, 3])

    def test_fetch_next_cmd_forced_throttle_1000ms_drop_first(self) -> None:
        drop_cmd = self.make_cmd(ThrottleBehavior.DROP)
        foced_cmd = self.make_cmd(ThrottleBehavior.FORCE)
        self.check_fetch_next_cmd(
            # given that a dropped and forced commands are sent
            [drop_cmd, foced_cmd],
            # when the forced command is fetched
            # then the forced command is issued
            foced_cmd,
            [0, 1, 2],
        )

    def test_fetch_next_cmd_drop_behavior(self) -> None:
        drop_cmd = self.make_cmd(ThrottleBehavior.DROP)
        self.check_fetch_next_cmd([drop_cmd], drop_cmd, [0, 1])

    def test_fetch_next_cmd_drop_behavior_throttled(self) -> None:
        drop_cmd_1 = self.make_cmd(ThrottleBehavior.DROP)
        drop_cmd_2 = self.make_cmd(ThrottleBehavior.DROP, throttle_ms=10)
        self.check_fetch_next_cmd(
            [drop_cmd_1, drop_cmd_2], CommandSender.NOOP_COMMAND, [0, 1, 2]
        )

    def test_fetch_next_cmd_drop_behavior_throttled_with_third_cmd(self) -> None:
        drop_cmd_1 = self.make_cmd(ThrottleBehavior.DROP)
        drop_cmd_2 = self.make_cmd(ThrottleBehavior.DROP, throttle_ms=10)
        drop_cmd_3 = self.make_cmd(ThrottleBehavior.DROP, throttle_ms=1)
        self.check_fetch_next_cmd(
            [drop_cmd_1, drop_cmd_2, drop_cmd_3], drop_cmd_3, [0, 1, 2, 3]
        )

    def test_fetch_next_cmd_requeued_top(self) -> None:
        requeue_top_cmd = self.make_cmd(ThrottleBehavior.REQUEUE_TOP)
        self.check_fetch_next_cmd([requeue_top_cmd], requeue_top_cmd, [0, 1])

    def test_fetch_next_cmd_requeued_top_throttled_once(self) -> None:
        requeue_top_cmd_1 = self.make_cmd(ThrottleBehavior.REQUEUE_TOP)
        requeue_top_cmd_2 = self.make_cmd(ThrottleBehavior.REQUEUE_TOP, throttle_ms=10)
        self.check_fetch_next_cmd(
            [requeue_top_cmd_1, requeue_top_cmd_2],
            CommandSender.NOOP_COMMAND,
            [0, 1, 2],
        )

    def test_fetch_next_cmd_requeued_top_not_throttled_twice(self) -> None:
        requeue_top_cmd_1 = self.make_cmd(ThrottleBehavior.REQUEUE_TOP)
        requeue_top_cmd_2 = self.make_cmd(ThrottleBehavior.REQUEUE_TOP, throttle_ms=10)
        self.check_fetch_next_cmd(
            [requeue_top_cmd_1, requeue_top_cmd_2], requeue_top_cmd_2, [0, 1, 20]
        )

    def test_fetch_next_cmd_requeued_top_throttled_then_requeued(self) -> None:
        requeue_top_cmd_1 = self.make_cmd(ThrottleBehavior.REQUEUE_TOP)
        requeue_top_cmd_2 = self.make_cmd(ThrottleBehavior.REQUEUE_TOP, throttle_ms=10)
        other_cmd_3 = self.make_cmd(
            ThrottleBehavior.DROP, throttle_ms=10, cmd_id="other_cmd"
        )
        self.check_fetch_next_cmd(
            [requeue_top_cmd_1, requeue_top_cmd_2, other_cmd_3],
            requeue_top_cmd_2,
            [1, 2, 3, 13],
        )

    def test_fetch_next_cmd_requeued_back(self) -> None:
        requeue_back_cmd = self.make_cmd(ThrottleBehavior.REQUEUE_BACK)
        self.check_fetch_next_cmd([requeue_back_cmd], requeue_back_cmd, [0, 1])

    def test_fetch_next_cmd_requeued_back_throttled_once(self) -> None:
        requeue_back_cmd_1 = self.make_cmd(ThrottleBehavior.REQUEUE_BACK)
        requeue_back_cmd_2 = self.make_cmd(ThrottleBehavior.REQUEUE_BACK, throttle_ms=10)
        self.check_fetch_next_cmd(
            [requeue_back_cmd_1, requeue_back_cmd_2],
            CommandSender.NOOP_COMMAND,
            [0, 1, 2],
        )

    def test_fetch_next_cmd_requeued_back_not_throttled_twice(self) -> None:
        requeue_back_cmd_1 = self.make_cmd(ThrottleBehavior.REQUEUE_BACK)
        requeue_back_cmd_2 = self.make_cmd(ThrottleBehavior.REQUEUE_BACK, throttle_ms=10)
        self.check_fetch_next_cmd(
            [requeue_back_cmd_1, requeue_back_cmd_2], requeue_back_cmd_2, [0, 1, 20]
        )

    def test_fetch_next_cmd_requeued_back_throttled_then_requeued_back(self) -> None:
        requeue_back_cmd_1 = self.make_cmd(ThrottleBehavior.REQUEUE_BACK)
        requeue_back_cmd_2 = self.make_cmd(ThrottleBehavior.REQUEUE_BACK, throttle_ms=10)
        other_cmd_3 = self.make_cmd(
            ThrottleBehavior.DROP, throttle_ms=1, cmd_id="other_cmd"
        )
        self.check_fetch_next_cmd(
            [requeue_back_cmd_1, requeue_back_cmd_2, other_cmd_3, None],
            requeue_back_cmd_2,
            [1, 2, 3, 13, 24, 34],
        )

    def check_fetch_next_cmd(
        self,
        cmds_to_send: List[Command],
        expected_final_cmd: Command = CommandSender.NOOP_COMMAND,
        timestamps: List[int] = None,
    ) -> None:
        # given
        if timestamps:
            self.timestamps = list(reversed(timestamps))
        target = self.make_target()
        # given that commands were sent instantaneously
        for cmd in cmds_to_send:
            if cmd is not None:
                target.send(cmd)
        # given that n - 1 commands are fetched
        for i in range(len(cmds_to_send) - 1):
            next_cmd = target.fetch_next_cmd()
            if not next_cmd is CommandSender.NOOP_COMMAND:
                # Make it so that the command is issued exactly
                # when it is fetched
                target.issue_cmd(next_cmd)
        # when the final command is fetched
        actual_cmd = target.fetch_next_cmd()
        # then we expect a specific command at the end
        self.assertEqual(
            actual_cmd,
            expected_final_cmd,
            (f"actual_cmd: {actual_cmd}\n, " f"expected_cmd: {expected_final_cmd}"),
        )


if __name__ == "__main__":
    unittest.main()
