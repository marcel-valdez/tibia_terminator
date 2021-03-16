#!/usr/bin/env python3.8

from typing import (List, Union)


class ItemName():
    __items = {}

    def __init__(self, name: str):
        self.name = name
        self.__class__.register(self.__class__, self)


    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name

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
    UNKNOWN = ItemName('unknown')
    EMPTY = ItemName('empty.amulet')
    # stone skin amuelt
    SSA = ItemName('ssa.amulet')
    # sacred tree amulet
    STA = ItemName('sacred.amulet')
    # bonfire amulet
    BONFIRE = ItemName('bonfire.amulet')
    # leviathan's amulet
    LEVIATHAN = ItemName('leviathan.amulet')
    # shockwave amulet
    SHOCK = ItemName('shockwave.amulet')
    # gill necklace
    GILL = ItemName('gill.amulet')
    # glacier amulet
    GLACIER = ItemName('glacier.amulet')
    # terra amulet
    TERRA = ItemName('terra.amulet')
    # magma amulet
    MAGMA = ItemName('magma.amulet')
    # lightning pendant
    LIGHTNING = ItemName('lightning.amulet')
    # necklace of the deep
    DEEP = ItemName('deep.amulet')
    # prismatic necklace
    PRISM = ItemName('prismatic.amulet')

    def __init__(self, name):
        super().__init__(name)


class RingName(ItemName):
    UNKNOWN = ItemName('unknown')
    EMPTY = ItemName('empty.ring')
    # might ring
    MIGHT = ItemName('might.ring')
    # prismatic ring
    PRISM = ItemName('prismatic.ring')

    def __init__(self, name):
        super().__init__(name)


class PixelColor():
    """Represents a pixel color from the screen."""

    def __init__(self, color: str):
        self.color = color

    def __hash__(self):
        return hash(self.color)

    def __eq__(self, other):
        return isinstance(other, PixelColor) and self.color == other.color

    def __str__(self):
        return self.color


class ColorSpec():
    def __init__(self, colors: List[PixelColor]):
        self.colors = tuple(colors)

    def __hash__(self):
        return hash(self.colors)

    def __eq__(self, other):
        return isinstance(other, ColorSpec) and self.colors == other.colors


class ItemSpec():
    def __init__(self, name: ItemName, action_color_specs: List[ColorSpec], eq_color_specs: List[ColorSpec]):
        self.action_color_specs = tuple(action_color_specs)
        self.eq_color_specs = tuple(eq_color_specs)
        self.name = name
        self.__hashable = frozenset(
            (self.name, self.action_color_specs, self.eq_color_specs))

    def __hash__(self):
        return hash(self.__hashable)

    def __eq__(self, other):
        return isinstance(other, ItemSpec) and self.__hashable == other.__hashable


class AmuletSpec(ItemSpec):
    def __init__(self, name: ItemName, action_color_specs: List[ColorSpec], eq_color_specs: List[ColorSpec]):
        super().__init__(name, action_color_specs, eq_color_specs)


class RingSpec(ItemSpec):
    def __init__(self, name: ItemName, action_color_specs: List[ColorSpec], eq_color_specs: List[ColorSpec]):
        super().__init__(name, action_color_specs, eq_color_specs)


class ItemRepository():
    def __init__(self, items: List[ItemSpec] = []):
        self.name_to_item = {}
        self.action_spec_to_name = {}
        self.equip_spec_to_name = {}
        for item in items:
            self.__register(item)

    def add(self, item: ItemSpec):
        self.__register(item)

    def get(self, name: ItemName) -> ItemSpec:
        return self.name_to_item.get(name, None)

    def get_action_name(self, color_spec: ColorSpec) -> ItemName:
        """Get the name of the action bar item, given a ColorSpec."""
        return self.action_spec_to_name.get(color_spec, ItemName('unknown'))

    def get_equipment_name(self, color_spec: ColorSpec) -> AmuletName:
        """Get the name of the equipped item, given its ColorSpec."""
        return self.equip_spec_to_name.get(color_spec, ItemName('unknown'))

    def __register(self, item: ItemSpec):
        self.name_to_item[item.name] = item
        for action_color_spec in item.action_color_specs:
            self.action_spec_to_name[action_color_spec] = item.name

        for eq_color_spec in item.eq_color_specs:
            self.equip_spec_to_name[eq_color_spec] = item.name


def spec(*colors):
    _colors = []
    for color in colors:
        _colors.append(PixelColor(color))
    return ColorSpec(_colors)


def item(name: ItemName, action_specs: List[ColorSpec], equip_specs: List[ColorSpec]):
    return ItemSpec(name, action_specs, equip_specs)


SSA = item(
    AmuletName.SSA, [
        spec(
            # upper pixel
            "b9935f",
            # lower pixel
            "3c3c3c",
            # left pixel
            "444444",
            # right pixel
            "454545"
        )
    ],
    [
        spec("252626", "b8b8b8", "252626", "232424")
    ]
)

STA = item(
    AmuletName.STA,
    [spec("4d170", "1ad552", "d421d", "93215")],
    [spec("252626", "1b42c", "252626", "a3f19")]
)

LEVIATHAN = item(
    AmuletName.LEVIATHAN,
    [spec("b4e2f0", "032c1", "444444", "454545")],
    [spec("252626", "262627", "252626", "232424")]
)

SHOCK = item(
    AmuletName.SHOCK,
    [
        spec("61719", "404040", "89d27", "54312"),
        spec("59515", "404040", "6f519", "5d616"),
        spec("68a1f", "404040", "7da24", "5e719"),
        spec("57311", "404040", "7b81c", "5c514")
    ],
    [
        spec("252626", "60719", "91d28", "232424"),
        spec("252626", "6891a", "7e61b", "232424"),
        spec("252626", "5a517", "87b26", "232424"),
        spec("252626", "60719", "91d28", "232424"),
    ]
)

EMPTY_AMULET = item(
    AmuletName.EMPTY,
    [spec("1111111", "222222", "333333", "444444")],
    [spec("3d3f42", "434648", "252626", "232424",)]
)

AMULET_REPOSITORY = ItemRepository([SSA, STA, SHOCK, LEVIATHAN, EMPTY_AMULET])

MIGHT = item(
    RingName.MIGHT,
    [spec("9b8132", "d1af44", "faed75", "d5b246")],
    [spec("252625", "272728", "d1ae43", "927b34")]
)

EMPTY_RING = item(
    RingName.EMPTY,
    [spec("1111111", "222222", "333333", "444444")],
    [spec("252625", "36393c", "2e2e2f", "3d4042")]
)

RING_REPOSITORY = ItemRepository([MIGHT, EMPTY_RING])

if __name__ == '__main__':
    print(AmuletName.SHOCK.name)
    print(AmuletName.UNKNOWN == RingName.UNKNOWN)
