"""Utilities for more easily creating char configs."""


def copy(original, update):
    """Make a copy of the original with updated values."""
    copy = original.copy()
    copy.update(update)
    return copy
