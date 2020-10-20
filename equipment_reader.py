# /usr/bin/env python3

from window_utils import ScreenReader

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


class EquipmentReader(ScreenReader):

    def is_amulet(self, name):
        pixels = map(lambda (x, y): self.get_pixel_color(x, y), AMULET_COORDS)
        for i in range(0, 3):
            if pixels[i] != AMULET_SPEC[name][i]:
                return False
        return True

    def is_amulet_empty(self):
        return self.is_amulet('empty')

    def is_ring(self, name):
        pixels = map(lambda (x, y): self.get_pixel_color(x, y), RING_COORDS)
        for i in range(0, 3):
            if pixels[i] != RING_SPEC[name][i]:
                return False
        return True

    def is_ring_empty(self):
        return self.is_ring('empty')


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
    finally:
        eq_reader.close()
