#!/usr/bin/env python3.8

import color_spec
import unittest

from unittest import TestCase
from unittest.mock import Mock


class TestColorSpec(TestCase):

    def test_can_get_equipped_amulet_by_spec(self):
        # given
        eq_spec = color_spec.SSA.eq_color_specs[0]
        # when
        name = color_spec.AMULET_REPOSITORY.get_equipment_name(eq_spec)
        # then
        self.assertEqual(color_spec.SSA.name, name)

    def test_can_get_equipped_ring_by_spec(self):
        # given
        eq_spec = color_spec.MIGHT.eq_color_specs[0]
        # when
        name = color_spec.RING_REPOSITORY.get_equipment_name(eq_spec)
        # then
        self.assertEqual(color_spec.MIGHT.name, name)

    def test_can_get_action_amulet_by_spec(self):
        # given
        action_spec = color_spec.SSA.action_color_specs[0]
        # when
        name = color_spec.AMULET_REPOSITORY.get_action_name(action_spec)
        # then
        self.assertEqual(color_spec.SSA.name, name)

    def test_can_get_action_ring_by_spec(self):
        # given
        action_spec = color_spec.MIGHT.action_color_specs[0]
        # when
        name = color_spec.RING_REPOSITORY.get_action_name(action_spec)
        # then
        self.assertEqual(color_spec.MIGHT.name, name)

    def test_can_get_unknown_equipped_amulet_by_spec(self):
        # given
        eq_spec = color_spec.spec("1", "1", "1", "1")
        # when
        name = color_spec.AMULET_REPOSITORY.get_equipment_name(eq_spec)
        # then
        self.assertEqual(color_spec.AmuletName.UNKNOWN, name)

    def test_can_get_unknown_equipped_ring_by_spec(self):
        # given
        eq_spec = color_spec.spec("1", "1", "1", "1")
        # when
        name = color_spec.RING_REPOSITORY.get_equipment_name(eq_spec)
        # then
        self.assertEqual(color_spec.AmuletName.UNKNOWN, name)

    def test_can_get_unknown_action_amulet_by_spec(self):
        # given
        action_spec = color_spec.spec("1", "1", "1", "1")
        # when
        name = color_spec.AMULET_REPOSITORY.get_action_name(action_spec)
        # then
        self.assertEqual(color_spec.AmuletName.UNKNOWN, name)

    def test_can_get_unknown_action_ring_by_spec(self):
        # given
        action_spec = color_spec.spec("1", "1", "1", "1")
        # when
        name = color_spec.RING_REPOSITORY.get_action_name(action_spec)
        # then
        self.assertEqual(color_spec.RingName.UNKNOWN, name)


if __name__ == '__main__':
    unittest.main()
