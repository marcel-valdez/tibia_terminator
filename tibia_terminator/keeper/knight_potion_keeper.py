"""Keeps mana at healthy levels specific for Knights
by balancing the usage of heal and mana potions using an effective strategy.
"""

import random

from enum import Enum
from typing import TypeVar, Tuple, Dict, NamedTuple, List


from tibia_terminator.interface.client_interface import ClientInterface
from tibia_terminator.common.char_status import CharStatus
from tibia_terminator.schemas.char_config_schema import BattleConfig


T = TypeVar("T")


class RefillPriority(Enum):
    NO_REFILL = 1
    DOWNTIME = 2
    HIGH_PRIORITY = 3
    CRITICAL = 4

    def __lt__(self, other: "RefillPriority") -> bool:
        if not isinstance(other, RefillPriority):
            raise Exception(f"Can't compare {type(self)} < {type(other)}")
        return self.value < other.value

    def __le__(self, other: "RefillPriority") -> bool:
        if not isinstance(other, RefillPriority):
            raise Exception(f"Can't compare {type(self)} <= {type(other)}")
        return self.value <= other.value

    def __gt__(self, other: "RefillPriority") -> bool:
        if not isinstance(other, RefillPriority):
            raise Exception(f"Can't compare {type(self)} > {type(other)}")
        return self.value > other.value

    def __ge__(self, other: "RefillPriority") -> bool:
        if not isinstance(other, RefillPriority):
            raise Exception(f"Can't compare {type(self)} >= {type(other)}")
        return self.value >= other.value


class RefillPriorities(NamedTuple):
    hp_priority: RefillPriority
    mana_priority: RefillPriority


class RefillType(Enum):
    MANA = 1
    HP = 2


class StatConfig(NamedTuple):
    downtime: int
    hi: int
    lo: int
    critical: int


class KnightPrioritiesStrategy:
    def __init__(self, mana_config: StatConfig, hp_config: StatConfig):
        self.mana_config = mana_config
        self.hp_config = hp_config
        self.last_mana_priority = RefillPriority.NO_REFILL
        self.last_hp_priority = RefillPriority.NO_REFILL

    def fetch_priorities(self, char_status: CharStatus) -> RefillPriorities:
        hp_priority = self.get_hp_priority(char_status)
        mana_priority = self.get_mana_priority(char_status)
        self.last_hp_priority = hp_priority
        self.last_mana_priority = mana_priority
        return RefillPriorities(hp_priority=hp_priority, mana_priority=mana_priority)

    def get_hp_priority(self, char_status: CharStatus) -> RefillPriority:
        return KnightPrioritiesStrategy.get_priority(
            self.hp_config, self.last_hp_priority, char_status.hp
        )

    def get_mana_priority(self, char_status: CharStatus) -> RefillPriority:
        return KnightPrioritiesStrategy.get_priority(
            self.mana_config, self.last_mana_priority, char_status.mana
        )

    @staticmethod
    def get_priority(
        stat_config: StatConfig, last_priority: RefillPriority, stat_value: int
    ) -> RefillPriority:
        if stat_value < stat_config.critical:
            return RefillPriority.CRITICAL
        if stat_config.critical <= stat_value < stat_config.lo:
            # continue in critical priority until stat_config.lo
            # if last priority was critical
            return max(last_priority, RefillPriority.HIGH_PRIORITY)
        if stat_config.lo <= stat_value < stat_config.hi:
            return RefillPriority.HIGH_PRIORITY
        if stat_config.hi <= stat_value < stat_config.downtime:
            return RefillPriority.DOWNTIME

        return RefillPriority.NO_REFILL


class KnightPotionKeeper:
    THRESHOLD_PRIORITY_MAP = {
        RefillPriority.CRITICAL: 666,
        RefillPriority.HIGH_PRIORITY: 1000,
        RefillPriority.DOWNTIME: 2500,
        RefillPriority.NO_REFILL: 60000 * 5,
    }

    def __init__(
        self,
        client: ClientInterface,
        battle_config: BattleConfig,
        total_hp: int
    ):
        self.priorities_strategy = KnightPrioritiesStrategy(
            mana_config=StatConfig(
                battle_config.downtime_mana,
                battle_config.mana_hi,
                battle_config.mana_lo,
                battle_config.critical_mana,
            ),
            hp_config=StatConfig(
                total_hp - battle_config.heal_at_missing,
                battle_config.potion_hp_hi,
                battle_config.potion_hp_lo,
                battle_config.potion_hp_critical,
            ),
        )
        self.client = client
        self.mana_lo = battle_config.mana_lo
        self.critical_mana = battle_config.critical_mana
        self.refill_probability_map = self.gen_refill_probability_map()

    def handle_status_change(self, char_status: CharStatus, is_downtime: bool):
        priorities = self.priorities_strategy.fetch_priorities(char_status)
        if (
            priorities.mana_priority is RefillPriority.NO_REFILL
            and priorities.hp_priority is RefillPriority.NO_REFILL
        ):
            return

        if not is_downtime and (
            priorities.mana_priority <= RefillPriority.DOWNTIME
            and priorities.hp_priority <= RefillPriority.DOWNTIME
        ):
            return

        refill_type = self.pick_refill(priorities)
        if refill_type is RefillType.HP:
            used_potion = self.drink_hp_potion(priorities.hp_priority, char_status)
            # Make sure to refill mana if we're out of heal potions
            if not used_potion:
                if (
                    is_downtime
                    and priorities.mana_priority is RefillPriority.DOWNTIME
                    or priorities.mana_priority > RefillPriority.DOWNTIME
                ):
                    self.drink_mana_potion(priorities.mana_priority)
        else:
            self.drink_mana_potion(priorities.mana_priority)

    def drink_hp_potion(
        self, refill_priority: RefillPriority, char_status: CharStatus
    ) -> bool:
        threshold_ms = self.get_priority_threshold_ms(refill_priority)
        if refill_priority is RefillPriority.CRITICAL:
            if char_status.has_greater_heal_potions:
                self.client.drink_greater_heal(threshold_ms)
            elif char_status.has_medium_heal_potions:
                self.client.drink_medium_heal(threshold_ms)
            elif char_status.has_minor_heal_potions:
                self.client.drink_minor_heal(threshold_ms)
            else:
                return False
        elif refill_priority is RefillPriority.HIGH_PRIORITY:
            if char_status.has_medium_heal_potions:
                self.client.drink_medium_heal(threshold_ms)
            elif char_status.has_greater_heal_potions:
                self.client.drink_greater_heal(threshold_ms)
            elif char_status.has_minor_heal_potions:
                self.client.drink_minor_heal(threshold_ms)
            else:
                return False
        elif refill_priority is RefillPriority.DOWNTIME:
            if char_status.has_minor_heal_potions:
                self.client.drink_minor_heal(threshold_ms)
            else:
                return False
        return True

    def drink_mana_potion(self, refill_priority: RefillPriority):
        threshold_ms = self.get_priority_threshold_ms(refill_priority)
        self.client.drink_mana(threshold_ms)

    def pick_refill(self, priorities: RefillPriorities) -> RefillType:
        hp_probability = self.refill_probability_map[priorities]
        return self.random_choice(
            prob_a=hp_probability, choice_a=RefillType.HP, choice_b=RefillType.MANA
        )

    def is_critical_mana(self, current_mana: int) -> bool:
        return current_mana <= self.critical_mana

    def is_healthy_mana(self, current_mana: int) -> bool:
        return current_mana > self.mana_lo

    @staticmethod
    def gen_choice_constant_hp(
        hp_priority: RefillPriority, hp_probability: float
    ) -> List[Tuple[RefillPriorities, float]]:
        return [
            (
                RefillPriorities(hp_priority=hp_priority, mana_priority=mana_priority),
                hp_probability,
            )
            for mana_priority in RefillPriority
        ]

    @staticmethod
    def gen_choice_constant_mana(
        mana_priority: RefillPriority, mana_probability: float
    ) -> List[Tuple[RefillPriorities, float]]:
        return [
            (
                RefillPriorities(hp_priority=hp_priority, mana_priority=mana_priority),
                1 - mana_probability,
            )
            for hp_priority in RefillPriority
        ]

    def gen_refill_probability_map(self) -> Dict[RefillPriorities, float]:
        return dict(
            # whenever HP is critical always favour HP potions
            KnightPotionKeeper.gen_choice_constant_hp(
                hp_priority=RefillPriority.CRITICAL, hp_probability=1.0
            )
            + KnightPotionKeeper.gen_choice_constant_hp(
                hp_priority=RefillPriority.DOWNTIME, hp_probability=0.0
            )
            + KnightPotionKeeper.gen_choice_constant_mana(
                mana_priority=RefillPriority.DOWNTIME, mana_probability=0.0
            )
            + KnightPotionKeeper.gen_choice_constant_hp(
                hp_priority=RefillPriority.NO_REFILL, hp_probability=0.0
            )
            + KnightPotionKeeper.gen_choice_constant_mana(
                mana_priority=RefillPriority.NO_REFILL, mana_probability=0.0
            )
            + [
                # favour mana 3:1 because knights can heal with spells too
                (
                    RefillPriorities(
                        hp_priority=RefillPriority.DOWNTIME,
                        mana_priority=RefillPriority.DOWNTIME,
                    ),
                    0.25,
                ),
                # favour mana 3:1, because in critical mana levels
                # we need it to do more things than just heal and
                # HP is not yet critical.
                (
                    RefillPriorities(
                        hp_priority=RefillPriority.HIGH_PRIORITY,
                        mana_priority=RefillPriority.CRITICAL,
                    ),
                    0.25,
                ),
                # favour HP 3:2, because mana helps heal as well
                (
                    RefillPriorities(
                        hp_priority=RefillPriority.HIGH_PRIORITY,
                        mana_priority=RefillPriority.HIGH_PRIORITY,
                    ),
                    0.6,
                ),
            ]
        )

    def get_priority_threshold_ms(self, priority: RefillPriority) -> int:
        return KnightPotionKeeper.THRESHOLD_PRIORITY_MAP[priority]

    def random_choice(self, prob_a: float, choice_a: T, choice_b: T) -> T:
        value = random.random()
        return choice_a if value <= prob_a else choice_b

