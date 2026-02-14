"""Dice with injectable random number generator for deterministic testing."""

from __future__ import annotations

import random

from monopoly.engine.types import DiceRoll


class Dice:
    """Two six-sided dice with injectable RNG."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def roll(self) -> DiceRoll:
        """Roll two dice and return the result."""
        die1 = self._rng.randint(1, 6)
        die2 = self._rng.randint(1, 6)
        return DiceRoll(die1=die1, die2=die2)
