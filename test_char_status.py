#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from char_status import CharStatusAsync, immediate


class TestCharStatusAsync(TestCase):
    def test_gets_values(self):
        # given
        stats = immediate({'mana': 1, 'speed': 2, 'hp': 3, 'magic_shield': 4})
        equipment = immediate({
            'emergency_action_amulet': 'a',
            'emergency_action_ring': 'b',
            'equipped_amulet': 'c',
            'equipped_ring': 'd',
            'magic_shield_status': 'e',
        })
        # when
        target = CharStatusAsync(stats, equipment)
        # then
        self.assertEqual(target.mana, 1)
        self.assertEqual(target.speed, 2)
        self.assertEqual(target.hp, 3)
        self.assertEqual(target.magic_shield_level, 4)
        self.assertEqual(target.emergency_action_amulet, 'a')
        self.assertEqual(target.emergency_action_ring, 'b')
        self.assertEqual(target.equipped_amulet, 'c')
        self.assertEqual(target.equipped_ring, 'd')
        self.assertEqual(target.magic_shield_status, 'e')


if __name__ == '__main__':
    unittest.main()
