#!/usr/bin/env python3.8

from typing import Union, List, Dict

from tibia_terminator.reader.color_spec import ItemName

from tibia_terminator.schemas.reader.interface_config_schema import (
    ItemRepositorySpec,
    ItemEntry,
    ItemColors,
)


UNKNOWN_ITEM = ItemEntry(
    name="unknown",
    equipped_colors=ItemColors("FFF", "FFF", "FFF", "FFF"),
    action_bar_colors=ItemColors("FFF", "FFF", "FFF", "FFF"),
)


class ItemRepositoryContainer:
    def __init__(self, item_repository: ItemRepositorySpec):
        self.item_repository = item_repository
        self.rings_by_name: Dict[str, ItemEntry] = {}
        self.rings_by_action_bar_colors: Dict[ItemColors, ItemEntry] = {}
        self.rings_by_equipped_colors: Dict[ItemColors, ItemEntry] = {}
        self.amulets_by_name: Dict[str, ItemEntry] = {}
        self.amulets_by_action_bar_colors: Dict[ItemColors, ItemEntry] = {}
        self.amulets_by_equipped_colors: Dict[ItemColors, ItemEntry] = {}

    def lookup_ring_by_name(self, name: Union[str, ItemName]) -> ItemEntry:
        name = str(name)
        ring = self.rings_by_name.get(name, UNKNOWN_ITEM)
        if ring is not UNKNOWN_ITEM:
            return ring

        rings = self.item_repository.rings
        ring_matches = tuple(filter(lambda r: r.name == str(name), rings))
        if len(ring_matches) == 0:
            raise Exception(f"Ring {name} has no specification in the configuration!")
        if len(ring_matches) > 1:
            raise Exception(
                f"Ring {name} has multiple specification in the configuration!"
            )

        ring = ring_matches[0]
        self.rings_by_name[name] = ring
        return ring

    def lookup_amulet_by_name(self, name: Union[str, ItemName]) -> ItemEntry:
        name = str(name)
        amulet = self.amulets_by_name.get(name, UNKNOWN_ITEM)
        if amulet is not UNKNOWN_ITEM:
            return amulet

        amulets = self.item_repository.amulets
        amulet_matches = tuple(filter(lambda a: a.name == name, amulets))
        if len(amulet_matches) == 0:
            raise Exception(f"Amulet {name} has no specification in the configuration!")
        if len(amulet_matches) > 1:
            raise Exception(
                f"Amulet {name} has multiple specification in the configuration!"
            )
        amulet = amulet_matches[0]
        self.amulets_by_name[name] = amulet
        return amulet

    def lookup_amulet_by_action_bar_colors(
        self, colors: ItemColors
    ) -> ItemEntry:
        result = self.amulets_by_action_bar_colors.get(colors, UNKNOWN_ITEM)
        if result is not UNKNOWN_ITEM:
            return result

        for amulet in self.item_repository.amulets:
            for spec_colors in amulet.action_bar_colors:
                if spec_colors == colors:
                    result = amulet

        self.amulets_by_action_bar_colors[colors] = result
        return result

    def lookup_ring_by_action_bar_colors(self, colors: ItemColors) -> ItemEntry:
        result = self.rings_by_action_bar_colors.get(colors, UNKNOWN_ITEM)
        if result is not UNKNOWN_ITEM:
            return result

        for ring in self.item_repository.rings:
            for spec_colors in ring.action_bar_colors:
                if spec_colors == colors:
                    result = ring

        self.rings_by_action_bar_colors[colors] = result
        return result

    def lookup_ring_by_equipped_colors(self, colors: ItemColors) -> ItemEntry:
        result = self.rings_by_equipped_colors.get(colors, UNKNOWN_ITEM)
        if result is not UNKNOWN_ITEM:
            return result

        for ring in self.item_repository.rings:
            for spec_colors in ring.equipped_colors:
                if spec_colors == colors:
                    result = ring

        self.rings_by_equipped_colors[colors] = result
        return result

    def lookup_amulet_by_equipped_colors(self, colors: ItemColors) -> ItemEntry:
        result = self.rings_by_equipped_colors.get(colors, UNKNOWN_ITEM)
        if result is not UNKNOWN_ITEM:
            return result

        for amulet in self.item_repository.amulets:
            for spec_colors in amulet.equipped_colors:
                if spec_colors == colors:
                    result = amulet

        self.amulets_by_equipped_colors[colors] = result
        return result
