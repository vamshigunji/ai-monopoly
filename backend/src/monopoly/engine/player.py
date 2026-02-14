"""Player state management for Monopoly."""

from __future__ import annotations

from dataclasses import dataclass, field


STARTING_CASH = 1500


@dataclass
class Player:
    """A Monopoly player's mutable state."""

    player_id: int
    name: str
    position: int = 0
    cash: int = STARTING_CASH
    properties: list[int] = field(default_factory=list)     # positions of owned properties
    houses: dict[int, int] = field(default_factory=dict)    # position -> house count (0-5, 5=hotel)
    mortgaged: set[int] = field(default_factory=set)        # positions of mortgaged properties
    in_jail: bool = False
    jail_turns: int = 0
    get_out_of_jail_cards: int = 0
    is_bankrupt: bool = False
    consecutive_doubles: int = 0

    def add_cash(self, amount: int) -> None:
        """Add cash to the player."""
        self.cash += amount

    def remove_cash(self, amount: int) -> bool:
        """Remove cash from the player. Returns False if insufficient funds."""
        if self.cash < amount:
            return False
        self.cash -= amount
        return True

    def add_property(self, position: int) -> None:
        """Add a property to the player's portfolio."""
        if position not in self.properties:
            self.properties.append(position)

    def remove_property(self, position: int) -> None:
        """Remove a property from the player's portfolio."""
        if position in self.properties:
            self.properties.remove(position)
        self.mortgaged.discard(position)
        self.houses.pop(position, None)

    def owns_property(self, position: int) -> bool:
        """Check if the player owns a property at a given position."""
        return position in self.properties

    def mortgage_property(self, position: int) -> None:
        """Mark a property as mortgaged."""
        self.mortgaged.add(position)

    def unmortgage_property(self, position: int) -> None:
        """Mark a property as unmortgaged."""
        self.mortgaged.discard(position)

    def is_mortgaged(self, position: int) -> bool:
        """Check if a property is mortgaged."""
        return position in self.mortgaged

    def get_house_count(self, position: int) -> int:
        """Get the number of houses on a property (5 = hotel)."""
        return self.houses.get(position, 0)

    def set_houses(self, position: int, count: int) -> None:
        """Set the house count on a property."""
        if count == 0:
            self.houses.pop(position, None)
        else:
            self.houses[position] = count

    def send_to_jail(self) -> None:
        """Send player to jail."""
        self.position = 10  # Jail position
        self.in_jail = True
        self.jail_turns = 0
        self.consecutive_doubles = 0

    def release_from_jail(self) -> None:
        """Release player from jail."""
        self.in_jail = False
        self.jail_turns = 0

    def move_to(self, position: int) -> bool:
        """Move player to a position. Returns True if passed GO."""
        old_position = self.position
        self.position = position % 40
        # Check if passed GO (moved forward past position 0)
        return self.position < old_position and self.position != old_position

    def move_forward(self, spaces: int) -> bool:
        """Move player forward by a number of spaces. Returns True if passed GO."""
        old_position = self.position
        self.position = (self.position + spaces) % 40
        return self.position < old_position

    def net_worth(self, board) -> int:
        """Calculate total net worth (cash + property values + building values)."""
        from monopoly.engine.board import PROPERTIES, RAILROADS, UTILITIES

        total = self.cash
        for pos in self.properties:
            if pos in PROPERTIES:
                prop = PROPERTIES[pos]
                if pos in self.mortgaged:
                    total += prop.mortgage_value
                else:
                    total += prop.price
                houses = self.get_house_count(pos)
                if houses == 5:  # hotel
                    total += prop.house_cost * 5  # 4 houses + 1 hotel cost
                else:
                    total += prop.house_cost * houses
            elif pos in RAILROADS:
                rr = RAILROADS[pos]
                total += rr.mortgage_value if pos in self.mortgaged else rr.price
            elif pos in UTILITIES:
                util = UTILITIES[pos]
                total += util.mortgage_value if pos in self.mortgaged else util.price
        return total
