"""Bank management — money supply, house/hotel inventory, auctions."""

from __future__ import annotations

from dataclasses import dataclass, field


MAX_HOUSES = 32
MAX_HOTELS = 12


@dataclass
class Bank:
    """The Monopoly bank managing houses, hotels, and auctions."""

    houses_available: int = MAX_HOUSES
    hotels_available: int = MAX_HOTELS

    def buy_house(self) -> bool:
        """Buy a house from the bank. Returns False if none available."""
        if self.houses_available <= 0:
            return False
        self.houses_available -= 1
        return True

    def return_house(self) -> None:
        """Return a house to the bank."""
        self.houses_available = min(self.houses_available + 1, MAX_HOUSES)

    def buy_hotel(self) -> bool:
        """Buy a hotel from the bank. Returns False if none available."""
        if self.hotels_available <= 0:
            return False
        self.hotels_available -= 1
        return True

    def return_hotel(self) -> None:
        """Return a hotel to the bank."""
        self.hotels_available = min(self.hotels_available + 1, MAX_HOTELS)

    def upgrade_to_hotel(self) -> bool:
        """Upgrade from 4 houses to a hotel: take hotel, return 4 houses.
        Returns False if no hotels available."""
        if self.hotels_available <= 0:
            return False
        self.hotels_available -= 1
        self.houses_available = min(self.houses_available + 4, MAX_HOUSES)
        return True

    def downgrade_from_hotel(self) -> bool:
        """Downgrade a hotel to 4 houses: return hotel, take 4 houses.
        Returns False if not enough houses available."""
        if self.houses_available < 4:
            return False
        self.houses_available -= 4
        self.hotels_available = min(self.hotels_available + 1, MAX_HOTELS)
        return True

    @property
    def has_housing_shortage(self) -> bool:
        """Check if there's a housing shortage."""
        return self.houses_available == 0

    @property
    def has_hotel_shortage(self) -> bool:
        """Check if there's a hotel shortage."""
        return self.hotels_available == 0
