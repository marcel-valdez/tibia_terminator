#!/usr/bin/env python3.8

from typing import List


class ItemName:
    __items = {}

    def __init__(self, name: str):
        self.name = name
        self.__class__.register(self.__class__, self)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return (isinstance(other, str) and other == self.name) or (
            isinstance(other, self.__class__) and self.name == other.name
        )

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def from_name(cls, name: str):
        return cls.items().get(name, None)

    @staticmethod
    def register(cls, item):
        cls.items(cls)[item.name] = item

    @staticmethod
    def items(cls):
        return cls.__items


class AmuletName(ItemName):
    UNKNOWN = ItemName("unknown")
    EMPTY = ItemName("empty.amulet")
    # stone skin amuelt
    SSA = ItemName("ssa.amulet")
    # sacred tree amulet
    STA = ItemName("sacred.amulet")
    # bonfire amulet
    BONFIRE = ItemName("bonfire.amulet")
    # leviathan's amulet
    LEVIATHAN = ItemName("leviathan.amulet")
    # shockwave amulet
    SHOCK = ItemName("shockwave.amulet")
    # gill necklace
    GILL = ItemName("gill.amulet")
    # glacier amulet
    GLACIER = ItemName("glacier.amulet")
    # terra amulet
    TERRA = ItemName("terra.amulet")
    # magma amulet
    MAGMA = ItemName("magma.amulet")
    # lightning pendant
    LIGHTNING = ItemName("lightning.amulet")
    # necklace of the deep
    DEEP = ItemName("deep.amulet")
    # prismatic necklace
    PRISM = ItemName("prismatic.amulet")
    # glooth
    GLOOTH = ItemName("glooth.amulet")

    def __init__(self, name):
        super().__init__(name)


class RingName(ItemName):
    UNKNOWN = ItemName("unknown")
    EMPTY = ItemName("empty.ring")
    # might ring
    MIGHT = ItemName("might.ring")
    # prismatic ring
    PRISM = ItemName("prismatic.ring")

    def __init__(self, name):
        super().__init__(name)


if __name__ == "__main__":
    print(AmuletName.SHOCK.name)
    print(AmuletName.UNKNOWN == RingName.UNKNOWN)
