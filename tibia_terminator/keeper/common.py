from typing import NamedTuple, List, Dict
from enum import Enum


class StatConfig(NamedTuple):
    downtime: int
    hi: int
    lo: int
    critical: int

    def validate(self) -> bool:
        if not (self.critical < self.lo < self.hi < self.downtime):
            raise Exception(
                "Invalid critical, hi, lo, downtime ranges battle config. "
                f"Found: {self}. Make sure to always configure such that: "
                "critical < lo < hi < downtime")


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


class ThresholdCalculator:
    def __init__(self, stat_config: StatConfig,
                 priority_threshold_map: Dict[RefillPriority, int]):
        self.stat_config = stat_config
        self.priority_threshold_map = priority_threshold_map

    def gen_threshold_ms(self, current: int) -> int:
        critical_threshold_ms = self.priority_threshold_map[
            RefillPriority.CRITICAL]
        if current <= self.stat_config.critical:
            return critical_threshold_ms

        hi_pri_threshold_ms = self.priority_threshold_map[
            RefillPriority.HIGH_PRIORITY]
        half_hi_pri_stat = (self.stat_config.hi + self.stat_config.lo) / 2
        if self.stat_config.critical < current <= half_hi_pri_stat:
            hi_pri_pct = (current - self.stat_config.critical) / (
                half_hi_pri_stat - self.stat_config.critical)
            critical_to_hi_pri_ms = hi_pri_threshold_ms - critical_threshold_ms
            return int(critical_threshold_ms +
                       (hi_pri_pct * critical_to_hi_pri_ms))

        downtime_threshold_ms = self.priority_threshold_map[
            RefillPriority.DOWNTIME]
        if half_hi_pri_stat < current <= self.stat_config.downtime:
            hi_pri_to_downtime_ms = downtime_threshold_ms - hi_pri_threshold_ms
            downtime_pct = (current - half_hi_pri_stat) / (self.stat_config.downtime -
                                                           half_hi_pri_stat)
            return int(hi_pri_threshold_ms +
                       (downtime_pct * hi_pri_to_downtime_ms))

        if current > self.stat_config.downtime:
            return self.priority_threshold_map[RefillPriority.NO_REFILL]

        raise Exception("This should never happen.")
