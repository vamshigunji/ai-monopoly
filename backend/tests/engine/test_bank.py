"""Comprehensive tests for the Monopoly Bank — house/hotel inventory management."""

import pytest

from monopoly.engine.bank import Bank, MAX_HOUSES, MAX_HOTELS


# ── Initial state tests ──────────────────────────────────────────────────────


class TestBankInitialState:
    """Tests for the Bank's initial inventory."""

    def test_bank_starts_with_32_houses(self):
        """A new bank must have exactly 32 houses."""
        bank = Bank()
        assert bank.houses_available == 32

    def test_bank_starts_with_12_hotels(self):
        """A new bank must have exactly 12 hotels."""
        bank = Bank()
        assert bank.hotels_available == 12

    def test_max_houses_constant(self):
        """MAX_HOUSES should be 32."""
        assert MAX_HOUSES == 32

    def test_max_hotels_constant(self):
        """MAX_HOTELS should be 12."""
        assert MAX_HOTELS == 12

    def test_no_housing_shortage_initially(self):
        """A fresh bank should NOT have a housing shortage."""
        bank = Bank()
        assert bank.has_housing_shortage is False

    def test_no_hotel_shortage_initially(self):
        """A fresh bank should NOT have a hotel shortage."""
        bank = Bank()
        assert bank.has_hotel_shortage is False


# ── House buying tests ───────────────────────────────────────────────────────


class TestBuyHouse:
    """Tests for buying houses from the bank."""

    def test_buy_house_returns_true(self):
        """buy_house returns True when houses are available."""
        bank = Bank()
        assert bank.buy_house() is True

    def test_buy_house_decrements_count(self):
        """Buying a house decrements houses_available by 1."""
        bank = Bank()
        bank.buy_house()
        assert bank.houses_available == 31

    def test_buy_multiple_houses(self):
        """Buying multiple houses decrements count correctly."""
        bank = Bank()
        for _ in range(5):
            bank.buy_house()
        assert bank.houses_available == 27

    def test_buy_house_returns_false_when_none_available(self):
        """buy_house returns False when all houses are sold."""
        bank = Bank()
        bank.houses_available = 0
        assert bank.buy_house() is False

    def test_buy_house_does_not_change_count_when_none_available(self):
        """When no houses remain, buy_house doesn't go negative."""
        bank = Bank()
        bank.houses_available = 0
        bank.buy_house()
        assert bank.houses_available == 0

    def test_buy_all_32_houses(self):
        """Can buy all 32 houses, then the next attempt fails."""
        bank = Bank()
        for i in range(32):
            assert bank.buy_house() is True, f"Failed buying house #{i + 1}"
        assert bank.houses_available == 0
        assert bank.buy_house() is False

    def test_housing_shortage_after_buying_all(self):
        """has_housing_shortage is True after buying all houses."""
        bank = Bank()
        for _ in range(32):
            bank.buy_house()
        assert bank.has_housing_shortage is True


# ── House returning tests ────────────────────────────────────────────────────


class TestReturnHouse:
    """Tests for returning houses to the bank."""

    def test_return_house_increments_count(self):
        """Returning a house increments houses_available by 1."""
        bank = Bank()
        bank.buy_house()
        bank.return_house()
        assert bank.houses_available == 32

    def test_return_house_does_not_exceed_max(self):
        """Returning houses cannot push count above MAX_HOUSES."""
        bank = Bank()
        bank.return_house()  # Already at max
        assert bank.houses_available == MAX_HOUSES

    def test_return_multiple_houses(self):
        """Can return multiple houses after buying them."""
        bank = Bank()
        for _ in range(10):
            bank.buy_house()
        assert bank.houses_available == 22
        for _ in range(10):
            bank.return_house()
        assert bank.houses_available == 32

    def test_return_house_clears_shortage(self):
        """Returning a house clears the housing shortage."""
        bank = Bank()
        bank.houses_available = 0
        assert bank.has_housing_shortage is True
        bank.return_house()
        assert bank.has_housing_shortage is False


# ── Hotel buying tests ───────────────────────────────────────────────────────


class TestBuyHotel:
    """Tests for buying hotels from the bank."""

    def test_buy_hotel_returns_true(self):
        """buy_hotel returns True when hotels are available."""
        bank = Bank()
        assert bank.buy_hotel() is True

    def test_buy_hotel_decrements_count(self):
        """Buying a hotel decrements hotels_available by 1."""
        bank = Bank()
        bank.buy_hotel()
        assert bank.hotels_available == 11

    def test_buy_hotel_returns_false_when_none_available(self):
        """buy_hotel returns False when all hotels are sold."""
        bank = Bank()
        bank.hotels_available = 0
        assert bank.buy_hotel() is False

    def test_buy_hotel_does_not_change_count_when_none_available(self):
        """When no hotels remain, buy_hotel doesn't go negative."""
        bank = Bank()
        bank.hotels_available = 0
        bank.buy_hotel()
        assert bank.hotels_available == 0

    def test_buy_all_12_hotels(self):
        """Can buy all 12 hotels, then the next attempt fails."""
        bank = Bank()
        for i in range(12):
            assert bank.buy_hotel() is True, f"Failed buying hotel #{i + 1}"
        assert bank.hotels_available == 0
        assert bank.buy_hotel() is False

    def test_hotel_shortage_after_buying_all(self):
        """has_hotel_shortage is True after buying all hotels."""
        bank = Bank()
        for _ in range(12):
            bank.buy_hotel()
        assert bank.has_hotel_shortage is True

    def test_buy_hotel_does_not_affect_houses(self):
        """Buying a hotel directly does not change house count."""
        bank = Bank()
        bank.buy_hotel()
        assert bank.houses_available == 32


# ── Hotel returning tests ────────────────────────────────────────────────────


class TestReturnHotel:
    """Tests for returning hotels to the bank."""

    def test_return_hotel_increments_count(self):
        """Returning a hotel increments hotels_available by 1."""
        bank = Bank()
        bank.buy_hotel()
        bank.return_hotel()
        assert bank.hotels_available == 12

    def test_return_hotel_does_not_exceed_max(self):
        """Returning hotels cannot push count above MAX_HOTELS."""
        bank = Bank()
        bank.return_hotel()  # Already at max
        assert bank.hotels_available == MAX_HOTELS


# ── Upgrade to hotel tests ───────────────────────────────────────────────────


class TestUpgradeToHotel:
    """Tests for upgrading from 4 houses to a hotel."""

    def test_upgrade_to_hotel_returns_true(self):
        """upgrade_to_hotel returns True when hotels are available."""
        bank = Bank()
        assert bank.upgrade_to_hotel() is True

    def test_upgrade_to_hotel_decrements_hotel_count(self):
        """Upgrading takes 1 hotel from inventory."""
        bank = Bank()
        bank.upgrade_to_hotel()
        assert bank.hotels_available == 11

    def test_upgrade_to_hotel_returns_4_houses(self):
        """Upgrading returns 4 houses to the bank."""
        bank = Bank()
        # First buy 4 houses so the math is clear
        for _ in range(4):
            bank.buy_house()
        assert bank.houses_available == 28
        bank.upgrade_to_hotel()
        assert bank.houses_available == 32  # 28 + 4 returned

    def test_upgrade_to_hotel_fails_when_no_hotels(self):
        """upgrade_to_hotel returns False when no hotels available."""
        bank = Bank()
        bank.hotels_available = 0
        assert bank.upgrade_to_hotel() is False

    def test_upgrade_fails_no_side_effects(self):
        """When upgrade fails, neither houses nor hotels change."""
        bank = Bank()
        bank.hotels_available = 0
        original_houses = bank.houses_available
        bank.upgrade_to_hotel()
        assert bank.houses_available == original_houses
        assert bank.hotels_available == 0

    def test_upgrade_houses_capped_at_max(self):
        """Returned houses from upgrade cannot exceed MAX_HOUSES."""
        bank = Bank()
        # Full house inventory, upgrading still caps at 32
        bank.upgrade_to_hotel()
        assert bank.houses_available == MAX_HOUSES

    def test_multiple_upgrades(self):
        """Can perform multiple upgrades in sequence."""
        bank = Bank()
        # Buy 8 houses (for 2 upgrades)
        for _ in range(8):
            bank.buy_house()
        assert bank.houses_available == 24

        bank.upgrade_to_hotel()
        assert bank.houses_available == 28  # 24 + 4
        assert bank.hotels_available == 11

        bank.upgrade_to_hotel()
        assert bank.houses_available == 32  # 28 + 4 (capped at 32)
        assert bank.hotels_available == 10


# ── Downgrade from hotel tests ───────────────────────────────────────────────


class TestDowngradeFromHotel:
    """Tests for downgrading a hotel back to 4 houses."""

    def test_downgrade_from_hotel_returns_true(self):
        """downgrade_from_hotel returns True when at least 4 houses available."""
        bank = Bank()
        assert bank.downgrade_from_hotel() is True

    def test_downgrade_takes_4_houses(self):
        """Downgrading removes 4 houses from inventory."""
        bank = Bank()
        bank.downgrade_from_hotel()
        assert bank.houses_available == 28

    def test_downgrade_returns_1_hotel(self):
        """Downgrading returns 1 hotel to inventory."""
        bank = Bank()
        bank.buy_hotel()
        assert bank.hotels_available == 11
        bank.downgrade_from_hotel()
        assert bank.hotels_available == 12

    def test_downgrade_fails_when_not_enough_houses(self):
        """downgrade_from_hotel returns False when fewer than 4 houses available."""
        bank = Bank()
        bank.houses_available = 3
        assert bank.downgrade_from_hotel() is False

    def test_downgrade_fails_with_zero_houses(self):
        """downgrade_from_hotel returns False when 0 houses available."""
        bank = Bank()
        bank.houses_available = 0
        assert bank.downgrade_from_hotel() is False

    def test_downgrade_fails_no_side_effects(self):
        """When downgrade fails, neither houses nor hotels change."""
        bank = Bank()
        bank.houses_available = 2
        original_hotels = bank.hotels_available
        bank.downgrade_from_hotel()
        assert bank.houses_available == 2
        assert bank.hotels_available == original_hotels

    def test_downgrade_with_exactly_4_houses(self):
        """Downgrade succeeds with exactly 4 houses available."""
        bank = Bank()
        bank.houses_available = 4
        assert bank.downgrade_from_hotel() is True
        assert bank.houses_available == 0
        assert bank.hotels_available == MAX_HOTELS  # capped at max (12)

    def test_downgrade_hotel_capped_at_max(self):
        """Returned hotels from downgrade cannot exceed MAX_HOTELS."""
        bank = Bank()
        # hotels already at max
        bank.downgrade_from_hotel()
        assert bank.hotels_available == MAX_HOTELS

    def test_multiple_downgrades(self):
        """Can perform multiple downgrades in sequence if enough houses."""
        bank = Bank()
        # Buy 2 hotels first
        bank.buy_hotel()
        bank.buy_hotel()
        assert bank.hotels_available == 10

        bank.downgrade_from_hotel()
        assert bank.houses_available == 28
        assert bank.hotels_available == 11

        bank.downgrade_from_hotel()
        assert bank.houses_available == 24
        assert bank.hotels_available == 12


# ── Shortage property tests ──────────────────────────────────────────────────


class TestShortageProperties:
    """Tests for housing and hotel shortage detection."""

    def test_has_housing_shortage_true_at_zero(self):
        """has_housing_shortage is True when houses_available is 0."""
        bank = Bank()
        bank.houses_available = 0
        assert bank.has_housing_shortage is True

    def test_has_housing_shortage_false_at_one(self):
        """has_housing_shortage is False when even 1 house is available."""
        bank = Bank()
        bank.houses_available = 1
        assert bank.has_housing_shortage is False

    def test_has_hotel_shortage_true_at_zero(self):
        """has_hotel_shortage is True when hotels_available is 0."""
        bank = Bank()
        bank.hotels_available = 0
        assert bank.has_hotel_shortage is True

    def test_has_hotel_shortage_false_at_one(self):
        """has_hotel_shortage is False when even 1 hotel is available."""
        bank = Bank()
        bank.hotels_available = 1
        assert bank.has_hotel_shortage is False


# ── Round-trip / integration-style tests ─────────────────────────────────────


class TestBankRoundTrips:
    """Test realistic sequences of bank operations."""

    def test_buy_houses_then_upgrade_then_downgrade(self):
        """Full lifecycle: buy 4 houses -> upgrade to hotel -> downgrade back."""
        bank = Bank()
        for _ in range(4):
            assert bank.buy_house() is True
        assert bank.houses_available == 28

        assert bank.upgrade_to_hotel() is True
        assert bank.houses_available == 32  # 28 + 4 returned (capped at 32)
        assert bank.hotels_available == 11

        assert bank.downgrade_from_hotel() is True
        assert bank.houses_available == 28
        assert bank.hotels_available == 12

    def test_exhaust_houses_blocks_downgrade(self):
        """If all houses are sold, downgrading a hotel is impossible."""
        bank = Bank()
        # Sell all 32 houses
        for _ in range(32):
            bank.buy_house()
        assert bank.houses_available == 0

        # Cannot downgrade because no houses available
        assert bank.downgrade_from_hotel() is False

    def test_custom_initial_inventory(self):
        """Bank can be created with custom initial inventory via dataclass."""
        bank = Bank(houses_available=10, hotels_available=3)
        assert bank.houses_available == 10
        assert bank.hotels_available == 3
