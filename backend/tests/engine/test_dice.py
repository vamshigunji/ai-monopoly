"""Comprehensive tests for the Monopoly dice module."""

import pytest

from monopoly.engine.dice import Dice
from monopoly.engine.types import DiceRoll


# ===========================================================================
# 1. Basic roll validity
# ===========================================================================

class TestDiceRollValidity:
    """Each die must return a value between 1 and 6."""

    def test_single_roll_die1_in_range(self):
        dice = Dice(seed=42)
        roll = dice.roll()
        assert 1 <= roll.die1 <= 6

    def test_single_roll_die2_in_range(self):
        dice = Dice(seed=42)
        roll = dice.roll()
        assert 1 <= roll.die2 <= 6

    def test_many_rolls_die1_always_in_range(self):
        dice = Dice(seed=99)
        for _ in range(1000):
            roll = dice.roll()
            assert 1 <= roll.die1 <= 6

    def test_many_rolls_die2_always_in_range(self):
        dice = Dice(seed=99)
        for _ in range(1000):
            roll = dice.roll()
            assert 1 <= roll.die2 <= 6

    def test_roll_returns_diceroll_type(self):
        dice = Dice(seed=1)
        roll = dice.roll()
        assert isinstance(roll, DiceRoll)

    def test_die_values_are_integers(self):
        dice = Dice(seed=1)
        roll = dice.roll()
        assert isinstance(roll.die1, int)
        assert isinstance(roll.die2, int)


# ===========================================================================
# 2. Total calculation
# ===========================================================================

class TestDiceTotal:
    """DiceRoll.total must be the sum of die1 and die2."""

    def test_total_is_sum(self):
        dice = Dice(seed=42)
        roll = dice.roll()
        assert roll.total == roll.die1 + roll.die2

    def test_total_minimum_is_2(self):
        """The minimum total is 2 (snake eyes)."""
        dice = Dice(seed=0)
        for _ in range(1000):
            roll = dice.roll()
            assert roll.total >= 2

    def test_total_maximum_is_12(self):
        """The maximum total is 12 (double sixes)."""
        dice = Dice(seed=0)
        for _ in range(1000):
            roll = dice.roll()
            assert roll.total <= 12

    def test_total_range_over_many_rolls(self):
        """Over many rolls we should see totals from 2 to 12."""
        dice = Dice(seed=123)
        totals = set()
        for _ in range(10000):
            roll = dice.roll()
            totals.add(roll.total)
        assert totals == set(range(2, 13))

    def test_total_with_known_values(self):
        roll = DiceRoll(die1=3, die2=4)
        assert roll.total == 7

    def test_total_snake_eyes(self):
        roll = DiceRoll(die1=1, die2=1)
        assert roll.total == 2

    def test_total_boxcars(self):
        roll = DiceRoll(die1=6, die2=6)
        assert roll.total == 12


# ===========================================================================
# 3. Doubles detection
# ===========================================================================

class TestDoublesDetection:
    """DiceRoll.is_doubles must detect when both dice show the same value."""

    def test_doubles_when_equal(self):
        roll = DiceRoll(die1=3, die2=3)
        assert roll.is_doubles is True

    def test_not_doubles_when_different(self):
        roll = DiceRoll(die1=3, die2=4)
        assert roll.is_doubles is False

    @pytest.mark.parametrize("value", [1, 2, 3, 4, 5, 6])
    def test_all_possible_doubles(self, value):
        roll = DiceRoll(die1=value, die2=value)
        assert roll.is_doubles is True

    @pytest.mark.parametrize(
        "die1, die2",
        [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (1, 6), (2, 5), (3, 6)],
    )
    def test_various_non_doubles(self, die1, die2):
        roll = DiceRoll(die1=die1, die2=die2)
        assert roll.is_doubles is False

    def test_doubles_occur_in_many_rolls(self):
        """Over many rolls, doubles should occur roughly 1/6 of the time."""
        dice = Dice(seed=42)
        doubles_count = sum(
            1 for _ in range(6000) if dice.roll().is_doubles
        )
        # Expect ~1000; allow generous range for randomness
        assert 700 < doubles_count < 1300


# ===========================================================================
# 4. Deterministic seed reproducibility
# ===========================================================================

class TestDeterministicSeed:
    """Using the same seed must produce identical sequences of rolls."""

    def test_same_seed_same_first_roll(self):
        dice_a = Dice(seed=42)
        dice_b = Dice(seed=42)
        assert dice_a.roll() == dice_b.roll()

    def test_same_seed_same_sequence(self):
        dice_a = Dice(seed=42)
        dice_b = Dice(seed=42)
        for _ in range(100):
            assert dice_a.roll() == dice_b.roll()

    def test_same_seed_full_sequence_equality(self):
        dice_a = Dice(seed=12345)
        dice_b = Dice(seed=12345)
        rolls_a = [dice_a.roll() for _ in range(50)]
        rolls_b = [dice_b.roll() for _ in range(50)]
        assert rolls_a == rolls_b

    def test_seed_zero_is_deterministic(self):
        dice_a = Dice(seed=0)
        dice_b = Dice(seed=0)
        rolls_a = [dice_a.roll() for _ in range(20)]
        rolls_b = [dice_b.roll() for _ in range(20)]
        assert rolls_a == rolls_b

    def test_large_seed_is_deterministic(self):
        dice_a = Dice(seed=2**31 - 1)
        dice_b = Dice(seed=2**31 - 1)
        rolls_a = [dice_a.roll() for _ in range(20)]
        rolls_b = [dice_b.roll() for _ in range(20)]
        assert rolls_a == rolls_b


# ===========================================================================
# 5. Different seeds produce different results
# ===========================================================================

class TestDifferentSeeds:
    """Different seeds should (almost certainly) produce different sequences."""

    def test_different_seeds_different_first_roll(self):
        """Two different seeds are very unlikely to produce the same first roll.
        We check a few pairs to be robust."""
        different_found = False
        for seed_a, seed_b in [(1, 2), (42, 43), (100, 200), (0, 999)]:
            dice_a = Dice(seed=seed_a)
            dice_b = Dice(seed=seed_b)
            if dice_a.roll() != dice_b.roll():
                different_found = True
                break
        assert different_found, "All seed pairs produced identical first rolls"

    def test_different_seeds_different_sequence(self):
        dice_a = Dice(seed=42)
        dice_b = Dice(seed=43)
        rolls_a = [dice_a.roll() for _ in range(20)]
        rolls_b = [dice_b.roll() for _ in range(20)]
        assert rolls_a != rolls_b

    def test_many_different_seeds_produce_variety(self):
        """Roll once with 100 different seeds; we should get multiple distinct results."""
        results = set()
        for seed in range(100):
            dice = Dice(seed=seed)
            roll = dice.roll()
            results.add((roll.die1, roll.die2))
        # With 100 seeds and 36 possible outcomes, we should see many distinct results
        assert len(results) > 10


# ===========================================================================
# 6. Multiple rolls with same seed are reproducible
# ===========================================================================

class TestMultipleRollsReproducibility:
    """Reproducing multiple rolls from the same starting seed."""

    def test_10th_roll_is_reproducible(self):
        """The 10th roll from seed=42 should always be the same."""
        def get_10th_roll(seed):
            dice = Dice(seed=seed)
            for _ in range(9):
                dice.roll()
            return dice.roll()

        roll_a = get_10th_roll(42)
        roll_b = get_10th_roll(42)
        assert roll_a == roll_b

    def test_100th_roll_is_reproducible(self):
        def get_nth_roll(seed, n):
            dice = Dice(seed=seed)
            for _ in range(n - 1):
                dice.roll()
            return dice.roll()

        roll_a = get_nth_roll(42, 100)
        roll_b = get_nth_roll(42, 100)
        assert roll_a == roll_b

    def test_interleaved_rolls_are_independent(self):
        """Two Dice objects with the same seed produce the same sequence
        even when interleaved differently."""
        dice_a = Dice(seed=7)
        dice_b = Dice(seed=7)

        # Roll dice_a 5 times
        rolls_a = [dice_a.roll() for _ in range(5)]

        # Roll dice_b 3 times, skip, then continue
        rolls_b_part1 = [dice_b.roll() for _ in range(3)]
        rolls_b_part2 = [dice_b.roll() for _ in range(2)]

        assert rolls_a[:3] == rolls_b_part1
        assert rolls_a[3:] == rolls_b_part2


# ===========================================================================
# 7. No-seed (non-deterministic) mode
# ===========================================================================

class TestNonDeterministicMode:
    """Dice created without a seed should still produce valid rolls."""

    def test_no_seed_rolls_are_valid(self):
        dice = Dice()  # No seed
        for _ in range(100):
            roll = dice.roll()
            assert 1 <= roll.die1 <= 6
            assert 1 <= roll.die2 <= 6
            assert roll.total == roll.die1 + roll.die2

    def test_no_seed_produces_variety(self):
        """Without a seed, rolls should not all be identical."""
        dice = Dice()
        rolls = [dice.roll() for _ in range(100)]
        distinct = set((r.die1, r.die2) for r in rolls)
        assert len(distinct) > 1


# ===========================================================================
# 8. DiceRoll dataclass properties
# ===========================================================================

class TestDiceRollDataclass:
    """DiceRoll is a frozen dataclass with expected behavior."""

    def test_diceroll_is_frozen(self):
        roll = DiceRoll(die1=3, die2=4)
        with pytest.raises(AttributeError):
            roll.die1 = 5  # type: ignore[misc]

    def test_diceroll_equality(self):
        roll_a = DiceRoll(die1=3, die2=4)
        roll_b = DiceRoll(die1=3, die2=4)
        assert roll_a == roll_b

    def test_diceroll_inequality(self):
        roll_a = DiceRoll(die1=3, die2=4)
        roll_b = DiceRoll(die1=4, die2=3)
        assert roll_a != roll_b

    def test_diceroll_hash_consistency(self):
        roll_a = DiceRoll(die1=2, die2=5)
        roll_b = DiceRoll(die1=2, die2=5)
        assert hash(roll_a) == hash(roll_b)
