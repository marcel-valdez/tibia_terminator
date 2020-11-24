# /usr/bin/env python3

from window_utils import ScreenReader


class MagicShieldStatus:
    RECENTLY_CAST = 'recently_cast'
    OFF_COOLDOWN = 'off_cooldown'
    ON_COOLDOWN = 'on_cooldown'

# Playable area set at Y: 696 with 2 cols on left and 2 cols on right

AMULET_SPEC = {
    "empty": [
        "3d3f42",
        "434648",
        "252626",
        "232424",
    ]
}

AMULET_COORDS = [
    # upper pixel
    (1768, 259),
    # lower pixel
    (1768, 272),
    # left pixel
    (1758, 261),
    # right pixel
    (1779, 261)
]

RING_SPEC = {
    "empty": [
        "252625",
        "36393c",
        "2e2e2f",
        "3d4042",
    ]
}

RING_COORDS = [
    # upper pixel
    (1768, 333),
    # lower pixel
    (1768, 338),
    # left pixel
    (1765, 337),
    # right pixel
    (1770, 337)
]


MAGIC_SHIELD_SPEC = {
    MagicShieldStatus.RECENTLY_CAST: [
        "3730A",
    ],
    MagicShieldStatus.OFF_COOLDOWN: [
        "B9A022",
    ]
}

MAGIC_SHIELD_COORDS = [
    (1285, 760)
]


class EquipmentReader(ScreenReader):

    def matches_screen(self, coords, color_spec):
        pixels = map(lambda (x, y): self.get_pixel_color(x, y), coords)
        match = True
        for i in range(0, len(pixels)):
            match &= pixels[i].lower() == color_spec[i].lower()
        return match

    def is_amulet(self, name):
        return self.matches_screen(AMULET_COORDS, AMULET_SPEC[name])

    def is_amulet_empty(self):
        return self.is_amulet('empty')

    def is_ring(self, name):
      return self.matches_screen(RING_COORDS, RING_SPEC[name])

    def is_ring_empty(self):
        return self.is_ring('empty')

    def get_magic_shield_status(self):
        for name in MAGIC_SHIELD_SPEC:
            if self.matches_screen(MAGIC_SHIELD_COORDS, MAGIC_SHIELD_SPEC[name]):
                return name
        # There are only 3 possible states: recently cast, off cooldown and
        # on cooldown.
        return MagicShieldStatus.ON_COOLDOWN


if __name__ == '__main__':
    import time
    eq_reader = EquipmentReader()
    eq_reader.open()
    try:
        print("Amulet color spec")
        for (x, y) in AMULET_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        print("Ring color spec")
        for (x, y) in RING_COORDS:
            print(eq_reader.get_pixel_color(x, y))

        for name in AMULET_SPEC:
            start_ms = time.time() * 1000
            is_amulet_ = eq_reader.is_amulet(name)
            end_ms = time.time() * 1000
            print("is_amulet('" + name + "'): " + str(is_amulet_))
            print("Elapsed time: " + str(end_ms - start_ms) + " ms")

        for name in RING_SPEC:
            start_ms = time.time() * 1000
            is_ring_ = eq_reader.is_ring(name)
            end_ms = time.time() * 1000
            print("is_ring('" + name + "'): " + str(is_ring_))
            print("Elapsed time: " + str(end_ms - start_ms) + " ms")

        start_ms = time.time() * 1000
        magic_shield_status = eq_reader.get_magic_shield_status()
        end_ms = time.time() * 1000
        print("get_magic_shield_status(): " + str(magic_shield_status))
        print("Elapsed time: " + str(end_ms - start_ms) + " ms")
    finally:
        eq_reader.close()
