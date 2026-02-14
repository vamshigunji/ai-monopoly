"""Comprehensive tests for Monopoly rule enforcement — rent, building, mortgage, trade."""

import pytest

from monopoly.engine.bank import Bank
from monopoly.engine.board import (
    Board,
    COLOR_GROUP_POSITIONS,
    PROPERTIES,
    RAILROAD_RENTS,
    RAILROADS,
    UTILITIES,
    UTILITY_MULTIPLIERS,
)
from monopoly.engine.player import Player
from monopoly.engine.rules import Rules
from monopoly.engine.types import ColorGroup, DiceRoll, TradeProposal


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def board():
    return Board()


@pytest.fixture
def rules(board):
    return Rules(board)


@pytest.fixture
def bank():
    return Bank()


def _make_player(pid: int = 0, name: str = "TestPlayer", cash: int = 1500) -> Player:
    """Create a player with optional custom cash."""
    return Player(player_id=pid, name=name, cash=cash)


def _give_monopoly(player: Player, color_group: ColorGroup) -> None:
    """Give the player all properties in a color group."""
    for pos in COLOR_GROUP_POSITIONS[color_group]:
        player.add_property(pos)


# ── Rent calculation: standard properties ────────────────────────────────────


class TestPropertyRent:
    """Tests for rent calculation on colored properties."""

    def test_unimproved_property_rent(self, rules):
        """Rent on unimproved property without monopoly equals base rent."""
        owner = _make_player()
        # Owner has Mediterranean (pos 1) but NOT Baltic (pos 3) => no monopoly
        owner.add_property(1)
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[0]  # $2

    def test_monopoly_doubles_base_rent(self, rules):
        """Owning all properties in a color group doubles the unimproved rent."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)  # positions 1, 3
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[0] * 2  # $2 * 2 = $4

    def test_rent_with_1_house(self, rules):
        """Rent with 1 house uses the 1-house tier from the rent table."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)
        owner.set_houses(1, 1)
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[1]  # $10

    def test_rent_with_2_houses(self, rules):
        """Rent with 2 houses uses the 2-house tier from the rent table."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)
        owner.set_houses(1, 2)
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[2]  # $30

    def test_rent_with_3_houses(self, rules):
        """Rent with 3 houses uses the 3-house tier from the rent table."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)
        owner.set_houses(1, 3)
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[3]  # $90

    def test_rent_with_4_houses(self, rules):
        """Rent with 4 houses uses the 4-house tier from the rent table."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)
        owner.set_houses(1, 4)
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[4]  # $160

    def test_rent_with_hotel(self, rules):
        """Rent with a hotel (5 houses) uses the hotel tier from the rent table."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)
        owner.set_houses(1, 5)
        rent = rules.calculate_rent(1, owner)
        assert rent == PROPERTIES[1].rent[5]  # $250

    def test_rent_on_mortgaged_property_is_zero(self, rules):
        """No rent is charged on a mortgaged property."""
        owner = _make_player()
        owner.add_property(1)
        owner.mortgage_property(1)
        rent = rules.calculate_rent(1, owner)
        assert rent == 0

    def test_rent_on_mortgaged_property_with_monopoly_is_zero(self, rules):
        """No rent even if the owner has a monopoly but the property is mortgaged."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.BROWN)
        owner.mortgage_property(1)
        rent = rules.calculate_rent(1, owner)
        assert rent == 0

    @pytest.mark.parametrize("color_group, position", [
        (ColorGroup.LIGHT_BLUE, 6),
        (ColorGroup.PINK, 11),
        (ColorGroup.ORANGE, 16),
        (ColorGroup.RED, 21),
        (ColorGroup.YELLOW, 26),
        (ColorGroup.GREEN, 31),
        (ColorGroup.DARK_BLUE, 37),
    ])
    def test_monopoly_rent_for_each_color_group(self, rules, color_group, position):
        """Monopoly doubles rent for every color group."""
        owner = _make_player()
        _give_monopoly(owner, color_group)
        rent = rules.calculate_rent(position, owner)
        expected = PROPERTIES[position].rent[0] * 2
        assert rent == expected

    def test_boardwalk_hotel_rent(self, rules):
        """Boardwalk with a hotel charges $2000."""
        owner = _make_player()
        _give_monopoly(owner, ColorGroup.DARK_BLUE)
        owner.set_houses(39, 5)
        rent = rules.calculate_rent(39, owner)
        assert rent == 2000


# ── Rent calculation: railroads ──────────────────────────────────────────────


class TestRailroadRent:
    """Tests for railroad rent calculation based on number owned."""

    def test_railroad_rent_1_owned(self, rules):
        """Rent is $25 when owner has 1 railroad."""
        owner = _make_player()
        owner.add_property(5)
        rent = rules.calculate_rent(5, owner)
        assert rent == 25

    def test_railroad_rent_2_owned(self, rules):
        """Rent is $50 when owner has 2 railroads."""
        owner = _make_player()
        owner.add_property(5)
        owner.add_property(15)
        rent = rules.calculate_rent(5, owner)
        assert rent == 50

    def test_railroad_rent_3_owned(self, rules):
        """Rent is $100 when owner has 3 railroads."""
        owner = _make_player()
        owner.add_property(5)
        owner.add_property(15)
        owner.add_property(25)
        rent = rules.calculate_rent(5, owner)
        assert rent == 100

    def test_railroad_rent_4_owned(self, rules):
        """Rent is $200 when owner has all 4 railroads."""
        owner = _make_player()
        for pos in RAILROADS:
            owner.add_property(pos)
        rent = rules.calculate_rent(5, owner)
        assert rent == 200

    def test_railroad_rent_matches_table(self, rules):
        """Railroad rents match the RAILROAD_RENTS table exactly."""
        rr_positions = sorted(RAILROADS.keys())
        owner = _make_player()
        for i, pos in enumerate(rr_positions, start=1):
            owner.add_property(pos)
            rent = rules.calculate_rent(pos, owner)
            assert rent == RAILROAD_RENTS[i]

    def test_mortgaged_railroad_not_counted_for_rent(self, rules):
        """A mortgaged railroad does not count toward the railroad rent multiplier."""
        owner = _make_player()
        owner.add_property(5)
        owner.add_property(15)
        owner.mortgage_property(15)
        # Only 1 unmortgaged railroad
        rent = rules.calculate_rent(5, owner)
        assert rent == 25

    def test_mortgaged_railroad_charges_zero_rent(self, rules):
        """Landing on a mortgaged railroad charges $0."""
        owner = _make_player()
        owner.add_property(5)
        owner.mortgage_property(5)
        rent = rules.calculate_rent(5, owner)
        assert rent == 0


# ── Rent calculation: utilities ──────────────────────────────────────────────


class TestUtilityRent:
    """Tests for utility rent calculation (dice-based)."""

    def test_utility_rent_1_owned_4x_multiplier(self, rules):
        """With 1 utility owned, rent = dice_total * 4."""
        owner = _make_player()
        owner.add_property(12)  # Electric Company
        dice = DiceRoll(3, 4)  # total = 7
        rent = rules.calculate_rent(12, owner, dice)
        assert rent == 7 * 4

    def test_utility_rent_2_owned_10x_multiplier(self, rules):
        """With 2 utilities owned, rent = dice_total * 10."""
        owner = _make_player()
        owner.add_property(12)
        owner.add_property(28)
        dice = DiceRoll(5, 6)  # total = 11
        rent = rules.calculate_rent(12, owner, dice)
        assert rent == 11 * 10

    def test_utility_rent_requires_dice_roll(self, rules):
        """Calculating utility rent without a dice_roll raises ValueError."""
        owner = _make_player()
        owner.add_property(12)
        with pytest.raises(ValueError, match="Dice roll required"):
            rules.calculate_rent(12, owner, dice_roll=None)

    def test_utility_rent_mortgaged_is_zero(self, rules):
        """Mortgaged utility charges no rent."""
        owner = _make_player()
        owner.add_property(12)
        owner.mortgage_property(12)
        rent = rules.calculate_rent(12, owner, DiceRoll(3, 3))
        assert rent == 0

    def test_utility_rent_with_one_mortgaged_counts_only_unmortgaged(self, rules):
        """If one of two utilities is mortgaged, only the unmortgaged one counts (4x)."""
        owner = _make_player()
        owner.add_property(12)
        owner.add_property(28)
        owner.mortgage_property(28)
        dice = DiceRoll(2, 5)  # total = 7
        rent = rules.calculate_rent(12, owner, dice)
        assert rent == 7 * 4  # only 1 unmortgaged

    @pytest.mark.parametrize("d1, d2", [
        (1, 1), (2, 3), (6, 6), (4, 5),
    ])
    def test_utility_rent_various_dice_rolls(self, rules, d1, d2):
        """Utility rent scales linearly with dice total."""
        owner = _make_player()
        owner.add_property(12)
        dice = DiceRoll(d1, d2)
        rent = rules.calculate_rent(12, owner, dice)
        assert rent == (d1 + d2) * UTILITY_MULTIPLIERS[1]


# ── has_monopoly checks ─────────────────────────────────────────────────────


class TestHasMonopoly:
    """Tests for monopoly detection."""

    def test_has_monopoly_true_when_all_owned(self, rules):
        """has_monopoly returns True when player owns all properties in the color group."""
        player = _make_player()
        _give_monopoly(player, ColorGroup.BROWN)
        assert rules.has_monopoly(player, ColorGroup.BROWN) is True

    def test_has_monopoly_false_when_one_missing(self, rules):
        """has_monopoly returns False when one property is missing."""
        player = _make_player()
        player.add_property(1)  # Mediterranean but not Baltic
        assert rules.has_monopoly(player, ColorGroup.BROWN) is False

    def test_has_monopoly_false_with_no_properties(self, rules):
        """has_monopoly is False when player owns nothing."""
        player = _make_player()
        assert rules.has_monopoly(player, ColorGroup.BROWN) is False

    @pytest.mark.parametrize("color_group", list(ColorGroup))
    def test_has_monopoly_for_each_group(self, rules, color_group):
        """has_monopoly works correctly for all color groups."""
        player = _make_player()
        _give_monopoly(player, color_group)
        assert rules.has_monopoly(player, color_group) is True

    def test_owning_properties_in_different_group_not_monopoly(self, rules):
        """Owning properties from different groups doesn't count as a monopoly."""
        player = _make_player()
        player.add_property(1)   # Brown
        player.add_property(6)   # Light blue
        assert rules.has_monopoly(player, ColorGroup.BROWN) is False
        assert rules.has_monopoly(player, ColorGroup.LIGHT_BLUE) is False


# ── Building rules: can_build_house ──────────────────────────────────────────


class TestCanBuildHouse:
    """Tests for house building eligibility."""

    def test_can_build_house_with_monopoly(self, rules, bank):
        """Can build on a property when player has monopoly, cash, and bank has houses."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        assert rules.can_build_house(player, 1, bank) is True

    def test_cannot_build_house_without_monopoly(self, rules, bank):
        """Cannot build without owning the complete color group."""
        player = _make_player(cash=5000)
        player.add_property(1)  # only Mediterranean, not Baltic
        assert rules.can_build_house(player, 1, bank) is False

    def test_cannot_build_on_non_property(self, rules, bank):
        """Cannot build on a railroad, utility, or special space."""
        player = _make_player(cash=5000)
        player.add_property(5)  # Reading Railroad
        assert rules.can_build_house(player, 5, bank) is False

    def test_cannot_build_when_mortgaged_in_group(self, rules, bank):
        """Cannot build when any property in the color group is mortgaged."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.mortgage_property(3)  # mortgage Baltic
        assert rules.can_build_house(player, 1, bank) is False

    def test_cannot_build_without_enough_cash(self, rules, bank):
        """Cannot build when player doesn't have enough cash for the house cost."""
        player = _make_player(cash=10)  # house cost for Brown is $50
        _give_monopoly(player, ColorGroup.BROWN)
        assert rules.can_build_house(player, 1, bank) is False

    def test_cannot_build_when_bank_has_no_houses(self, rules):
        """Cannot build when the bank has no houses available."""
        bank = Bank(houses_available=0)
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        assert rules.can_build_house(player, 1, bank) is False

    def test_even_build_rule_prevents_uneven_construction(self, rules, bank):
        """Even build rule: cannot build if this property already has more houses than a sibling."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        # Build 1 house on Mediterranean but 0 on Baltic
        player.set_houses(1, 1)
        # Cannot build another on Mediterranean because Baltic has 0
        assert rules.can_build_house(player, 1, bank) is False
        # CAN build on Baltic (it's behind)
        assert rules.can_build_house(player, 3, bank) is True

    def test_even_build_three_property_group(self, rules, bank):
        """Even build works correctly for 3-property groups (e.g., light blue)."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.LIGHT_BLUE)  # 6, 8, 9

        # All at 0: can build on any
        assert rules.can_build_house(player, 6, bank) is True
        assert rules.can_build_house(player, 8, bank) is True
        assert rules.can_build_house(player, 9, bank) is True

        # Build on pos 6 => 6 has 1, others have 0
        player.set_houses(6, 1)
        assert rules.can_build_house(player, 6, bank) is False  # ahead
        assert rules.can_build_house(player, 8, bank) is True   # behind
        assert rules.can_build_house(player, 9, bank) is True   # behind

    def test_cannot_build_5th_house(self, rules, bank):
        """Cannot build a 5th house (that requires a hotel upgrade, different method)."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 4)
        player.set_houses(3, 4)
        assert rules.can_build_house(player, 1, bank) is False

    def test_cannot_build_on_property_with_hotel(self, rules, bank):
        """Cannot build on a property that already has a hotel (5)."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 5)
        player.set_houses(3, 5)
        assert rules.can_build_house(player, 1, bank) is False


# ── Building rules: can_build_hotel ──────────────────────────────────────────


class TestCanBuildHotel:
    """Tests for hotel building eligibility."""

    def test_can_build_hotel_with_4_houses(self, rules, bank):
        """Can build a hotel when property has 4 houses and all siblings have >= 4."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 4)
        player.set_houses(3, 4)
        assert rules.can_build_hotel(player, 1, bank) is True

    def test_cannot_build_hotel_without_4_houses(self, rules, bank):
        """Cannot build a hotel if the property has fewer than 4 houses."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 3)
        player.set_houses(3, 4)
        assert rules.can_build_hotel(player, 1, bank) is False

    def test_cannot_build_hotel_without_monopoly(self, rules, bank):
        """Cannot build a hotel without owning the full color group."""
        player = _make_player(cash=5000)
        player.add_property(1)
        player.set_houses(1, 4)
        assert rules.can_build_hotel(player, 1, bank) is False

    def test_cannot_build_hotel_when_sibling_has_fewer_than_4(self, rules, bank):
        """Even build: cannot build hotel if a sibling has fewer than 4 houses."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 4)
        player.set_houses(3, 3)
        assert rules.can_build_hotel(player, 1, bank) is False

    def test_cannot_build_hotel_without_enough_cash(self, rules, bank):
        """Cannot build a hotel when player lacks cash for house_cost."""
        player = _make_player(cash=10)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 4)
        player.set_houses(3, 4)
        assert rules.can_build_hotel(player, 1, bank) is False

    def test_cannot_build_hotel_when_bank_has_none(self, rules):
        """Cannot build a hotel when bank has no hotels."""
        bank = Bank(hotels_available=0)
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 4)
        player.set_houses(3, 4)
        assert rules.can_build_hotel(player, 1, bank) is False

    def test_cannot_build_hotel_on_non_property(self, rules, bank):
        """Cannot build a hotel on a railroad or utility."""
        player = _make_player(cash=5000)
        assert rules.can_build_hotel(player, 5, bank) is False

    def test_cannot_build_hotel_when_mortgaged_in_group(self, rules, bank):
        """Cannot build hotel if any property in group is mortgaged."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 4)
        player.set_houses(3, 4)
        player.mortgage_property(3)
        assert rules.can_build_hotel(player, 1, bank) is False

    def test_can_build_hotel_three_property_group(self, rules, bank):
        """Can build hotel in a 3-property group when all have 4 houses."""
        player = _make_player(cash=5000)
        _give_monopoly(player, ColorGroup.LIGHT_BLUE)
        player.set_houses(6, 4)
        player.set_houses(8, 4)
        player.set_houses(9, 4)
        assert rules.can_build_hotel(player, 6, bank) is True
        assert rules.can_build_hotel(player, 8, bank) is True
        assert rules.can_build_hotel(player, 9, bank) is True


# ── Mortgage rules ───────────────────────────────────────────────────────────


class TestMortgageRules:
    """Tests for mortgage and unmortgage eligibility."""

    def test_can_mortgage_owned_unimproved_property(self, rules):
        """Can mortgage an owned property with no buildings."""
        player = _make_player()
        player.add_property(1)
        assert rules.can_mortgage(player, 1) is True

    def test_cannot_mortgage_unowned_property(self, rules):
        """Cannot mortgage a property the player doesn't own."""
        player = _make_player()
        assert rules.can_mortgage(player, 1) is False

    def test_cannot_mortgage_already_mortgaged(self, rules):
        """Cannot mortgage a property that is already mortgaged."""
        player = _make_player()
        player.add_property(1)
        player.mortgage_property(1)
        assert rules.can_mortgage(player, 1) is False

    def test_cannot_mortgage_if_buildings_exist_in_group(self, rules):
        """Cannot mortgage if ANY property in the color group has buildings."""
        player = _make_player()
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(3, 1)  # Baltic has 1 house
        # Cannot mortgage Mediterranean because Baltic has buildings
        assert rules.can_mortgage(player, 1) is False
        # Cannot mortgage Baltic either (itself has buildings)
        assert rules.can_mortgage(player, 3) is False

    def test_can_mortgage_railroad(self, rules):
        """Can mortgage a railroad."""
        player = _make_player()
        player.add_property(5)
        assert rules.can_mortgage(player, 5) is True

    def test_can_mortgage_utility(self, rules):
        """Can mortgage a utility."""
        player = _make_player()
        player.add_property(12)
        assert rules.can_mortgage(player, 12) is True

    def test_can_unmortgage_with_enough_cash(self, rules):
        """Can unmortgage when player has enough cash (mortgage_value * 1.1)."""
        player = _make_player(cash=5000)
        player.add_property(1)
        player.mortgage_property(1)
        assert rules.can_unmortgage(player, 1) is True

    def test_cannot_unmortgage_without_enough_cash(self, rules):
        """Cannot unmortgage when cash is less than mortgage_value * 1.1."""
        player = _make_player(cash=0)
        player.add_property(1)
        player.mortgage_property(1)
        assert rules.can_unmortgage(player, 1) is False

    def test_cannot_unmortgage_if_not_mortgaged(self, rules):
        """Cannot unmortgage a property that is not mortgaged."""
        player = _make_player(cash=5000)
        player.add_property(1)
        assert rules.can_unmortgage(player, 1) is False

    def test_cannot_unmortgage_unowned_property(self, rules):
        """Cannot unmortgage a property the player doesn't own."""
        player = _make_player(cash=5000)
        assert rules.can_unmortgage(player, 1) is False

    def test_unmortgage_cost_is_110_percent_of_mortgage_value(self, rules):
        """Unmortgage cost is exactly int(mortgage_value * 1.1)."""
        # Mediterranean: mortgage_value = 30 => cost = int(30 * 1.1) = 33
        cost = rules.unmortgage_cost(1)
        assert cost == int(30 * 1.1)  # 33

    def test_unmortgage_cost_for_railroad(self, rules):
        """Unmortgage cost for a railroad with mortgage_value=100 is int(100*1.1)=110."""
        cost = rules.unmortgage_cost(5)
        assert cost == int(100 * 1.1)

    def test_unmortgage_cost_for_utility(self, rules):
        """Unmortgage cost for a utility with mortgage_value=75 is int(75*1.1)=82."""
        cost = rules.unmortgage_cost(12)
        assert cost == int(75 * 1.1)

    def test_unmortgage_cost_boundary_cash(self, rules):
        """Player with exactly enough cash can unmortgage."""
        cost = rules.unmortgage_cost(1)  # 33
        player = _make_player(cash=cost)
        player.add_property(1)
        player.mortgage_property(1)
        assert rules.can_unmortgage(player, 1) is True

    def test_unmortgage_cost_one_short(self, rules):
        """Player with 1 less than the cost cannot unmortgage."""
        cost = rules.unmortgage_cost(1)  # 33
        player = _make_player(cash=cost - 1)
        player.add_property(1)
        player.mortgage_property(1)
        assert rules.can_unmortgage(player, 1) is False


# ── Mortgage value accessor ──────────────────────────────────────────────────


class TestGetMortgageValue:
    """Tests for get_mortgage_value public accessor."""

    def test_property_mortgage_value(self, rules):
        """get_mortgage_value returns correct value for a property."""
        assert rules.get_mortgage_value(1) == 30  # Mediterranean

    def test_railroad_mortgage_value(self, rules):
        """get_mortgage_value returns correct value for a railroad."""
        assert rules.get_mortgage_value(5) == 100

    def test_utility_mortgage_value(self, rules):
        """get_mortgage_value returns correct value for a utility."""
        assert rules.get_mortgage_value(12) == 75

    def test_non_ownable_space_mortgage_value(self, rules):
        """get_mortgage_value returns 0 for non-ownable spaces."""
        assert rules.get_mortgage_value(0) == 0   # GO
        assert rules.get_mortgage_value(10) == 0  # Jail
        assert rules.get_mortgage_value(20) == 0  # Free Parking
        assert rules.get_mortgage_value(30) == 0  # Go To Jail


# ── Trade validation ─────────────────────────────────────────────────────────


class TestTradeValidation:
    """Tests for trade proposal validation."""

    def test_valid_property_trade(self, rules):
        """A simple property-for-property trade is valid."""
        proposer = _make_player(pid=0, cash=500)
        receiver = _make_player(pid=1, cash=500)
        proposer.add_property(1)
        receiver.add_property(3)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[1],
            requested_properties=[3],
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is True
        assert reason == ""

    def test_trade_invalid_proposer_doesnt_own_property(self, rules):
        """Trade is invalid if proposer doesn't own the offered property."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1)
        receiver.add_property(3)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[1],  # proposer doesn't own this
            requested_properties=[3],
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Proposer doesn't own" in reason

    def test_trade_invalid_receiver_doesnt_own_property(self, rules):
        """Trade is invalid if receiver doesn't own the requested property."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1)
        proposer.add_property(1)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[1],
            requested_properties=[3],  # receiver doesn't own this
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Receiver doesn't own" in reason

    def test_trade_invalid_proposer_not_enough_cash(self, rules):
        """Trade is invalid if proposer offers more cash than they have."""
        proposer = _make_player(pid=0, cash=100)
        receiver = _make_player(pid=1)
        receiver.add_property(1)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_cash=500,
            requested_properties=[1],
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Proposer doesn't have enough cash" in reason

    def test_trade_invalid_receiver_not_enough_cash(self, rules):
        """Trade is invalid if the receiver can't cover the requested cash."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1, cash=50)
        proposer.add_property(1)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[1],
            requested_cash=500,
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Receiver doesn't have enough cash" in reason

    def test_trade_invalid_proposer_not_enough_jail_cards(self, rules):
        """Trade is invalid if proposer offers more jail cards than they have."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1)
        proposer.get_out_of_jail_cards = 0

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_jail_cards=1,
            requested_cash=50,
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Proposer doesn't have enough Get Out of Jail" in reason

    def test_trade_invalid_receiver_not_enough_jail_cards(self, rules):
        """Trade is invalid if the receiver can't provide requested jail cards."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1)
        receiver.get_out_of_jail_cards = 0

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_cash=50,
            requested_jail_cards=1,
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Receiver doesn't have enough Get Out of Jail" in reason

    def test_trade_valid_with_jail_cards(self, rules):
        """A trade involving jail cards is valid when both sides can cover them."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1)
        proposer.get_out_of_jail_cards = 1
        receiver.get_out_of_jail_cards = 1

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_jail_cards=1,
            requested_jail_cards=1,
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is True

    def test_trade_invalid_cannot_trade_property_with_buildings(self, rules):
        """Cannot trade a property that has buildings on it."""
        proposer = _make_player(pid=0, cash=5000)
        receiver = _make_player(pid=1, cash=5000)
        _give_monopoly(proposer, ColorGroup.BROWN)
        proposer.set_houses(1, 2)  # 2 houses on Mediterranean
        receiver.add_property(6)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[1],
            requested_properties=[6],
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Must sell buildings" in reason

    def test_trade_invalid_receiver_property_with_buildings(self, rules):
        """Cannot trade a receiver's property that has buildings on it."""
        proposer = _make_player(pid=0, cash=5000)
        receiver = _make_player(pid=1, cash=5000)
        _give_monopoly(receiver, ColorGroup.BROWN)
        receiver.set_houses(1, 1)
        proposer.add_property(6)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[6],
            requested_properties=[1],
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "Must sell buildings" in reason

    def test_trade_must_involve_something(self, rules):
        """A completely empty trade is invalid."""
        proposer = _make_player(pid=0)
        receiver = _make_player(pid=1)

        trade = TradeProposal(proposer_id=0, receiver_id=1)
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is False
        assert "must involve at least one item" in reason.lower()

    def test_trade_cash_only_is_valid(self, rules):
        """A cash-for-cash trade (while unusual) is valid if amounts are set."""
        proposer = _make_player(pid=0, cash=500)
        receiver = _make_player(pid=1, cash=500)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_cash=100,
            requested_cash=200,
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is True

    def test_trade_property_for_cash(self, rules):
        """Trading a property for cash is valid."""
        proposer = _make_player(pid=0, cash=500)
        receiver = _make_player(pid=1, cash=500)
        proposer.add_property(1)

        trade = TradeProposal(
            proposer_id=0,
            receiver_id=1,
            offered_properties=[1],
            requested_cash=200,
        )
        valid, reason = rules.validate_trade(trade, proposer, receiver)
        assert valid is True


# ── Mortgage transfer fee ────────────────────────────────────────────────────


class TestMortgageTransferFee:
    """Tests for the 10% mortgage transfer fee when trading mortgaged properties."""

    def test_transfer_fee_is_10_percent_of_mortgage_value(self, rules):
        """Mortgage transfer fee is int(mortgage_value * 0.1)."""
        # Mediterranean mortgage_value = 30 => fee = int(30 * 0.1) = 3
        fee = rules.mortgage_transfer_fee(1)
        assert fee == int(30 * 0.1)

    def test_transfer_fee_for_railroad(self, rules):
        """Transfer fee for railroad with mortgage_value=100 is 10."""
        fee = rules.mortgage_transfer_fee(5)
        assert fee == 10

    def test_transfer_fee_for_utility(self, rules):
        """Transfer fee for utility with mortgage_value=75 is int(75*0.1)=7."""
        fee = rules.mortgage_transfer_fee(12)
        assert fee == int(75 * 0.1)

    def test_transfer_fee_for_boardwalk(self, rules):
        """Transfer fee for Boardwalk with mortgage_value=200 is 20."""
        fee = rules.mortgage_transfer_fee(39)
        assert fee == 20

    def test_transfer_fee_for_non_ownable_space_is_zero(self, rules):
        """Transfer fee for a non-ownable space is 0 (mortgage_value is 0)."""
        fee = rules.mortgage_transfer_fee(0)  # GO
        assert fee == 0

    @pytest.mark.parametrize("position, expected_mv", [
        (1, 30),    # Mediterranean
        (39, 200),  # Boardwalk
        (5, 100),   # Reading Railroad
        (12, 75),   # Electric Company
    ])
    def test_transfer_fee_parametrized(self, rules, position, expected_mv):
        """Transfer fee is always exactly 10% of the mortgage value."""
        fee = rules.mortgage_transfer_fee(position)
        assert fee == int(expected_mv * 0.1)


# ── Buying rules ─────────────────────────────────────────────────────────────


class TestCanBuyProperty:
    """Tests for the can_buy_property rule."""

    def test_can_buy_with_enough_cash(self, rules):
        """Player with enough cash can buy an unowned property."""
        player = _make_player(cash=500)
        assert rules.can_buy_property(player, 1) is True  # Mediterranean costs $60

    def test_cannot_buy_without_enough_cash(self, rules):
        """Player without enough cash cannot buy."""
        player = _make_player(cash=10)
        assert rules.can_buy_property(player, 1) is False

    def test_cannot_buy_non_purchasable_space(self, rules):
        """Cannot buy GO, Jail, Free Parking, etc."""
        player = _make_player(cash=50000)
        assert rules.can_buy_property(player, 0) is False   # GO
        assert rules.can_buy_property(player, 10) is False  # Jail
        assert rules.can_buy_property(player, 20) is False  # Free Parking
        assert rules.can_buy_property(player, 30) is False  # Go To Jail

    def test_can_buy_railroad(self, rules):
        """Can buy a railroad with enough cash ($200)."""
        player = _make_player(cash=200)
        assert rules.can_buy_property(player, 5) is True

    def test_can_buy_utility(self, rules):
        """Can buy a utility with enough cash ($150)."""
        player = _make_player(cash=150)
        assert rules.can_buy_property(player, 12) is True

    def test_cannot_buy_tax_space(self, rules):
        """Cannot buy a tax space."""
        player = _make_player(cash=50000)
        assert rules.can_buy_property(player, 4) is False   # Income Tax
        assert rules.can_buy_property(player, 38) is False  # Luxury Tax

    def test_can_buy_with_exact_cash(self, rules):
        """Player with exactly the purchase price can buy."""
        player = _make_player(cash=60)  # Mediterranean costs $60
        assert rules.can_buy_property(player, 1) is True


# ── Can sell house tests ─────────────────────────────────────────────────────


class TestCanSellHouse:
    """Tests for the even sell-back rule."""

    def test_can_sell_house_from_property_with_houses(self, rules):
        """Can sell a house from a property that has houses."""
        player = _make_player()
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 1)
        player.set_houses(3, 1)
        assert rules.can_sell_house(player, 1) is True

    def test_cannot_sell_house_from_empty_property(self, rules):
        """Cannot sell a house from a property with 0 houses."""
        player = _make_player()
        _give_monopoly(player, ColorGroup.BROWN)
        assert rules.can_sell_house(player, 1) is False

    def test_cannot_sell_house_from_hotel_property(self, rules):
        """Cannot sell a house from a property with a hotel (must downgrade first)."""
        player = _make_player()
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 5)
        assert rules.can_sell_house(player, 1) is False

    def test_even_sell_rule(self, rules):
        """Even sell rule: can't sell if this property has fewer houses than a sibling."""
        player = _make_player()
        _give_monopoly(player, ColorGroup.BROWN)
        player.set_houses(1, 1)
        player.set_houses(3, 2)
        # Can't sell from Mediterranean (1 house) when Baltic has 2
        assert rules.can_sell_house(player, 1) is False
        # CAN sell from Baltic (highest)
        assert rules.can_sell_house(player, 3) is True

    def test_cannot_sell_house_on_non_property(self, rules):
        """Cannot sell a house from a railroad."""
        player = _make_player()
        player.add_property(5)
        assert rules.can_sell_house(player, 5) is False
