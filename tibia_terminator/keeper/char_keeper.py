"""Keeps the character healthy in every way."""

from typing import List, Dict, Optional, Union

from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.schemas.hotkeys_config_schema import HotkeysConfig
from tibia_terminator.schemas.char_config_schema import CharConfig, BattleConfig
from tibia_terminator.schemas.directional_macro_config_schema import DirectionalMacroConfig
from tibia_terminator.schemas.item_crosshair_macro_config_schema import ItemCrosshairMacroConfig
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.interface.macro.cancel_emergency_macro import (
    CancelEmergencyMacro, CancelTankModeMacro
)
from tibia_terminator.interface.macro.item_crosshair_macro import ItemCrosshairMacro
from tibia_terminator.interface.macro.directional_macro import DirectionalMacro
from tibia_terminator.interface.macro.macro import Macro
from tibia_terminator.interface.macro.start_emergency_macro import (
    StartEmergencyMacro, StartTankModeMacro
)
from tibia_terminator.reader.equipment_reader import MagicShieldStatus
from tibia_terminator.keeper.emergency_reporter import (
    EmergencyReporter,
    TankModeReporter,
)
from tibia_terminator.keeper.equipment_keeper import EquipmentKeeper
from tibia_terminator.keeper.hp_keeper import HpKeeper
from tibia_terminator.keeper.emergency_magic_shield_keeper import (
    EmergencyMagicShieldKeeper,
)
from tibia_terminator.keeper.magic_shield_keeper import MagicShieldKeeper
from tibia_terminator.keeper.protector_keeper import (
    ProtectorKeeper,
    EmergencyProtectorKeeper,
)
from tibia_terminator.keeper.mana_keeper import ManaKeeper
from tibia_terminator.keeper.knight_potion_keeper import KnightPotionKeeper
from tibia_terminator.keeper.speed_keeper import SpeedKeeper


class CharKeeper:
    def __init__(
        self,
        client: ClientInterface,
        char_config: CharConfig,
        battle_config: BattleConfig,
        hotkeys_config: HotkeysConfig,
        emergency_reporter: Optional[EmergencyReporter] = None,
        tank_mode_reporter: Optional[TankModeReporter] = None,
        mana_keeper: Optional[Union[ManaKeeper, KnightPotionKeeper]] = None,
        hp_keeper: Optional[HpKeeper] = None,
        speed_keeper: Optional[SpeedKeeper] = None,
        equipment_keeper: Optional[EquipmentKeeper] = None,
        magic_shield_keeper: Optional[Union[MagicShieldKeeper, ProtectorKeeper]] = None,
        item_crosshair_macros: Optional[List[ItemCrosshairMacro]] = None,
        core_macros: Optional[List[Macro]] = None,
    ):
        self.item_crosshair_macros: List[ItemCrosshairMacro] = []
        self.directional_macros: List[DirectionalMacro] = []
        self.core_macros: List[Macro] = []
        self.client = client
        self.hotkeys_config = hotkeys_config
        # load the first battle config from the first char config
        self.init_emergency_reporter(char_config, battle_config, emergency_reporter)
        self.init_tank_mode_reporter(tank_mode_reporter)
        self.init_mana_keeper(client, char_config, battle_config, mana_keeper)
        self.init_hp_keeper(client, char_config, battle_config, hp_keeper)
        self.init_speed_keeper(client, char_config, battle_config, speed_keeper)
        self.init_equipment_keeper(client, battle_config, equipment_keeper)
        self.init_magic_shield_keeper(
            client, char_config, battle_config, magic_shield_keeper
        )
        self.init_item_crosshair_macros(
            battle_config.item_crosshair_macros or [],
            self.hotkeys_config,
            item_crosshair_macros,
        )
        self.init_core_macros(self.hotkeys_config, core_macros)
        self.init_directional_macros(battle_config.directional_macros or [])

    def load_char_config(self, char_config: CharConfig, battle_config: BattleConfig):
        self.init_emergency_reporter(char_config, battle_config)
        self.init_mana_keeper(self.client, char_config, battle_config)
        self.init_hp_keeper(self.client, char_config, battle_config)
        self.init_speed_keeper(self.client, char_config, battle_config)
        self.init_equipment_keeper(self.client, battle_config)
        self.init_magic_shield_keeper(self.client, char_config, battle_config)
        self.init_item_crosshair_macros(
            battle_config.item_crosshair_macros or [], self.hotkeys_config
        )
        self.init_core_macros(self.hotkeys_config)
        self.init_directional_macros(battle_config.directional_macros or [])

    def init_emergency_reporter(
        self,
        char_config: CharConfig,
        battle_config: BattleConfig,
        emergency_reporter: Optional[EmergencyReporter] = None,
    ):
        if emergency_reporter is None:
            self.emergency_reporter = EmergencyReporter(
                char_config.total_hp,
                battle_config.mana_lo,
                battle_config.emergency_hp_threshold,
            )
        else:
            self.emergency_reporter = emergency_reporter

    def init_tank_mode_reporter(
        self,
        tank_mode_reporter: Optional[TankModeReporter] = None,
    ):
        if tank_mode_reporter is None:
            self.tank_mode_reporter = TankModeReporter()
        else:
            self.tank_mode_reporter = tank_mode_reporter

    def init_mana_keeper(
        self,
        client,
        char_config: CharConfig,
        battle_config: BattleConfig,
        mana_keeper: Optional[Union[ManaKeeper, KnightPotionKeeper]] = None,
    ):
        self.mana_keeper: Union[
            ManaKeeper, KnightPotionKeeper
        ] = None  # type: ignore
        if mana_keeper is None:
            if char_config.vocation == "mage" or not char_config.vocation:
                self.mana_keeper = ManaKeeper(
                    client,
                    battle_config.mana_hi,
                    battle_config.mana_lo,
                    battle_config.critical_mana,
                    battle_config.downtime_mana,
                    char_config.total_mana,
                )
            elif char_config.vocation == "knight":
                self.mana_keeper = KnightPotionKeeper(
                    client=client,
                    battle_config=battle_config,
                    total_hp=char_config.total_hp
                )
            else:
                raise Exception(f"Unsupported vocation: {char_config.vocation}")
        else:
            self.mana_keeper = mana_keeper

    def init_hp_keeper(
        self,
        client,
        char_config: CharConfig,
        battle_config: BattleConfig,
        hp_keeper: Optional[HpKeeper] = None,
    ):
        if hp_keeper is None:
            self.hp_keeper = HpKeeper(
                client,
                self.emergency_reporter,
                char_config.total_hp,
                battle_config.heal_at_missing,
                battle_config.minor_heal,
                battle_config.medium_heal,
                battle_config.greater_heal,
                battle_config.downtime_heal_at_missing,
                battle_config.emergency_hp_threshold,
            )
        else:
            self.hp_keeper = hp_keeper

    def init_speed_keeper(
        self,
        client,
        char_config: CharConfig,
        battle_config: BattleConfig,
        speed_keeper: Optional[SpeedKeeper] = None,
    ):
        if speed_keeper is None:
            self.speed_keeper = SpeedKeeper(
                client, char_config.base_speed, battle_config.hasted_speed
            )
        else:
            self.speed_keeper = speed_keeper

    def init_equipment_keeper(
        self,
        client,
        battle_config: BattleConfig,
        equipment_keeper: Optional[EquipmentKeeper] = None,
    ):
        if equipment_keeper is None:
            self.equipment_keeper = EquipmentKeeper(
                client,
                self.emergency_reporter,
                self.tank_mode_reporter,
                battle_config.should_equip_amulet,
                battle_config.should_equip_ring,
                battle_config.should_eat_food,
                battle_config.equip_amulet_secs,
                battle_config.equip_ring_secs,
            )
        else:
            self.equipment_keeper = equipment_keeper

    def init_magic_shield_keeper(
        self,
        client,
        char_config: CharConfig,
        battle_config: BattleConfig,
        magic_shield_keeper: Union[MagicShieldKeeper, ProtectorKeeper] = None,
    ):
        self.magic_shield_keeper: Union[
            MagicShieldKeeper, ProtectorKeeper, NoopKeeper
        ] = None  # type: ignore
        magic_shield_type = battle_config.magic_shield_type
        if magic_shield_keeper is not None:
            self.magic_shield_keeper = magic_shield_keeper

        if magic_shield_type == "permanent":
            if char_config.vocation is None or char_config.vocation == "mage":
                self.magic_shield_keeper = MagicShieldKeeper(
                    client, char_config.total_hp, battle_config.magic_shield_threshold
                )
            elif char_config.vocation == "knight":
                self.magic_shield_keeper = ProtectorKeeper(client)
            else:
                raise Exception(f"Unsupported vocation: {char_config.vocation}")
        elif magic_shield_type == "emergency":
            if char_config.vocation is None or char_config.vocation == "mage":
                self.magic_shield_keeper = EmergencyMagicShieldKeeper(
                    client,
                    self.emergency_reporter,
                    self.tank_mode_reporter,
                    char_config.total_hp,
                    battle_config.magic_shield_threshold or 0,
                )
            elif char_config.vocation == "knight":
                self.magic_shield_keeper = EmergencyProtectorKeeper(
                    client, self.emergency_reporter, self.tank_mode_reporter
                )
            else:
                raise Exception(f"Unsupported vocation: {char_config.vocation}")
        elif magic_shield_type:
            raise Exception(f"Unknown magic shield type {magic_shield_type}")
        else:  # None or empty
            self.magic_shield_keeper = NoopKeeper()

    def init_item_crosshair_macros(
        self,
        macro_configs: List[ItemCrosshairMacroConfig],
        hotkeys_config: HotkeysConfig,
        item_crosshair_macros: Optional[List[ItemCrosshairMacro]] = None,
    ):
        self.unload_item_crosshair_macros()
        if item_crosshair_macros is not None:
            self.item_crosshair_macros = item_crosshair_macros
        else:
            for macro_config in macro_configs:
                self.item_crosshair_macros.append(
                    ItemCrosshairMacro(self.client, macro_config, hotkeys_config)
                )

    def unload_item_crosshair_macros(self):
        self.__unhook_macros(self.item_crosshair_macros)
        self.item_crosshair_macros = []

    def init_directional_macros(
        self,
        macro_configs: List[DirectionalMacroConfig],
        directional_macros: Optional[List[DirectionalMacro]] = None,
    ):
        self.unload_directional_macros()
        if directional_macros is not None:
            self.directional_macros = directional_macros
        else:
            for macro_config in macro_configs:
                self.directional_macros.append(DirectionalMacro(macro_config))

    def unload_directional_macros(self):
        self.__unhook_macros(self.directional_macros)
        self.directional_macros = []

    def init_core_macros(
        self,
        hotkeys_config: HotkeysConfig,
        core_macros: Optional[List[Macro]] = None
    ):
        self.unload_core_macros()
        if core_macros is not None:
            self.core_macros = core_macros
        else:
            cancel_emergency_key = hotkeys_config.cancel_emergency
            if cancel_emergency_key:
                self.core_macros.append(
                    CancelEmergencyMacro(self.emergency_reporter, cancel_emergency_key)
                )
            start_emergency_key = hotkeys_config.start_emergency
            if start_emergency_key:
                self.core_macros.append(
                    StartEmergencyMacro(self.emergency_reporter, start_emergency_key)
                )
            cancel_tank_mode_key = hotkeys_config.cancel_tank_mode
            if cancel_tank_mode_key:
                self.core_macros.append(
                    CancelTankModeMacro(self.tank_mode_reporter, cancel_tank_mode_key)
                )
            start_tank_mode_key = hotkeys_config.start_tank_mode
            if start_tank_mode_key:
                self.core_macros.append(
                    StartTankModeMacro(self.tank_mode_reporter, start_tank_mode_key)
                )

    def unload_core_macros(self):
        self.__unhook_macros(self.core_macros)
        self.core_macros = []

    def unhook_macros(self):
        self.__unhook_macros(self.item_crosshair_macros)
        self.__unhook_macros(self.core_macros)
        self.__unhook_macros(self.directional_macros)

    def __unhook_macros(self, macros: Optional[List[Macro]] = None):
        for macro in macros or []:
            macro.unhook_hotkey()

    def hook_macros(self):
        self.__hook_macros(self.item_crosshair_macros)
        self.__hook_macros(self.core_macros)
        self.__hook_macros(self.directional_macros)

    def __hook_macros(self, macros: Optional[List[Macro]] = None):
        for macro in macros or []:
            macro.hook_hotkey()

    def handle_char_status(self, char_status: CharStatus):
        # First set the emergency status, so all sub-keepers can change their
        # their behaviours accordingly.
        self.handle_emergency_status_change(char_status)

        # Note that we have to handle stats changes always, even if they
        # haven't actually changed, because a command to heal or drink mana
        # or haste could be ignored if the character is exhausted, therefore
        # we have to spam the action until the effect takes place.
        #
        # The order of these is important, since reading pixels off the screen
        # takes a few miliseconds, so addressing equipment before addresing
        # magic shield, it will make it so that magic shield will have to wait
        # for equipment pixels to fetched before magic shield status pixels.
        #
        # Additionally, casting spells that share a cooldown has an effect on
        # the subsequent char keeping. e.g. if we cast haste before casting
        # utamo, then we won't be able to cast utamo when needed since using
        # haste will put utamo on cooldown.
        self.handle_hp_change(char_status)
        self.handle_shield_change(char_status)
        self.handle_mana_change(char_status)
        self.handle_equipment(char_status)
        self.handle_speed_change(char_status)

    def handle_emergency_status_change(self, char_status: CharStatus):
        if self.emergency_reporter.in_emergency:
            if self.emergency_reporter.should_stop_emergency(char_status):
                self.emergency_reporter.stop_emergency()
        elif self.emergency_reporter.is_emergency(char_status):
            self.emergency_reporter.start_emergency()

    def handle_shield_change(self, char_status: CharStatus):
        self.magic_shield_keeper.handle_status_change(char_status)

    def handle_hp_change(self, char_status: CharStatus):
        is_downtime = self.speed_keeper.is_hasted(
            char_status.speed
        ) and self.mana_keeper.is_healthy(char_status)
        self.hp_keeper.handle_status_change(char_status, is_downtime)

    def handle_mana_change(self, char_status: CharStatus):
        is_downtime = (
            self.hp_keeper.is_healthy(char_status) and
            self.speed_keeper.is_hasted(char_status.speed)
        )
        self.mana_keeper.handle_status_change(char_status, is_downtime)

    def handle_speed_change(self, char_status: CharStatus):
        if not self.should_skip_haste(char_status):
            self.speed_keeper.handle_status_change(char_status)

    def should_skip_haste(self, char_status: CharStatus) -> bool:
        # Do not issue order to haste if we're at critical HP levels,
        # since haste shared cooldown with magic shield.
        if self.hp_keeper.is_critical_hp(char_status.hp) and \
           not self.magic_shield_keeper.is_healthy(char_status):
            return True

        # Do not issue a haste order if we're not paralyzed and we're at
        # critical mana levels.
        if self.mana_keeper.is_critical_mana(
            char_status.mana
        ) and not self.speed_keeper.is_paralized(char_status.speed):
            return True

        # Do not issue haste, if we should be casting magic shield next, since
        # haste and magic shield share cooldowns.
        if (
            char_status.magic_shield_status == MagicShieldStatus.OFF_COOLDOWN
            and self.magic_shield_keeper.should_cast(char_status)
        ):
            return True

        return False

    def handle_equipment(self, char_status: CharStatus):
        self.equipment_keeper.handle_status_change(char_status)


class NoopKeeper:
    def handle_status_change(self, _: CharStatus):
        pass

    def should_cast(self, _: CharStatus) -> bool:
        return False

    def is_healthy(self, _: CharStatus) -> bool:
        return True
