"""Keeps the character healthy in every way."""

from typing import List, Dict

from common.char_status import CharStatus
from interface.macro.cancel_emergency_macro import CancelEmergencyMacro
from interface.macro.item_crosshair_macro import ItemCrosshairMacro
from interface.macro.macro import Macro
from interface.macro.start_emergency_macro import StartEmergencyMacro
from keeper.emergency_magic_shield_keeper import (EmergencyMagicShieldKeeper,
                                                  MagicShieldStatus)
from keeper.emergency_reporter import EmergencyReporter
from keeper.equipment_keeper import EquipmentKeeper
from keeper.hp_keeper import HpKeeper
from keeper.magic_shield_keeper import MagicShieldKeeper
from keeper.mana_keeper import ManaKeeper
from keeper.speed_keeper import SpeedKeeper


class CharKeeper:
    def __init__(self,
                 client,
                 char_configs,
                 hotkeys: Dict[str, str],
                 emergency_reporter=None,
                 mana_keeper=None,
                 hp_keeper=None,
                 speed_keeper=None,
                 equipment_keeper=None,
                 magic_shield_keeper=None,
                 item_crosshair_macros=None,
                 core_macros=None):
        self.item_crosshair_macros = []
        self.core_macros = []
        self.client = client
        self.char_configs = char_configs
        self.hotkeys = hotkeys
        # load the first one by default
        char_config = char_configs[0]["config"]
        self.init_emergency_reporter(char_config, emergency_reporter)
        self.init_mana_keeper(client, char_config, mana_keeper)
        self.init_hp_keeper(client, char_config, hp_keeper)
        self.init_speed_keeper(client, char_config, speed_keeper)
        self.init_equipment_keeper(client, char_config, equipment_keeper)
        self.init_magic_shield_keeper(client, char_config, magic_shield_keeper)
        self.init_item_crosshair_macros(
            char_config.get('item_crosshair_macros', []),
            item_crosshair_macros)
        self.init_core_macros(self.hotkeys, core_macros)

    def change_char_config(self, index):
        self.load_char_config(self.char_configs[index]["config"])

    def load_char_config(self, char_config):
        self.init_emergency_reporter(char_config)
        self.init_mana_keeper(self.client, char_config)
        self.init_hp_keeper(self.client, char_config)
        self.init_speed_keeper(self.client, char_config)
        self.init_equipment_keeper(self.client, char_config)
        self.init_magic_shield_keeper(self.client, char_config)
        self.init_item_crosshair_macros(
            char_config.get('item_crosshair_macros', []))
        self.init_core_macros(self.hotkeys)

    def init_emergency_reporter(self, char_config, emergency_reporter=None):
        if emergency_reporter is None:
            self.emergency_reporter = EmergencyReporter(
                char_config['total_hp'], char_config['mana_lo'],
                char_config['emergency_shield_hp_treshold'])
        else:
            self.emergency_reporter = emergency_reporter

    def init_mana_keeper(self, client, char_config, mana_keeper=None):
        if mana_keeper is None:
            self.mana_keeper = ManaKeeper(client, char_config['mana_hi'],
                                          char_config['mana_lo'],
                                          char_config['critical_mana'],
                                          char_config['downtime_mana'],
                                          char_config['total_mana'])
        else:
            self.mana_keeper = mana_keeper

    def init_hp_keeper(self, client, char_config, hp_keeper=None):
        if hp_keeper is None:
            self.hp_keeper = HpKeeper(client, self.emergency_reporter,
                                      char_config['total_hp'],
                                      char_config['heal_at_missing'],
                                      char_config['exura_heal'],
                                      char_config['exura_gran_heal'],
                                      char_config['downtime_heal_at_missing'])
        else:
            self.hp_keeper = hp_keeper

    def init_speed_keeper(self, client, char_config, speed_keeper=None):
        if speed_keeper is None:
            self.speed_keeper = SpeedKeeper(client, char_config['base_speed'],
                                            char_config['hasted_speed'])
        else:
            self.speed_keeper = speed_keeper

    def init_equipment_keeper(self,
                              client,
                              char_config,
                              equipment_keeper=None):
        if equipment_keeper is None:
            self.equipment_keeper = EquipmentKeeper(
                client, self.emergency_reporter,
                char_config['should_equip_amulet'],
                char_config['should_equip_ring'],
                char_config['should_eat_food'],
                char_config.get('equip_amulet_secs', 1),
                char_config.get('equip_ring_secs', 1))
        else:
            self.equipment_keeper = equipment_keeper

    def init_magic_shield_keeper(self,
                                 client,
                                 char_config,
                                 magic_shield_keeper=None):
        magic_shield_type = char_config.get('magic_shield_type', None)
        if magic_shield_keeper is not None:
            self.magic_shield_keeper = magic_shield_keeper

        if magic_shield_type == "permanent":
            self.magic_shield_keeper = MagicShieldKeeper(
                client, char_config['total_hp'],
                char_config['magic_shield_treshold'])
        elif magic_shield_type == "emergency":
            self.magic_shield_keeper = EmergencyMagicShieldKeeper(
                client, self.emergency_reporter, char_config['total_hp'],
                char_config['mana_lo'], char_config['magic_shield_treshold'])
        elif magic_shield_type is None:
            self.magic_shield_keeper = NoopKeeper()
        elif magic_shield_type is not None:
            raise Exception(f"Unknown magic shield type {magic_shield_type}")

    def init_item_crosshair_macros(self,
                                   macro_configs: List[Dict[str, str]],
                                   item_crosshair_macros: List[Macro] = None):
        self.unload_item_crosshair_macros()
        if item_crosshair_macros is not None:
            self.item_crosshair_macros = item_crosshair_macros
        else:
            for macro_config in macro_configs:
                self.item_crosshair_macros.append(
                    ItemCrosshairMacro(self.client, macro_config['hotkey']))

    def unload_item_crosshair_macros(self):
        self.__unhook_macros(self.item_crosshair_macros)
        self.item_crosshair_macros = []

    def init_core_macros(self,
                         hotkeys_configs: Dict[str, str],
                         core_macros: List[Macro] = None):
        self.unload_core_macros()
        if core_macros is not None:
            self.core_macros = core_macros
        else:
            cancel_emergency_key = hotkeys_configs.get('cancel_emergency')
            if cancel_emergency_key is not None:
                self.core_macros.append(
                    CancelEmergencyMacro(self.emergency_reporter,
                                         cancel_emergency_key))

            start_emergency_key = hotkeys_configs.get('start_emergency')
            if start_emergency_key is not None:
                self.core_macros.append(
                    StartEmergencyMacro(self.emergency_reporter,
                                        start_emergency_key))

    def unload_core_macros(self):
        self.__unhook_macros(self.core_macros)
        self.core_macros = []

    def unhook_macros(self):
        self.__unhook_macros(self.item_crosshair_macros)
        self.__unhook_macros(self.core_macros)

    def __unhook_macros(self, macros: List[Macro] = None):
        for macro in (macros or []):
            macro.unhook_hotkey()

    def hook_macros(self):
        self.__hook_macros(self.item_crosshair_macros)
        self.__hook_macros(self.core_macros)

    def __hook_macros(self, macros: List[Macro] = None):
        for macro in (macros or []):
            macro.hook_hotkey()

    def handle_char_status(self, char_status: CharStatus):
        # First set the emergency status, so all sub-keepers can change their
        # their behaviours accordingly.
        self.handle_emergency_status_change(char_status)

        # Note that we have to handle stats changes always, even if they
        # haven't actually changed, because a command to heal or drink mana
        # or haste could be ignored if the character is exhausted, therefore
        # we have to spam the action until the effect takes place.
        self.handle_hp_change(char_status)
        self.handle_mana_change(char_status)
        self.handle_equipment(char_status)
        self.handle_speed_change(char_status)

    def handle_emergency_status_change(self, char_status: CharStatus):
        if self.emergency_reporter.in_emergency:
            if self.emergency_reporter.should_stop_emergency(char_status):
                self.emergency_reporter.stop_emergency()
        elif self.emergency_reporter.is_emergency(char_status):
            self.emergency_reporter.start_emergency()

    def handle_hp_change(self, char_status: CharStatus):
        is_downtime = self.speed_keeper.is_hasted(char_status.speed) and \
            self.mana_keeper.is_healthy_mana(char_status.mana)

        self.hp_keeper.handle_status_change(char_status, is_downtime)

    def handle_mana_change(self, char_status: CharStatus):
        if self.should_skip_drinking_mana(char_status):
            return False

        is_downtime = self.hp_keeper.is_healthy_hp(char_status.hp) and \
            self.speed_keeper.is_hasted(char_status.speed)
        self.mana_keeper.handle_status_change(char_status, is_downtime)

    def should_skip_drinking_mana(self, char_status: CharStatus):
        # Do not issue order to use mana potion if we're at critical HP levels,
        # unless we're at critical mana levels in order to avoid delaying
        # heals.
        if self.hp_keeper.is_critical_hp(char_status.hp) and \
           not self.mana_keeper.is_critical_mana(char_status.mana):
            return True

        # Do not issue order to use mana potion if we are paralyzed unless
        # we're at critical mana levels, in order to avoid delaying haste.
        if self.speed_keeper.is_paralized(char_status.speed) and \
           not self.mana_keeper.is_critical_mana(char_status.mana):
            return True

        return False

    def handle_speed_change(self, char_status: CharStatus):
        if self.should_skip_haste(char_status):
            return False
        self.speed_keeper.handle_status_change(char_status)

    def should_skip_haste(self, char_status: CharStatus):
        # Do not issue order to haste if we're at critical HP levels.
        if self.hp_keeper.is_critical_hp(char_status.hp):
            return True

        # Do not issue a haste order if we're not paralyzed and we're at
        # critical mana levels.
        if self.mana_keeper.is_critical_mana(char_status.mana) and \
           not self.speed_keeper.is_paralized(char_status.speed):
            return True

        # Do not issue haste, if we should be casting magic shield next, since
        # haste and magic shield share cooldowns.
        if (char_status.magic_shield_status == MagicShieldStatus.OFF_COOLDOWN
                and self.magic_shield_keeper.should_cast(char_status)):
            return True

        return False

    def handle_equipment(self, char_status: CharStatus):
        self.magic_shield_keeper.handle_status_change(char_status)
        self.equipment_keeper.handle_status_change(char_status)


class NoopKeeper:
    def handle_status_change(self, char_status: CharStatus):
        pass

    def should_cast(self, char_status: CharStatus):
        return False
