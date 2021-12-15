"""Keeps mana at healthy levels specific for Knights
by balancing the usage of heal and mana potions using an effective strategy.
"""

import random
import time

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

    @classmethod
    def values(cls) -> List['RefillPriority']:
        return [cls.NO_REFILL, cls.DOWNTIME, cls.HIGH_PRIORITY, cls.CRITICAL]

    def higher_priority(self) -> "RefillPriority":
        if self is RefillPriority.CRITICAL:
            return self
        if self is RefillPriority.HIGH_PRIORITY:
            return RefillPriority.CRITICAL
        if self is RefillPriority.DOWNTIME:
            return RefillPriority.HIGH_PRIORITY
        return RefillPriority.DOWNTIME

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
        return RefillPriorities(hp_priority=hp_priority,
                                mana_priority=mana_priority)

    def get_hp_priority(self, char_status: CharStatus) -> RefillPriority:
        return KnightPrioritiesStrategy.get_priority(self.hp_config,
                                                     self.last_hp_priority,
                                                     char_status.hp)

    def get_mana_priority(self, char_status: CharStatus) -> RefillPriority:
        return KnightPrioritiesStrategy.get_priority(self.mana_config,
                                                     self.last_mana_priority,
                                                     char_status.mana)

    @staticmethod
    def get_priority(stat_config: StatConfig, last_priority: RefillPriority,
                     stat_value: int) -> RefillPriority:
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

    def __init__(self, client: ClientInterface, battle_config: BattleConfig,
                 total_hp: int):
        if not battle_config.potion_hp_hi:
            raise Exception("battle_config.potion_hp_hi can't be null")
        if not battle_config.potion_hp_lo:
            raise Exception("battle_config.potion_hp_lo can't be null")
        if not battle_config.potion_hp_critical:
            raise Exception("battle_config.potion_hp_critical can't be null")

        self.mana_config = StatConfig(
            downtime=battle_config.downtime_mana,
            hi=battle_config.mana_hi,
            lo=battle_config.mana_lo,
            critical=battle_config.critical_mana,
        )
        self.validate_stat_config(self.mana_config)
        self.hp_config = StatConfig(
            downtime=total_hp - battle_config.heal_at_missing,
            hi=battle_config.potion_hp_hi,
            lo=battle_config.potion_hp_lo,
            critical=battle_config.potion_hp_critical,
        )
        self.validate_stat_config(self.hp_config)

        self.priorities_strategy = KnightPrioritiesStrategy(
            mana_config=self.mana_config,
            hp_config=self.hp_config,
        )

        self.client = client
        self.mana_lo = battle_config.mana_lo
        self.critical_mana = battle_config.critical_mana
        self.refill_probability_map = type(self).gen_refill_probability_map()
        self.last_threshold_ms = 9999999
        self.last_threshold_ts = time.time()

    def handle_status_change(self, char_status: CharStatus, is_downtime: bool):
        priorities = self.priorities_strategy.fetch_priorities(char_status)
        if (priorities.mana_priority is RefillPriority.NO_REFILL
                and priorities.hp_priority is RefillPriority.NO_REFILL):
            return

        if not is_downtime and (
                priorities.mana_priority <= RefillPriority.DOWNTIME
                and priorities.hp_priority <= RefillPriority.DOWNTIME):
            return

        refill_type = self.pick_refill(char_status, priorities)
        if refill_type is RefillType.HP:
            used_potion = self.drink_hp_potion(priorities.hp_priority,
                                               char_status)
            # Make sure to refill mana if we're out of heal potions
            if not used_potion:
                if (is_downtime
                        and priorities.mana_priority is RefillPriority.DOWNTIME
                        or priorities.mana_priority > RefillPriority.DOWNTIME):
                    self.drink_mana_potion(char_status)
        else:
            self.drink_mana_potion(char_status)

    def drink_hp_potion(self, refill_priority: RefillPriority,
                        char_status: CharStatus) -> bool:
        threshold_ms = self.get_threshold_ms(char_status.hp, self.hp_config)
        if refill_priority is RefillPriority.CRITICAL:
            if char_status.has_greater_heal_potions:
                self.client.drink_greater_heal(
                    self.update_last_threshold(threshold_ms))
            elif char_status.has_medium_heal_potions:
                self.client.drink_medium_heal(
                    self.update_last_threshold(threshold_ms))
            elif char_status.has_minor_heal_potions:
                self.client.drink_minor_heal(
                    self.update_last_threshold(threshold_ms))
            else:
                return False
        elif refill_priority is RefillPriority.HIGH_PRIORITY:
            if char_status.has_medium_heal_potions:
                self.client.drink_medium_heal(
                    self.update_last_threshold(threshold_ms))
            elif char_status.has_greater_heal_potions:
                self.client.drink_greater_heal(
                    self.update_last_threshold(threshold_ms))
            elif char_status.has_minor_heal_potions:
                self.client.drink_minor_heal(
                    self.update_last_threshold(threshold_ms))
            else:
                return False
        elif refill_priority is RefillPriority.DOWNTIME:
            if char_status.has_minor_heal_potions:
                self.client.drink_minor_heal(
                    self.update_last_threshold(threshold_ms))
            else:
                return False

        self.last_threshold_ms = threshold_ms
        return True

    def drink_mana_potion(self, char_status: CharStatus):
        threshold_ms = self.update_last_threshold(
            self.get_threshold_ms(
                char_status.mana,
                self.mana_config,
            ))
        self.client.drink_mana(threshold_ms)

    def pick_refill(self, char_status: CharStatus,
                    priorities: RefillPriorities) -> RefillType:
        hp_probability = self.gen_hp_refill_probability(
            char_status.hp, priorities)
        return self.random_choice(prob_a=hp_probability,
                                  choice_a=RefillType.HP,
                                  choice_b=RefillType.MANA)

    def is_critical_mana(self, current_mana: int) -> bool:
        return current_mana <= self.critical_mana

    def is_healthy(self, char_status: CharStatus) -> bool:
        return char_status.mana > self.mana_lo

    # get the probability equivalent to the hp range
    #
    # i.e. if we're 50% of the way to the next probability, then add
    # half of the range between the current probability and the next one.
    #
    # e.g. given hp critical = 10, lo = 30, hi = 60 and hp = 35 and current
    # mana is critical, then the range is 10 to 60, half way there is 35,
    # given that the probability of critical is 100% and high priority
    # against critical mana is 33%.
    # then the result should be half way between 33% to 100%, meaning
    # 33% + 67%/2 = 66.5%
    def gen_hp_refill_probability(self, current_hp: int,
                                  priorities: RefillPriorities) -> float:
        priority_probability = self.refill_probability_map[priorities]
        if (priorities.hp_priority is RefillPriority.NO_REFILL
                or priorities.mana_priority is RefillPriority.NO_REFILL):
            return priority_probability

        if priorities.hp_priority is RefillPriority.CRITICAL:
            return priority_probability

        if (priorities.hp_priority is RefillPriority.DOWNTIME
                and priorities.mana_priority is RefillPriority.DOWNTIME):
            return priority_probability

        higher_priority_probability = self.refill_probability_map[
            RefillPriorities(
                hp_priority=priorities.hp_priority.higher_priority(),
                mana_priority=priorities.mana_priority)]
        higher_priority_hp_boundary = self.hp_config.critical
        if priorities.hp_priority is RefillPriority.DOWNTIME:
            higher_priority_hp_boundary = self.hp_config.hi

        priority_hp_boundary = self.hp_config.hi
        if priorities.hp_priority is RefillPriority.DOWNTIME:
            priority_hp_boundary = self.hp_config.downtime

        range_probability_hp = higher_priority_probability - priority_probability
        range_priority_hp = priority_hp_boundary - higher_priority_hp_boundary
        pct_priority_hp = (priority_hp_boundary - current_hp) / range_priority_hp
        return priority_probability + (range_probability_hp * pct_priority_hp)

    @staticmethod
    def gen_choice_constant_hp(
            hp_priority: RefillPriority,
            hp_probability: float) -> List[Tuple[RefillPriorities, float]]:
        return [(
            RefillPriorities(hp_priority=hp_priority,
                             mana_priority=mana_priority),
            hp_probability,
        ) for mana_priority in RefillPriority]

    @staticmethod
    def gen_choice_constant_mana(
            mana_priority: RefillPriority,
            mana_probability: float) -> List[Tuple[RefillPriorities, float]]:
        return [(
            RefillPriorities(hp_priority=hp_priority,
                             mana_priority=mana_priority),
            1 - mana_probability,
        ) for hp_priority in RefillPriority]

    @staticmethod
    def gen_refill_probability_map() -> Dict[RefillPriorities, float]:
        return dict(
            # whenever HP is critical always favour HP potions
            KnightPotionKeeper.gen_choice_constant_hp(
                hp_priority=RefillPriority.CRITICAL, hp_probability=1.0) +
            KnightPotionKeeper.gen_choice_constant_hp(
                hp_priority=RefillPriority.DOWNTIME, hp_probability=0.0) +
            KnightPotionKeeper.gen_choice_constant_mana(
                mana_priority=RefillPriority.DOWNTIME, mana_probability=0.0) +
            KnightPotionKeeper.gen_choice_constant_hp(
                hp_priority=RefillPriority.NO_REFILL, hp_probability=0.0) +
            KnightPotionKeeper.gen_choice_constant_mana(
                mana_priority=RefillPriority.NO_REFILL, mana_probability=0.0) +
            [
                # favour mana 3:1 because knights can heal with spells too
                (
                    RefillPriorities(
                        hp_priority=RefillPriority.DOWNTIME,
                        mana_priority=RefillPriority.DOWNTIME,
                    ),
                    0.25,
                ),
                # favour mana 2:1, because in critical mana levels
                # we need it to do more things than just heal and
                # HP is not yet critical.
                (
                    RefillPriorities(
                        hp_priority=RefillPriority.HIGH_PRIORITY,
                        mana_priority=RefillPriority.CRITICAL,
                    ),
                    0.33,
                ),
                # favour HP 3:2, because mana helps heal as well
                (
                    RefillPriorities(
                        hp_priority=RefillPriority.HIGH_PRIORITY,
                        mana_priority=RefillPriority.HIGH_PRIORITY,
                    ),
                    0.6,
                ),
            ])

    def update_last_threshold(self, new_threshold_ms: int) -> int:
        now_ts = time.time()
        adjusted_threshold_ms = new_threshold_ms
        # if its been less than one second since the last threshold
        if now_ts - self.last_threshold_ts < 1:
            # then adjust threshold
            adjusted_threshold_ms = min(self.last_threshold_ms,
                                        new_threshold_ms)

        self.last_threshold_ts = now_ts
        self.last_threshold_ms = new_threshold_ms
        return adjusted_threshold_ms

    def get_threshold_ms(self, stat_value: int,
                         stat_config: StatConfig) -> int:
        critical_threshold_ms = self.get_priority_threshold_ms(
            RefillPriority.CRITICAL)
        if stat_value <= stat_config.critical:
            return critical_threshold_ms

        hi_pri_threshold_ms = self.get_priority_threshold_ms(
            RefillPriority.HIGH_PRIORITY)
        half_hi_pri_stat = (stat_config.hi + stat_config.lo) / 2
        if stat_config.critical < stat_value <= half_hi_pri_stat:
            hi_pri_pct = (stat_value - stat_config.critical) / (
                half_hi_pri_stat - stat_config.critical)
            critical_to_hi_pri_ms = hi_pri_threshold_ms - critical_threshold_ms
            return int(critical_threshold_ms +
                       (hi_pri_pct * critical_to_hi_pri_ms))

        downtime_threshold_ms = self.get_priority_threshold_ms(
            RefillPriority.DOWNTIME)
        if half_hi_pri_stat < stat_value <= stat_config.downtime:
            hi_pri_to_downtime_ms = downtime_threshold_ms - hi_pri_threshold_ms
            downtime_pct = (stat_value - half_hi_pri_stat) / (
                stat_config.downtime - half_hi_pri_stat)
            return int(hi_pri_threshold_ms +
                       (downtime_pct * hi_pri_to_downtime_ms))

        if stat_value > stat_config.downtime:
            return self.get_priority_threshold_ms(RefillPriority.NO_REFILL)
        raise Exception("This should never happen.")

    def get_priority_threshold_ms(self, priority: RefillPriority) -> int:
        return KnightPotionKeeper.THRESHOLD_PRIORITY_MAP[priority]

    def validate_stat_config(self, stat_config: StatConfig) -> None:
        if not (stat_config.critical < stat_config.lo < stat_config.hi <
                stat_config.downtime):
            raise Exception(
                "Invalid critical, hi, lo, downtime ranges battle config. "
                f"Found: {stat_config}. Make sure to always configure such that: "
                "critical < lo < hi < downtime")

    def random_choice(self, prob_a: float, choice_a: T, choice_b: T) -> T:
        value = random.random()
        return choice_a if value <= prob_a else choice_b
