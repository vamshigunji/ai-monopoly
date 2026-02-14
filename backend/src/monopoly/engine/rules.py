"""Rule enforcement for Monopoly — building, rent, mortgage, trade validation."""

from __future__ import annotations

from monopoly.engine.board import (
    Board,
    COLOR_GROUP_POSITIONS,
    PROPERTIES,
    RAILROAD_RENTS,
    RAILROADS,
    UTILITIES,
    UTILITY_MULTIPLIERS,
)
from monopoly.engine.bank import Bank
from monopoly.engine.player import Player
from monopoly.engine.types import DiceRoll, SpaceType, TradeProposal


class Rules:
    """Stateless rule enforcement for Monopoly."""

    def __init__(self, board: Board) -> None:
        self.board = board

    # ── Rent calculation ────────────────────────────────────────────────

    def calculate_rent(
        self, position: int, owner: Player, dice_roll: DiceRoll | None = None
    ) -> int:
        """Calculate rent owed for landing on an owned property."""
        if owner.is_mortgaged(position):
            return 0

        space = self.board.get_space(position)

        if space.space_type == SpaceType.PROPERTY:
            return self._property_rent(position, owner)
        elif space.space_type == SpaceType.RAILROAD:
            return self._railroad_rent(owner)
        elif space.space_type == SpaceType.UTILITY:
            if dice_roll is None:
                raise ValueError("Dice roll required for utility rent calculation")
            return self._utility_rent(owner, dice_roll)
        return 0

    def _property_rent(self, position: int, owner: Player) -> int:
        """Calculate rent for a standard property."""
        prop = PROPERTIES[position]
        houses = owner.get_house_count(position)

        if houses > 0:
            # rent tuple: (base, 1h, 2h, 3h, 4h, hotel)
            return prop.rent[houses]  # index 1-5

        # Unimproved: check for monopoly (double rent)
        if self.has_monopoly(owner, prop.color_group):
            return prop.rent[0] * 2
        return prop.rent[0]

    def _railroad_rent(self, owner: Player) -> int:
        """Calculate rent for a railroad based on how many the owner has."""
        count = sum(1 for pos in RAILROADS if owner.owns_property(pos)
                    and not owner.is_mortgaged(pos))
        return RAILROAD_RENTS.get(count, 0)

    def _utility_rent(self, owner: Player, dice_roll: DiceRoll) -> int:
        """Calculate rent for a utility based on dice roll and count owned."""
        count = sum(1 for pos in UTILITIES if owner.owns_property(pos)
                    and not owner.is_mortgaged(pos))
        multiplier = UTILITY_MULTIPLIERS.get(count, 0)
        return dice_roll.total * multiplier

    # ── Monopoly checks ────────────────────────────────────────────────

    def has_monopoly(self, player: Player, color_group) -> bool:
        """Check if a player owns all properties in a color group."""
        positions = COLOR_GROUP_POSITIONS[color_group]
        return all(player.owns_property(pos) for pos in positions)

    # ── Building rules ──────────────────────────────────────────────────

    def can_build_house(self, player: Player, position: int, bank: Bank) -> bool:
        """Check if a player can build a house on a property."""
        if position not in PROPERTIES:
            return False
        prop = PROPERTIES[position]

        # Must own full color group
        if not self.has_monopoly(player, prop.color_group):
            return False

        # No property in group can be mortgaged
        group_positions = COLOR_GROUP_POSITIONS[prop.color_group]
        if any(player.is_mortgaged(pos) for pos in group_positions):
            return False

        # Current house count
        current = player.get_house_count(position)
        if current >= 5:  # already has hotel
            return False

        # Even build rule: can't build if this property already has
        # more houses than any other in the group
        if current >= 4:  # need hotel upgrade, not another house
            return False

        for pos in group_positions:
            if pos != position and player.get_house_count(pos) < current:
                return False

        # Must have enough cash
        if player.cash < prop.house_cost:
            return False

        # Bank must have houses available
        if current < 4 and not bank.houses_available:
            return False

        return True

    def can_build_hotel(self, player: Player, position: int, bank: Bank) -> bool:
        """Check if a player can build a hotel on a property."""
        if position not in PROPERTIES:
            return False
        prop = PROPERTIES[position]

        if not self.has_monopoly(player, prop.color_group):
            return False

        group_positions = COLOR_GROUP_POSITIONS[prop.color_group]
        if any(player.is_mortgaged(pos) for pos in group_positions):
            return False

        current = player.get_house_count(position)
        if current != 4:
            return False

        # Even build: all others must also have 4 houses or a hotel
        for pos in group_positions:
            if pos != position and player.get_house_count(pos) < 4:
                return False

        if player.cash < prop.house_cost:
            return False

        if not bank.hotels_available:
            return False

        return True

    def can_sell_house(self, player: Player, position: int) -> bool:
        """Check if a player can sell a house from a property (even sell-back)."""
        if position not in PROPERTIES:
            return False
        prop = PROPERTIES[position]
        current = player.get_house_count(position)

        if current <= 0 or current == 5:
            # Can't sell house from empty or hotel (must downgrade hotel first)
            return False

        # Even sell: can't sell if this property has fewer houses than others in group
        group_positions = COLOR_GROUP_POSITIONS[prop.color_group]
        for pos in group_positions:
            if pos != position and player.get_house_count(pos) > current:
                return False

        return True

    def can_sell_hotel(self, player: Player, position: int, bank: Bank) -> bool:
        """Check if a player can sell/downgrade a hotel."""
        if position not in PROPERTIES:
            return False
        current = player.get_house_count(position)
        if current != 5:
            return False

        # Need 4 houses available to downgrade
        # (or sell everything if no houses available)
        return True  # Can always sell a hotel (might need to sell down to 0)

    # ── Mortgage rules ──────────────────────────────────────────────────

    def can_mortgage(self, player: Player, position: int) -> bool:
        """Check if a player can mortgage a property."""
        if not player.owns_property(position):
            return False
        if player.is_mortgaged(position):
            return False

        # If it's a colored property, no buildings allowed on ANY property in the group
        if position in PROPERTIES:
            prop = PROPERTIES[position]
            group_positions = COLOR_GROUP_POSITIONS[prop.color_group]
            for pos in group_positions:
                if player.get_house_count(pos) > 0:
                    return False

        return True

    def can_unmortgage(self, player: Player, position: int) -> bool:
        """Check if a player can unmortgage a property."""
        if not player.owns_property(position):
            return False
        if not player.is_mortgaged(position):
            return False

        # Calculate unmortgage cost (mortgage value + 10% interest)
        cost = self.unmortgage_cost(position)
        return player.cash >= cost

    def unmortgage_cost(self, position: int) -> int:
        """Calculate the cost to unmortgage a property."""
        mortgage_value = self._get_mortgage_value(position)
        return int(mortgage_value * 1.1)

    def _get_mortgage_value(self, position: int) -> int:
        """Get the mortgage value for a position."""
        if position in PROPERTIES:
            return PROPERTIES[position].mortgage_value
        if position in RAILROADS:
            return RAILROADS[position].mortgage_value
        if position in UTILITIES:
            return UTILITIES[position].mortgage_value
        return 0

    def get_mortgage_value(self, position: int) -> int:
        """Public accessor for mortgage value."""
        return self._get_mortgage_value(position)

    # ── Buying rules ────────────────────────────────────────────────────

    def can_buy_property(self, player: Player, position: int) -> bool:
        """Check if a player can buy a property at its listed price."""
        if not self.board.is_purchasable(position):
            return False
        price = self.board.get_purchase_price(position)
        return player.cash >= price

    # ── Trade validation ────────────────────────────────────────────────

    def validate_trade(
        self, proposal: TradeProposal, proposer: Player, receiver: Player
    ) -> tuple[bool, str]:
        """Validate a trade proposal. Returns (is_valid, reason)."""
        # Check proposer owns offered properties
        for pos in proposal.offered_properties:
            if not proposer.owns_property(pos):
                return False, f"Proposer doesn't own property at position {pos}"
            # Can't trade properties with buildings
            if proposer.get_house_count(pos) > 0:
                return False, f"Must sell buildings before trading property at position {pos}"

        # Check receiver owns requested properties
        for pos in proposal.requested_properties:
            if not receiver.owns_property(pos):
                return False, f"Receiver doesn't own property at position {pos}"
            if receiver.get_house_count(pos) > 0:
                return False, f"Must sell buildings before trading property at position {pos}"

        # Check cash
        if proposal.offered_cash > 0 and proposer.cash < proposal.offered_cash:
            return False, "Proposer doesn't have enough cash"
        if proposal.requested_cash > 0 and receiver.cash < proposal.requested_cash:
            return False, "Receiver doesn't have enough cash"

        # Check jail cards
        if proposal.offered_jail_cards > proposer.get_out_of_jail_cards:
            return False, "Proposer doesn't have enough Get Out of Jail Free cards"
        if proposal.requested_jail_cards > receiver.get_out_of_jail_cards:
            return False, "Receiver doesn't have enough Get Out of Jail Free cards"

        # Must trade something
        if (not proposal.offered_properties and not proposal.requested_properties
                and proposal.offered_cash == 0 and proposal.requested_cash == 0
                and proposal.offered_jail_cards == 0 and proposal.requested_jail_cards == 0):
            return False, "Trade must involve at least one item"

        return True, ""

    def mortgage_transfer_fee(self, position: int) -> int:
        """Calculate the 10% transfer fee when trading a mortgaged property."""
        mortgage_value = self._get_mortgage_value(position)
        return int(mortgage_value * 0.1)
