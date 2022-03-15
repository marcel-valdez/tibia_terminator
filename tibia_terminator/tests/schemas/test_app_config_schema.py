#!/usr/bin/env python3.8

import unittest
from unittest import TestCase
from tibia_terminator.schemas.app_config_schema import (AppConfigsSchema,
                                                        AppConfig, AppConfigs)


class TestAppCofigSchema(TestCase):
    def test_cleans_memory_address(self):
        # given
        data = {
            "default_pid":
            456,
            "configs": [{
                "pid": 123,
                "mana_memory_address": "0x1231",
                "speed_memory_address": "0x12312",
                "soul_points_memory_address": "0x123123",
                "hp_memory_address": "0x1231231",
                "magic_shield_memory_address": "0xabcdef",
                "max_mana_address": "0x0123456789abcdef",
                "max_hp_address": "0x0"
            }]
        }
        target = AppConfigsSchema()
        # when
        app_configs = target.load(data)
        # then
        self.assertIsInstance(app_configs.configs[0], AppConfig)
        self.assertEqual(app_configs.configs[0].pid, data["configs"][0]["pid"])
        self.assertEqual(app_configs.configs[0].mana_memory_address,
                         data["configs"][0]["mana_memory_address"][2:])
        self.assertEqual(app_configs.configs[0].speed_memory_address,
                         data["configs"][0]["speed_memory_address"][2:])
        self.assertEqual(app_configs.configs[0].soul_points_memory_address,
                         data["configs"][0]["soul_points_memory_address"][2:])
        self.assertEqual(app_configs.configs[0].hp_memory_address,
                         data["configs"][0]["hp_memory_address"][2:])
        self.assertEqual(app_configs.configs[0].magic_shield_memory_address,
                         data["configs"][0]["magic_shield_memory_address"][2:])
        self.assertEqual(app_configs.configs[0].max_mana_address,
                         data["configs"][0]["max_mana_address"][2:])
        self.assertEqual(app_configs.configs[0].max_hp_address,
                         data["configs"][0]["max_hp_address"][2:])

    def test_loads_minimal(self):
        # given
        data = {"default_pid": 456, "configs": [{"pid": 123}, {"pid": 456}]}
        target = AppConfigsSchema()
        # when
        app_configs = target.load(data)
        # then
        self.assertIsInstance(app_configs, AppConfigs)
        self.assertEqual(len(app_configs.configs), 2)
        for i in range(2):
            self.assertIsInstance(app_configs.configs[i], AppConfig)
            self.assertEqual(app_configs.configs[i].pid,
                             data["configs"][i]["pid"])

    def test_loads_maximal(self):
        # given
        data = {
            "default_pid":
            456,
            "configs": [{
                "pid": 123,
                "mana_memory_address": "1231",
                "speed_memory_address": "12312",
                "soul_points_memory_address": "123123",
                "hp_memory_address": "1231231",
                "magic_shield_memory_address": "12312312",
                "max_mana_address": "123123123",
                "max_hp_address": "1231231231"
            }, {
                "pid": 456,
                "mana_memory_address": "4564",
                "speed_memory_address": "45645",
                "soul_points_memory_address": "456456",
                "hp_memory_address": "4564564",
                "magic_shield_memory_address": "45645645",
                "max_mana_address": "456456456",
                "max_hp_address": "4564564564"
            }]
        }
        target = AppConfigsSchema()
        # when
        app_configs = target.load(data)
        # then
        self.assertIsInstance(app_configs, AppConfigs)
        self.assertEqual(len(app_configs.configs), 2)
        for i in range(2):
            self.assertIsInstance(app_configs.configs[i], AppConfig)
            self.assertEqual(app_configs.configs[i].pid,
                             data["configs"][i]["pid"])
            self.assertEqual(app_configs.configs[i].mana_memory_address,
                             data["configs"][i]["mana_memory_address"])
            self.assertEqual(app_configs.configs[i].speed_memory_address,
                             data["configs"][i]["speed_memory_address"])
            self.assertEqual(app_configs.configs[i].soul_points_memory_address,
                             data["configs"][i]["soul_points_memory_address"])
            self.assertEqual(app_configs.configs[i].hp_memory_address,
                             data["configs"][i]["hp_memory_address"])
            self.assertEqual(
                app_configs.configs[i].magic_shield_memory_address,
                data["configs"][i]["magic_shield_memory_address"])
            self.assertEqual(app_configs.configs[i].max_mana_address,
                             data["configs"][i]["max_mana_address"])
            self.assertEqual(app_configs.configs[i].max_hp_address,
                             data["configs"][i]["max_hp_address"])

    def test_get_by_pid(self):
        # given
        data = {"default_pid": 456, "configs": [{"pid": 123}, {"pid": 456}]}
        target = AppConfigsSchema()
        app_configs = target.load(data)
        # when
        for data_config in data["configs"]:
            actual = app_configs[data_config["pid"]]
            # then
            self.assertEqual(actual.pid, data_config["pid"])


if __name__ == '__main__':
    unittest.main()
