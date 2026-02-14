"""Comprehensive tests for the Monopoly Game engine.

Every test creates its own Game / Player / Board instances directly
instead of relying on conftest fixtures, for maximum clarity and isolation.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from monopoly.engine.bank import Bank
from monopoly.engine.board import (
    Board,
    COLOR_GROUP_POSITIONS,
    PROPERTIES,
    RAILROADS,
    UTILITIES,
)
from monopoly.engine.game import Game, GO_SALARY, JAIL_FINE, MAX_JAIL_TURNS
from monopoly.engine.player import Player, STARTING_CASH
from monopoly.engine.types import (
    DiceRoll,
    EventType,
    GamePhase,
    JailAction,
    SpaceType,
    TradeProposal,
    TurnPhase,
    ColorGroup,
)


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _make_game(num_players: int = 4, seed: int = 42) -> Game:
    """Create a deterministic game."""
    return Game(num_players=num_players, seed=seed)


def _events_of_type(game: Game, event_type: EventType) -> list:
    """Return all events of a given type."""
    return [e for e in game.events if e.event_type == event_type]


def _give_monopoly(game: Game, player: Player, color: ColorGroup) -> None:
    """Give a player all properties of a color group."""
    for pos in COLOR_GROUP_POSITIONS[color]:
        game.assign_property(player, pos)


# ────────────────────────────────────────────────────────────────────────────
# 1. Initialization
# ────────────────────────────────────────────────────────────────────────────

class TestGameInitialization:
    """Tests for game startup conditions."""

    def test_game_creates_correct_number_of_players(self):
        for n in (2, 3, 4, 6):
            game = Game(num_players=n, seed=0)
            assert len(game.players) == n

    def test_all_players_start_at_position_zero(self):
        game = _make_game()
        for p in game.players:
            assert p.position == 0

    def test_all_players_start_with_1500(self):
        game = _make_game()
        for p in game.players:
            assert p.cash == STARTING_CASH
            assert p.cash == 1500

    def test_no_properties_owned_at_start(self):
        game = _make_game()
        for pos in list(PROPERTIES.keys()) + list(RAILROADS.keys()) + list(UTILITIES.keys()):
            assert game.get_property_owner(pos) is None

    def test_game_starts_in_progress(self):
        game = _make_game()
        assert game.phase == GamePhase.IN_PROGRESS

    def test_turn_starts_at_zero(self):
        game = _make_game()
        assert game.turn_number == 0

    def test_current_player_is_first_player(self):
        game = _make_game()
        assert game.current_player.player_id == 0


# ────────────────────────────────────────────────────────────────────────────
# 2. Property ownership tracking
# ────────────────────────────────────────────────────────────────────────────

class TestPropertyOwnership:
    """Tests for assign, transfer, and unown operations."""

    def test_assign_property(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)  # Mediterranean Avenue
        assert game.get_property_owner(1) is player
        assert game.is_property_owned(1)
        assert player.owns_property(1)

    def test_transfer_property(self):
        game = _make_game()
        p0, p1 = game.players[0], game.players[1]
        game.assign_property(p0, 1)
        game.transfer_property(p0, p1, 1)
        assert game.get_property_owner(1) is p1
        assert not p0.owns_property(1)
        assert p1.owns_property(1)

    def test_unown_property(self):
        game = _make_game()
        p0 = game.players[0]
        game.assign_property(p0, 1)
        game.unown_property(1)
        assert game.get_property_owner(1) is None
        assert not game.is_property_owned(1)

    def test_assign_multiple_properties(self):
        game = _make_game()
        p0 = game.players[0]
        for pos in [1, 3, 6]:
            game.assign_property(p0, pos)
        assert all(game.get_property_owner(pos) is p0 for pos in [1, 3, 6])
        assert len(p0.properties) == 3

    def test_unown_nonexistent_property_is_noop(self):
        game = _make_game()
        game.unown_property(99)  # should not raise

    def test_get_property_owner_returns_none_for_unowned(self):
        game = _make_game()
        assert game.get_property_owner(1) is None


# ────────────────────────────────────────────────────────────────────────────
# 3. Dice rolling
# ────────────────────────────────────────────────────────────────────────────

class TestDiceRolling:
    """Tests for dice rolling producing valid results and events."""

    def test_roll_returns_valid_dice_values(self):
        game = _make_game(seed=0)
        for _ in range(50):
            roll = game.roll_dice()
            assert 1 <= roll.die1 <= 6
            assert 1 <= roll.die2 <= 6
            assert roll.total == roll.die1 + roll.die2

    def test_roll_stores_last_roll(self):
        game = _make_game()
        roll = game.roll_dice()
        assert game.last_roll is roll

    def test_roll_emits_dice_rolled_event(self):
        game = _make_game()
        game.roll_dice()
        events = _events_of_type(game, EventType.DICE_ROLLED)
        assert len(events) == 1
        assert "die1" in events[0].data
        assert "die2" in events[0].data
        assert "total" in events[0].data
        assert "doubles" in events[0].data

    def test_doubles_detected(self):
        roll = DiceRoll(die1=3, die2=3)
        assert roll.is_doubles is True

    def test_non_doubles_detected(self):
        roll = DiceRoll(die1=3, die2=4)
        assert roll.is_doubles is False

    def test_deterministic_seed(self):
        """Same seed produces the same roll sequence."""
        game1 = Game(num_players=2, seed=123)
        game2 = Game(num_players=2, seed=123)
        for _ in range(10):
            r1 = game1.roll_dice()
            r2 = game2.roll_dice()
            assert r1.die1 == r2.die1
            assert r1.die2 == r2.die2


# ────────────────────────────────────────────────────────────────────────────
# 4. Player movement
# ────────────────────────────────────────────────────────────────────────────

class TestPlayerMovement:
    """Tests for move_player (forward) and move_player_to (direct)."""

    def test_forward_movement(self):
        game = _make_game()
        player = game.players[0]
        game.move_player(player, 5)
        assert player.position == 5

    def test_forward_movement_wraps_around(self):
        game = _make_game()
        player = game.players[0]
        player.position = 38
        passed_go = game.move_player(player, 4)
        assert player.position == 2
        assert passed_go is True

    def test_passing_go_collects_200(self):
        game = _make_game()
        player = game.players[0]
        player.position = 38
        game.move_player(player, 4)
        assert player.cash == STARTING_CASH + GO_SALARY

    def test_passing_go_emits_event(self):
        game = _make_game()
        player = game.players[0]
        player.position = 38
        game.move_player(player, 4)
        events = _events_of_type(game, EventType.PASSED_GO)
        assert len(events) == 1
        assert events[0].data["salary"] == GO_SALARY

    def test_not_passing_go_no_salary(self):
        game = _make_game()
        player = game.players[0]
        game.move_player(player, 5)
        assert player.cash == STARTING_CASH

    def test_move_emits_player_moved_event(self):
        game = _make_game()
        player = game.players[0]
        game.move_player(player, 7)
        events = _events_of_type(game, EventType.PLAYER_MOVED)
        assert len(events) == 1
        assert events[0].data["new_position"] == 7

    # ── Direct movement (move_to) ──

    def test_move_to_specific_position(self):
        game = _make_game()
        player = game.players[0]
        player.position = 5
        game.move_player_to(player, 20)
        assert player.position == 20

    def test_move_to_passes_go_collects_salary(self):
        game = _make_game()
        player = game.players[0]
        player.position = 35
        game.move_player_to(player, 5)
        assert player.cash == STARTING_CASH + GO_SALARY

    def test_move_to_passes_go_with_collect_go_false(self):
        game = _make_game()
        player = game.players[0]
        player.position = 35
        game.move_player_to(player, 5, collect_go=False)
        assert player.cash == STARTING_CASH  # no salary

    def test_move_to_same_position_no_go(self):
        game = _make_game()
        player = game.players[0]
        player.position = 10
        game.move_player_to(player, 10)
        assert player.cash == STARTING_CASH


# ────────────────────────────────────────────────────────────────────────────
# 5. Landing on spaces
# ────────────────────────────────────────────────────────────────────────────

class TestLandingOnUnownedProperty:
    """Landing on unowned property should require a buy decision."""

    def test_unowned_property_requires_buy_decision(self):
        game = _make_game()
        player = game.players[0]
        player.position = 1  # Mediterranean Avenue
        result = game.process_landing(player)
        assert result.requires_buy_decision is True
        assert result.rent_owed == 0

    def test_unowned_railroad_requires_buy_decision(self):
        game = _make_game()
        player = game.players[0]
        player.position = 5  # Reading Railroad
        result = game.process_landing(player)
        assert result.requires_buy_decision is True

    def test_unowned_utility_requires_buy_decision(self):
        game = _make_game()
        player = game.players[0]
        player.position = 12  # Electric Company
        result = game.process_landing(player)
        assert result.requires_buy_decision is True


class TestLandingOnOwnedProperty:
    """Landing on owned property should calculate rent."""

    def test_owned_property_charges_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 1)  # Mediterranean: base rent $2
        game.last_roll = DiceRoll(3, 4)

        player = game.players[0]
        player.position = 1
        result = game.process_landing(player)
        assert result.rent_owed == 2
        assert result.rent_to_player == owner.player_id

    def test_owned_railroad_charges_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 5)  # Reading Railroad: 1 RR = $25

        player = game.players[0]
        player.position = 5
        result = game.process_landing(player)
        assert result.rent_owed == 25
        assert result.rent_to_player == owner.player_id

    def test_two_railroads_increase_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 5)
        game.assign_property(owner, 15)

        player = game.players[0]
        player.position = 5
        result = game.process_landing(player)
        assert result.rent_owed == 50  # 2 railroads

    def test_owned_utility_charges_rent_based_on_dice(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 12)  # Electric Company
        game.last_roll = DiceRoll(3, 4)  # total 7

        player = game.players[0]
        player.position = 12
        result = game.process_landing(player)
        # 1 utility owned: multiplier = 4, rent = 7 * 4 = 28
        assert result.rent_owed == 28

    def test_both_utilities_charges_10x(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 12)
        game.assign_property(owner, 28)
        game.last_roll = DiceRoll(3, 4)  # total 7

        player = game.players[0]
        player.position = 12
        result = game.process_landing(player)
        # 2 utilities owned: multiplier = 10, rent = 7 * 10 = 70
        assert result.rent_owed == 70


class TestLandingOnMortgagedProperty:
    """Landing on a mortgaged property should not charge rent."""

    def test_mortgaged_property_no_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 1)
        owner.mortgage_property(1)

        player = game.players[0]
        player.position = 1
        result = game.process_landing(player)
        assert result.rent_owed == 0
        assert result.requires_buy_decision is False

    def test_mortgaged_railroad_no_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 5)
        owner.mortgage_property(5)

        player = game.players[0]
        player.position = 5
        result = game.process_landing(player)
        assert result.rent_owed == 0

    def test_mortgaged_utility_no_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 12)
        owner.mortgage_property(12)
        game.last_roll = DiceRoll(3, 4)

        player = game.players[0]
        player.position = 12
        result = game.process_landing(player)
        assert result.rent_owed == 0


class TestLandingOnOwnProperty:
    """Landing on your own property should not charge rent."""

    def test_own_property_no_rent(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        player.position = 1
        result = game.process_landing(player)
        assert result.rent_owed == 0
        assert result.requires_buy_decision is False

    def test_own_railroad_no_rent(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 5)
        player.position = 5
        result = game.process_landing(player)
        assert result.rent_owed == 0

    def test_own_utility_no_rent(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 12)
        player.position = 12
        game.last_roll = DiceRoll(3, 4)
        result = game.process_landing(player)
        assert result.rent_owed == 0


# ────────────────────────────────────────────────────────────────────────────
# 6. Tax handling
# ────────────────────────────────────────────────────────────────────────────

class TestTaxHandling:
    """Tests for Income Tax and Luxury Tax."""

    def test_income_tax_200(self):
        game = _make_game()
        player = game.players[0]
        player.position = 4  # Income Tax
        result = game.process_landing(player)
        assert result.tax_amount == 200
        assert player.cash == STARTING_CASH - 200

    def test_luxury_tax_100(self):
        game = _make_game()
        player = game.players[0]
        player.position = 38  # Luxury Tax
        result = game.process_landing(player)
        assert result.tax_amount == 100
        assert player.cash == STARTING_CASH - 100

    def test_tax_emits_event(self):
        game = _make_game()
        player = game.players[0]
        player.position = 4
        game.process_landing(player)
        events = _events_of_type(game, EventType.TAX_PAID)
        assert len(events) == 1
        assert events[0].data["amount"] == 200


# ────────────────────────────────────────────────────────────────────────────
# 7. Go To Jail
# ────────────────────────────────────────────────────────────────────────────

class TestGoToJail:
    """Tests for the Go To Jail space."""

    def test_go_to_jail_sends_to_jail(self):
        game = _make_game()
        player = game.players[0]
        player.position = 30  # Go To Jail
        result = game.process_landing(player)
        assert result.sent_to_jail is True
        assert player.in_jail is True
        assert player.position == 10  # Jail position

    def test_go_to_jail_does_not_collect_go(self):
        game = _make_game()
        player = game.players[0]
        player.position = 30
        initial_cash = player.cash
        game.process_landing(player)
        # Player should NOT get $200 for passing GO
        assert player.cash == initial_cash

    def test_go_to_jail_emits_event(self):
        game = _make_game()
        player = game.players[0]
        player.position = 30
        game.process_landing(player)
        events = _events_of_type(game, EventType.PLAYER_JAILED)
        assert len(events) == 1
        assert events[0].player_id == player.player_id


# ────────────────────────────────────────────────────────────────────────────
# 8. Buying property
# ────────────────────────────────────────────────────────────────────────────

class TestBuyingProperty:
    """Tests for buying properties."""

    def test_buy_property_deducts_cash(self):
        game = _make_game()
        player = game.players[0]
        success = game.buy_property(player, 1)  # Mediterranean: $60
        assert success is True
        assert player.cash == STARTING_CASH - 60

    def test_buy_property_assigns_ownership(self):
        game = _make_game()
        player = game.players[0]
        game.buy_property(player, 1)
        assert game.get_property_owner(1) is player
        assert player.owns_property(1)

    def test_buy_railroad(self):
        game = _make_game()
        player = game.players[0]
        success = game.buy_property(player, 5)  # Reading Railroad: $200
        assert success is True
        assert player.cash == STARTING_CASH - 200
        assert game.get_property_owner(5) is player

    def test_buy_utility(self):
        game = _make_game()
        player = game.players[0]
        success = game.buy_property(player, 12)  # Electric Company: $150
        assert success is True
        assert player.cash == STARTING_CASH - 150

    def test_buy_emits_event(self):
        game = _make_game()
        player = game.players[0]
        game.buy_property(player, 1)
        events = _events_of_type(game, EventType.PROPERTY_PURCHASED)
        assert len(events) == 1
        assert events[0].data["position"] == 1
        assert events[0].data["price"] == 60
        assert events[0].player_id == player.player_id

    def test_buy_fails_insufficient_cash(self):
        game = _make_game()
        player = game.players[0]
        player.cash = 50  # less than $60 for Mediterranean
        success = game.buy_property(player, 1)
        assert success is False
        assert player.cash == 50  # unchanged
        assert game.get_property_owner(1) is None

    def test_buy_fails_already_owned(self):
        game = _make_game()
        p0 = game.players[0]
        p1 = game.players[1]
        game.buy_property(p0, 1)
        success = game.buy_property(p1, 1)
        assert success is False
        assert game.get_property_owner(1) is p0  # still owned by p0

    def test_buy_fails_non_purchasable_space(self):
        game = _make_game()
        player = game.players[0]
        success = game.buy_property(player, 0)  # GO -- price is 0
        assert success is False

    def test_buy_multiple_properties(self):
        game = _make_game()
        player = game.players[0]
        game.buy_property(player, 1)   # $60
        game.buy_property(player, 3)   # $60
        assert player.cash == STARTING_CASH - 120
        assert len(player.properties) == 2


# ────────────────────────────────────────────────────────────────────────────
# 9. Auctioning property
# ────────────────────────────────────────────────────────────────────────────

class TestAuction:
    """Tests for property auctions."""

    def test_highest_bidder_wins(self):
        game = _make_game()
        bids = {0: 100, 1: 150, 2: 120}
        winner = game.auction_property(1, bids)
        assert winner == 1
        assert game.get_property_owner(1) is game.players[1]
        assert game.players[1].cash == STARTING_CASH - 150

    def test_no_bids_returns_none(self):
        game = _make_game()
        winner = game.auction_property(1, {})
        assert winner is None
        assert game.get_property_owner(1) is None

    def test_zero_bid_invalid(self):
        game = _make_game()
        bids = {0: 0, 1: 0}
        winner = game.auction_property(1, bids)
        assert winner is None

    def test_bid_exceeding_cash_filtered(self):
        game = _make_game()
        game.players[0].cash = 50
        bids = {0: 200, 1: 100}  # player 0 can't afford 200
        winner = game.auction_property(1, bids)
        assert winner == 1
        assert game.players[1].cash == STARTING_CASH - 100

    def test_bankrupt_player_bid_filtered(self):
        game = _make_game()
        game.players[0].is_bankrupt = True
        bids = {0: 100, 1: 80}
        winner = game.auction_property(1, bids)
        assert winner == 1

    def test_auction_emits_event(self):
        game = _make_game()
        bids = {0: 100}
        game.auction_property(1, bids)
        events = _events_of_type(game, EventType.AUCTION_WON)
        assert len(events) == 1
        assert events[0].data["bid"] == 100

    def test_auction_single_bidder_wins(self):
        game = _make_game()
        bids = {2: 50}
        winner = game.auction_property(3, bids)
        assert winner == 2
        assert game.get_property_owner(3) is game.players[2]


# ────────────────────────────────────────────────────────────────────────────
# 10. Building houses
# ────────────────────────────────────────────────────────────────────────────

class TestBuildingHouses:
    """Tests for building houses on properties."""

    def test_build_house_deducts_cost(self):
        game = _make_game()
        player = game.players[0]
        # Give monopoly on Brown (positions 1, 3) -- house cost $50
        _give_monopoly(game, player, ColorGroup.BROWN)

        success = game.build_house(player, 1)
        assert success is True
        assert player.cash == STARTING_CASH - 50
        assert player.get_house_count(1) == 1

    def test_build_house_increments_count(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)

        game.build_house(player, 1)
        game.build_house(player, 3)  # even build: must build on 3 next
        game.build_house(player, 1)  # now can build second on 1
        assert player.get_house_count(1) == 2
        assert player.get_house_count(3) == 1

    def test_build_house_emits_event(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)

        game.build_house(player, 1)
        events = _events_of_type(game, EventType.HOUSE_BUILT)
        assert len(events) == 1
        assert events[0].data["position"] == 1
        assert events[0].data["houses"] == 1

    def test_build_house_fails_without_monopoly(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)  # only 1 of 2 browns
        success = game.build_house(player, 1)
        assert success is False

    def test_build_house_fails_insufficient_cash(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        player.cash = 10
        success = game.build_house(player, 1)
        assert success is False

    def test_build_house_decrements_bank_supply(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        initial_houses = game.bank.houses_available
        game.build_house(player, 1)
        assert game.bank.houses_available == initial_houses - 1

    def test_build_house_fails_when_bank_out_of_houses(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.bank.houses_available = 0
        success = game.build_house(player, 1)
        assert success is False

    def test_even_build_rule_enforced(self):
        """Cannot build a second house on pos 1 before building on pos 3."""
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)  # 1 house on pos 1
        success = game.build_house(player, 1)  # attempt 2nd on pos 1
        assert success is False
        assert player.get_house_count(1) == 1


# ────────────────────────────────────────────────────────────────────────────
# 11. Building hotels
# ────────────────────────────────────────────────────────────────────────────

class TestBuildingHotels:
    """Tests for building hotels (upgrade from 4 houses)."""

    def _build_up_to_4_houses(self, game: Game, player: Player, color: ColorGroup):
        """Helper to evenly build up 4 houses on all properties in a color group."""
        positions = COLOR_GROUP_POSITIONS[color]
        for _ in range(4):
            for pos in positions:
                game.build_house(player, pos)

    def test_build_hotel_from_4_houses(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_up_to_4_houses(game, player, ColorGroup.BROWN)
        assert player.get_house_count(1) == 4

        success = game.build_hotel(player, 1)
        assert success is True
        assert player.get_house_count(1) == 5  # 5 = hotel

    def test_build_hotel_deducts_house_cost(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_up_to_4_houses(game, player, ColorGroup.BROWN)
        cash_before = player.cash
        game.build_hotel(player, 1)
        # house_cost for brown = 50
        assert player.cash == cash_before - 50

    def test_build_hotel_emits_event(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_up_to_4_houses(game, player, ColorGroup.BROWN)
        game.build_hotel(player, 1)
        events = _events_of_type(game, EventType.HOTEL_BUILT)
        assert len(events) == 1
        assert events[0].data["position"] == 1

    def test_build_hotel_fails_without_4_houses(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        success = game.build_hotel(player, 1)
        assert success is False

    def test_build_hotel_updates_bank_inventory(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_up_to_4_houses(game, player, ColorGroup.BROWN)
        hotels_before = game.bank.hotels_available
        houses_before = game.bank.houses_available
        game.build_hotel(player, 1)
        assert game.bank.hotels_available == hotels_before - 1
        # 4 houses returned to bank
        assert game.bank.houses_available == houses_before + 4


# ────────────────────────────────────────────────────────────────────────────
# 12. Selling houses
# ────────────────────────────────────────────────────────────────────────────

class TestSellingHouses:
    """Tests for selling houses back at half price."""

    def test_sell_house_refunds_half_price(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)

        cash_before = player.cash
        success = game.sell_house(player, 1)
        assert success is True
        # house cost = 50, refund = 25
        assert player.cash == cash_before + 25
        assert player.get_house_count(1) == 0

    def test_sell_house_returns_to_bank(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        houses_before = game.bank.houses_available
        game.sell_house(player, 1)
        assert game.bank.houses_available == houses_before + 1

    def test_sell_house_emits_event(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        game.sell_house(player, 1)
        events = _events_of_type(game, EventType.BUILDING_SOLD)
        assert len(events) == 1
        assert events[0].data["refund"] == 25

    def test_sell_house_fails_on_empty(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        success = game.sell_house(player, 1)
        assert success is False

    def test_sell_house_even_rule(self):
        """Cannot sell house from pos 3 if pos 1 has more houses."""
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        game.build_house(player, 1)  # pos 1: 2 houses, pos 3: 1 house
        # Selling from pos 3 would violate even build (pos 1 has 2 > 0)
        success = game.sell_house(player, 3)
        assert success is False


# ────────────────────────────────────────────────────────────────────────────
# 13. Mortgage / unmortgage
# ────────────────────────────────────────────────────────────────────────────

class TestMortgage:
    """Tests for mortgage and unmortgage flow."""

    def test_mortgage_adds_cash(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)  # mortgage value = 30
        cash_before = player.cash
        success = game.mortgage_property(player, 1)
        assert success is True
        assert player.cash == cash_before + 30
        assert player.is_mortgaged(1) is True

    def test_mortgage_railroad(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 5)  # mortgage value = 100
        success = game.mortgage_property(player, 5)
        assert success is True
        assert player.cash == STARTING_CASH + 100

    def test_mortgage_utility(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 12)  # mortgage value = 75
        success = game.mortgage_property(player, 12)
        assert success is True
        assert player.cash == STARTING_CASH + 75

    def test_mortgage_emits_event(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        game.mortgage_property(player, 1)
        events = _events_of_type(game, EventType.PROPERTY_MORTGAGED)
        assert len(events) == 1
        assert events[0].data["position"] == 1
        assert events[0].data["value"] == 30

    def test_cannot_mortgage_already_mortgaged(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        game.mortgage_property(player, 1)
        success = game.mortgage_property(player, 1)
        assert success is False

    def test_cannot_mortgage_with_buildings_in_group(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        success = game.mortgage_property(player, 3)
        assert success is False

    def test_cannot_mortgage_unowned_property(self):
        game = _make_game()
        player = game.players[0]
        success = game.mortgage_property(player, 1)
        assert success is False

    def test_unmortgage_costs_110_percent(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        game.mortgage_property(player, 1)  # +$30
        cash_before = player.cash
        success = game.unmortgage_property(player, 1)
        assert success is True
        # unmortgage cost = 30 * 1.1 = 33
        assert player.cash == cash_before - 33
        assert player.is_mortgaged(1) is False

    def test_unmortgage_emits_event(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        game.mortgage_property(player, 1)
        game.unmortgage_property(player, 1)
        events = _events_of_type(game, EventType.PROPERTY_UNMORTGAGED)
        assert len(events) == 1
        assert events[0].data["cost"] == 33

    def test_unmortgage_fails_insufficient_cash(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        game.mortgage_property(player, 1)
        player.cash = 10  # less than $33 to unmortgage
        success = game.unmortgage_property(player, 1)
        assert success is False

    def test_unmortgage_fails_not_mortgaged(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        success = game.unmortgage_property(player, 1)
        assert success is False


# ────────────────────────────────────────────────────────────────────────────
# 14. Jail handling
# ────────────────────────────────────────────────────────────────────────────

class TestJailHandling:
    """Tests for jail mechanics: pay fine, use card, roll doubles, forced payment."""

    def test_pay_fine_releases_player(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        assert player.in_jail is True

        game.handle_jail_turn(player, JailAction.PAY_FINE)
        assert player.in_jail is False
        assert player.cash == STARTING_CASH - JAIL_FINE

    def test_pay_fine_emits_freed_event(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        game.handle_jail_turn(player, JailAction.PAY_FINE)
        events = _events_of_type(game, EventType.PLAYER_FREED)
        assert len(events) == 1
        assert events[0].data["method"] == "paid_fine"

    def test_pay_fine_fails_insufficient_cash(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        player.cash = 10  # less than $50
        game.handle_jail_turn(player, JailAction.PAY_FINE)
        assert player.in_jail is True  # still in jail

    def test_use_card_releases_player(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        player.get_out_of_jail_cards = 1

        game.handle_jail_turn(player, JailAction.USE_CARD)
        assert player.in_jail is False
        assert player.get_out_of_jail_cards == 0

    def test_use_card_emits_freed_event(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        player.get_out_of_jail_cards = 1
        game.handle_jail_turn(player, JailAction.USE_CARD)
        events = _events_of_type(game, EventType.PLAYER_FREED)
        assert len(events) == 1
        assert events[0].data["method"] == "used_card"

    def test_use_card_fails_without_card(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        player.get_out_of_jail_cards = 0
        game.handle_jail_turn(player, JailAction.USE_CARD)
        assert player.in_jail is True

    def test_roll_doubles_releases_player(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()

        # Force doubles via mock
        with patch.object(game.dice, "roll", return_value=DiceRoll(3, 3)):
            result = game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)
        assert player.in_jail is False
        assert result is not None
        assert result.is_doubles is True

    def test_roll_non_doubles_stays_in_jail(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()

        with patch.object(game.dice, "roll", return_value=DiceRoll(3, 4)):
            result = game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)
        assert player.in_jail is True
        assert result is None

    def test_forced_payment_after_3_turns(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()

        # Fail rolls twice
        with patch.object(game.dice, "roll", return_value=DiceRoll(3, 4)):
            game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)  # turn 1
            game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)  # turn 2
            result = game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)  # turn 3 -- forced payment

        assert player.in_jail is False
        assert player.cash == STARTING_CASH - JAIL_FINE
        assert result is not None

    def test_forced_payment_emits_freed_event(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()

        with patch.object(game.dice, "roll", return_value=DiceRoll(3, 4)):
            game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)
            game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)
            game.handle_jail_turn(player, JailAction.ROLL_DOUBLES)

        freed_events = _events_of_type(game, EventType.PLAYER_FREED)
        assert len(freed_events) == 1
        assert freed_events[0].data["method"] == "forced_payment"

    def test_handle_jail_turn_noop_if_not_in_jail(self):
        game = _make_game()
        player = game.players[0]
        assert player.in_jail is False
        result = game.handle_jail_turn(player, JailAction.PAY_FINE)
        assert result is None


# ────────────────────────────────────────────────────────────────────────────
# 15. Bankruptcy
# ────────────────────────────────────────────────────────────────────────────

class TestBankruptcy:
    """Tests for bankruptcy to another player and to the bank."""

    def test_bankruptcy_to_player_transfers_properties(self):
        game = _make_game()
        bankrupt = game.players[0]
        creditor = game.players[1]
        game.assign_property(bankrupt, 1)
        game.assign_property(bankrupt, 3)

        game.declare_bankruptcy(bankrupt, creditor_id=creditor.player_id)
        assert bankrupt.is_bankrupt is True
        assert creditor.owns_property(1)
        assert creditor.owns_property(3)
        assert game.get_property_owner(1) is creditor
        assert game.get_property_owner(3) is creditor

    def test_bankruptcy_to_player_transfers_cash(self):
        game = _make_game()
        bankrupt = game.players[0]
        creditor = game.players[1]
        bankrupt.cash = 300
        creditor_cash_before = creditor.cash

        game.declare_bankruptcy(bankrupt, creditor_id=creditor.player_id)
        assert creditor.cash == creditor_cash_before + 300
        assert bankrupt.cash == 0

    def test_bankruptcy_to_player_transfers_jail_cards(self):
        game = _make_game()
        bankrupt = game.players[0]
        creditor = game.players[1]
        bankrupt.get_out_of_jail_cards = 2
        creditor.get_out_of_jail_cards = 1

        game.declare_bankruptcy(bankrupt, creditor_id=creditor.player_id)
        assert creditor.get_out_of_jail_cards == 3
        assert bankrupt.get_out_of_jail_cards == 0

    def test_bankruptcy_to_player_transfers_mortgaged_status(self):
        game = _make_game()
        bankrupt = game.players[0]
        creditor = game.players[1]
        game.assign_property(bankrupt, 1)
        bankrupt.mortgage_property(1)

        game.declare_bankruptcy(bankrupt, creditor_id=creditor.player_id)
        assert creditor.is_mortgaged(1)

    def test_bankruptcy_to_bank_returns_properties(self):
        game = _make_game()
        bankrupt = game.players[0]
        game.assign_property(bankrupt, 1)
        game.assign_property(bankrupt, 3)

        game.declare_bankruptcy(bankrupt, creditor_id=None)
        assert bankrupt.is_bankrupt is True
        assert game.get_property_owner(1) is None
        assert game.get_property_owner(3) is None

    def test_bankruptcy_to_bank_returns_houses(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        houses_in_bank = game.bank.houses_available

        game.declare_bankruptcy(player, creditor_id=None)
        # 2 houses should be returned
        assert game.bank.houses_available == houses_in_bank + 2

    def test_bankruptcy_to_bank_returns_hotels(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        # Build up to hotels on both
        for _ in range(4):
            game.build_house(player, 1)
            game.build_house(player, 3)
        game.build_hotel(player, 1)
        game.build_hotel(player, 3)
        hotels_in_bank = game.bank.hotels_available

        game.declare_bankruptcy(player, creditor_id=None)
        assert game.bank.hotels_available == hotels_in_bank + 2

    def test_bankruptcy_emits_event(self):
        game = _make_game()
        player = game.players[0]
        game.declare_bankruptcy(player, creditor_id=None)
        events = _events_of_type(game, EventType.PLAYER_BANKRUPT)
        assert len(events) == 1
        assert events[0].player_id == player.player_id

    def test_bankruptcy_clears_all_player_state(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 1)
        player.mortgage_property(1)
        player.get_out_of_jail_cards = 2

        game.declare_bankruptcy(player, creditor_id=None)
        assert player.cash == 0
        assert len(player.properties) == 0
        assert len(player.houses) == 0
        assert len(player.mortgaged) == 0
        assert player.get_out_of_jail_cards == 0


# ────────────────────────────────────────────────────────────────────────────
# 16. Turn advancement
# ────────────────────────────────────────────────────────────────────────────

class TestTurnAdvancement:
    """Tests for advancing turns and skipping bankrupt players."""

    def test_advance_turn_moves_to_next_player(self):
        game = _make_game()
        assert game.current_player.player_id == 0
        game.advance_turn()
        assert game.current_player.player_id == 1

    def test_advance_turn_wraps_around(self):
        game = _make_game()
        for _ in range(4):
            game.advance_turn()
        assert game.current_player.player_id == 0

    def test_advance_turn_skips_bankrupt_players(self):
        game = _make_game()
        game.players[1].is_bankrupt = True
        game.advance_turn()  # should skip player 1
        assert game.current_player.player_id == 2

    def test_advance_turn_skips_multiple_bankrupt(self):
        game = _make_game()
        game.players[1].is_bankrupt = True
        game.players[2].is_bankrupt = True
        game.advance_turn()
        assert game.current_player.player_id == 3

    def test_advance_turn_increments_turn_number(self):
        game = _make_game()
        assert game.turn_number == 0
        game.advance_turn()
        assert game.turn_number == 1
        game.advance_turn()
        assert game.turn_number == 2

    def test_advance_turn_emits_event(self):
        game = _make_game()
        game.advance_turn()
        events = _events_of_type(game, EventType.TURN_STARTED)
        assert len(events) == 1
        assert events[0].data["turn_number"] == 1

    def test_advance_turn_resets_turn_phase(self):
        game = _make_game()
        game.turn_phase = TurnPhase.POST_ROLL
        game.advance_turn()
        assert game.turn_phase == TurnPhase.PRE_ROLL


# ────────────────────────────────────────────────────────────────────────────
# 17. Game over detection
# ────────────────────────────────────────────────────────────────────────────

class TestGameOver:
    """Tests for game-over conditions and winner detection."""

    def test_game_not_over_with_multiple_active(self):
        game = _make_game()
        assert game.is_over() is False

    def test_game_over_one_player_remaining(self):
        game = _make_game()
        for p in game.players[1:]:
            p.is_bankrupt = True
        assert game.is_over() is True

    def test_get_winner_returns_last_standing(self):
        game = _make_game()
        for p in game.players[1:]:
            p.is_bankrupt = True
        winner = game.get_winner()
        assert winner is game.players[0]

    def test_get_winner_returns_none_if_not_over(self):
        game = _make_game()
        assert game.get_winner() is None

    def test_get_active_players(self):
        game = _make_game()
        game.players[2].is_bankrupt = True
        active = game.get_active_players()
        assert len(active) == 3
        assert game.players[2] not in active

    def test_game_over_all_bankrupt(self):
        game = _make_game()
        for p in game.players:
            p.is_bankrupt = True
        assert game.is_over() is True
        assert game.get_winner() is None


# ────────────────────────────────────────────────────────────────────────────
# 18. Rent payment flow
# ────────────────────────────────────────────────────────────────────────────

class TestRentPayment:
    """Tests for the pay_rent method."""

    def test_rent_transfers_cash(self):
        game = _make_game()
        payer = game.players[0]
        owner = game.players[1]
        payer_cash = payer.cash
        owner_cash = owner.cash

        game.pay_rent(payer, owner.player_id, 100)
        assert payer.cash == payer_cash - 100
        assert owner.cash == owner_cash + 100

    def test_rent_emits_event(self):
        game = _make_game()
        game.pay_rent(game.players[0], 1, 50)
        events = _events_of_type(game, EventType.RENT_PAID)
        assert len(events) == 1
        assert events[0].data["amount"] == 50
        assert events[0].data["to_player"] == 1

    def test_rent_with_monopoly_doubles_base(self):
        game = _make_game()
        owner = game.players[1]
        _give_monopoly(game, owner, ColorGroup.BROWN)
        game.last_roll = DiceRoll(3, 4)

        player = game.players[0]
        player.position = 1  # Mediterranean: base rent 2, with monopoly -> 4
        result = game.process_landing(player)
        assert result.rent_owed == 4  # doubled base rent

    def test_rent_with_houses(self):
        game = _make_game()
        owner = game.players[1]
        _give_monopoly(game, owner, ColorGroup.BROWN)
        game.build_house(owner, 1)
        game.build_house(owner, 3)
        game.last_roll = DiceRoll(3, 4)

        player = game.players[0]
        player.position = 1
        result = game.process_landing(player)
        # Mediterranean with 1 house: $10
        assert result.rent_owed == 10


# ────────────────────────────────────────────────────────────────────────────
# 19. Event emission for all major actions
# ────────────────────────────────────────────────────────────────────────────

class TestEventEmission:
    """Verify that every major game action emits the correct event type."""

    def test_dice_rolled_event(self):
        game = _make_game()
        game.roll_dice()
        assert any(e.event_type == EventType.DICE_ROLLED for e in game.events)

    def test_player_moved_event(self):
        game = _make_game()
        game.move_player(game.players[0], 5)
        assert any(e.event_type == EventType.PLAYER_MOVED for e in game.events)

    def test_passed_go_event(self):
        game = _make_game()
        game.players[0].position = 39
        game.move_player(game.players[0], 3)
        assert any(e.event_type == EventType.PASSED_GO for e in game.events)

    def test_property_purchased_event(self):
        game = _make_game()
        game.buy_property(game.players[0], 1)
        assert any(e.event_type == EventType.PROPERTY_PURCHASED for e in game.events)

    def test_auction_won_event(self):
        game = _make_game()
        game.auction_property(1, {0: 100})
        assert any(e.event_type == EventType.AUCTION_WON for e in game.events)

    def test_rent_paid_event(self):
        game = _make_game()
        game.pay_rent(game.players[0], 1, 50)
        assert any(e.event_type == EventType.RENT_PAID for e in game.events)

    def test_tax_paid_event(self):
        game = _make_game()
        game.players[0].position = 4
        game.process_landing(game.players[0])
        assert any(e.event_type == EventType.TAX_PAID for e in game.events)

    def test_house_built_event(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        assert any(e.event_type == EventType.HOUSE_BUILT for e in game.events)

    def test_hotel_built_event(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        for _ in range(4):
            game.build_house(player, 1)
            game.build_house(player, 3)
        game.build_hotel(player, 1)
        assert any(e.event_type == EventType.HOTEL_BUILT for e in game.events)

    def test_building_sold_event(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        game.sell_house(player, 1)
        assert any(e.event_type == EventType.BUILDING_SOLD for e in game.events)

    def test_property_mortgaged_event(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 5)
        game.mortgage_property(player, 5)
        assert any(e.event_type == EventType.PROPERTY_MORTGAGED for e in game.events)

    def test_property_unmortgaged_event(self):
        game = _make_game()
        player = game.players[0]
        game.assign_property(player, 5)
        game.mortgage_property(player, 5)
        game.unmortgage_property(player, 5)
        assert any(e.event_type == EventType.PROPERTY_UNMORTGAGED for e in game.events)

    def test_player_jailed_event(self):
        game = _make_game()
        game.players[0].position = 30
        game.process_landing(game.players[0])
        assert any(e.event_type == EventType.PLAYER_JAILED for e in game.events)

    def test_player_freed_event(self):
        game = _make_game()
        player = game.players[0]
        player.send_to_jail()
        game.handle_jail_turn(player, JailAction.PAY_FINE)
        assert any(e.event_type == EventType.PLAYER_FREED for e in game.events)

    def test_player_bankrupt_event(self):
        game = _make_game()
        game.declare_bankruptcy(game.players[0])
        assert any(e.event_type == EventType.PLAYER_BANKRUPT for e in game.events)

    def test_turn_started_event(self):
        game = _make_game()
        game.advance_turn()
        assert any(e.event_type == EventType.TURN_STARTED for e in game.events)

    def test_trade_accepted_event(self):
        game = _make_game()
        p0, p1 = game.players[0], game.players[1]
        game.assign_property(p0, 1)
        game.assign_property(p1, 3)
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[3],
        )
        game.execute_trade(proposal)
        assert any(e.event_type == EventType.TRADE_ACCEPTED for e in game.events)

    def test_trade_rejected_event(self):
        game = _make_game()
        # Proposer does not own property 1 -> invalid
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1],
        )
        success, reason = game.execute_trade(proposal)
        assert success is False
        assert any(e.event_type == EventType.TRADE_REJECTED for e in game.events)


# ────────────────────────────────────────────────────────────────────────────
# 20. Event retrieval
# ────────────────────────────────────────────────────────────────────────────

class TestEventRetrieval:
    """Tests for get_events_since."""

    def test_get_events_since(self):
        game = _make_game()
        game.roll_dice()
        game.roll_dice()
        game.roll_dice()
        # 3 DICE_ROLLED events at indices 0, 1, 2
        events = game.get_events_since(1)
        assert len(events) == 2

    def test_get_events_since_zero(self):
        game = _make_game()
        game.roll_dice()
        assert game.get_events_since(0) == game.events

    def test_get_events_since_end(self):
        game = _make_game()
        game.roll_dice()
        assert game.get_events_since(len(game.events)) == []


# ────────────────────────────────────────────────────────────────────────────
# 21. Sell hotel
# ────────────────────────────────────────────────────────────────────────────

class TestSellHotel:
    """Tests for selling/downgrading hotels."""

    def _build_hotel(self, game: Game, player: Player, position: int, color: ColorGroup):
        """Build a hotel on one position of a color group, with even build."""
        positions = COLOR_GROUP_POSITIONS[color]
        for _ in range(4):
            for pos in positions:
                game.build_house(player, pos)
        game.build_hotel(player, position)

    def test_sell_hotel_downgrades_to_4_houses(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_hotel(game, player, 1, ColorGroup.BROWN)
        assert player.get_house_count(1) == 5

        success = game.sell_hotel(player, 1)
        assert success is True
        assert player.get_house_count(1) == 4

    def test_sell_hotel_refunds_half_house_cost(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_hotel(game, player, 1, ColorGroup.BROWN)
        cash_before = player.cash
        game.sell_hotel(player, 1)
        # half house cost for brown = 50 // 2 = 25
        assert player.cash == cash_before + 25

    def test_sell_hotel_when_no_houses_available(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        self._build_hotel(game, player, 1, ColorGroup.BROWN)
        game.bank.houses_available = 0  # no houses to downgrade to
        cash_before = player.cash
        success = game.sell_hotel(player, 1)
        assert success is True
        assert player.get_house_count(1) == 0  # sold everything
        # refund = 5 * half house cost = 5 * 25 = 125
        assert player.cash == cash_before + 125

    def test_sell_hotel_fails_if_not_hotel(self):
        game = _make_game()
        player = game.players[0]
        _give_monopoly(game, player, ColorGroup.BROWN)
        game.build_house(player, 1)
        game.build_house(player, 3)
        success = game.sell_hotel(player, 1)
        assert success is False


# ────────────────────────────────────────────────────────────────────────────
# 22. Landing on special spaces
# ────────────────────────────────────────────────────────────────────────────

class TestSpecialSpaces:
    """Tests for GO, Jail/Just Visiting, Free Parking."""

    def test_landing_on_go(self):
        game = _make_game()
        player = game.players[0]
        player.position = 0
        result = game.process_landing(player)
        assert result.space_type == SpaceType.GO
        assert result.rent_owed == 0
        assert result.requires_buy_decision is False

    def test_landing_on_just_visiting(self):
        game = _make_game()
        player = game.players[0]
        player.position = 10
        result = game.process_landing(player)
        assert result.space_type == SpaceType.JAIL
        # Just visiting, nothing happens
        assert result.rent_owed == 0
        assert result.sent_to_jail is False

    def test_landing_on_free_parking(self):
        game = _make_game()
        player = game.players[0]
        player.position = 20
        result = game.process_landing(player)
        assert result.space_type == SpaceType.FREE_PARKING
        assert result.rent_owed == 0


# ────────────────────────────────────────────────────────────────────────────
# 23. Trade via Game.execute_trade
# ────────────────────────────────────────────────────────────────────────────

class TestGameTrade:
    """Tests for trading through the Game's execute_trade method."""

    def test_successful_property_swap(self):
        game = _make_game()
        p0, p1 = game.players[0], game.players[1]
        game.assign_property(p0, 1)
        game.assign_property(p1, 3)

        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[3],
        )
        success, reason = game.execute_trade(proposal)
        assert success is True
        assert reason == ""
        # Ownership updated in game tracking
        assert game.get_property_owner(1) is p1
        assert game.get_property_owner(3) is p0

    def test_trade_updates_property_owners_dict(self):
        game = _make_game()
        p0, p1 = game.players[0], game.players[1]
        game.assign_property(p0, 5)  # Railroad
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[5], offered_cash=0,
        )
        game.execute_trade(proposal)
        assert game._property_owners[5] == p1.player_id

    def test_invalid_trade_rejected(self):
        game = _make_game()
        # Player 0 does not own property at position 1
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1],
        )
        success, reason = game.execute_trade(proposal)
        assert success is False
        assert "Proposer doesn't own" in reason


# ────────────────────────────────────────────────────────────────────────────
# 24. Monopoly rent multiplier
# ────────────────────────────────────────────────────────────────────────────

class TestMonopolyRent:
    """Tests verifying monopoly doubles unimproved rent."""

    def test_no_monopoly_base_rent(self):
        game = _make_game()
        owner = game.players[1]
        game.assign_property(owner, 1)  # only 1 of 2 browns

        player = game.players[0]
        player.position = 1
        game.last_roll = DiceRoll(3, 4)
        result = game.process_landing(player)
        assert result.rent_owed == 2  # base rent

    def test_monopoly_doubles_rent(self):
        game = _make_game()
        owner = game.players[1]
        _give_monopoly(game, owner, ColorGroup.BROWN)

        player = game.players[0]
        player.position = 1
        game.last_roll = DiceRoll(3, 4)
        result = game.process_landing(player)
        assert result.rent_owed == 4  # doubled


# ────────────────────────────────────────────────────────────────────────────
# 25. Edge cases
# ────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Miscellaneous edge-case tests."""

    def test_two_player_game(self):
        game = Game(num_players=2, seed=1)
        assert len(game.players) == 2
        game.advance_turn()
        assert game.current_player.player_id == 1
        game.advance_turn()
        assert game.current_player.player_id == 0

    def test_buy_boardwalk(self):
        game = _make_game()
        player = game.players[0]
        success = game.buy_property(player, 39)  # Boardwalk: $400
        assert success is True
        assert player.cash == STARTING_CASH - 400

    def test_landing_result_defaults(self):
        from monopoly.engine.game import LandingResult
        lr = LandingResult(space_type=SpaceType.GO, position=0)
        assert lr.requires_buy_decision is False
        assert lr.rent_owed == 0
        assert lr.rent_to_player == -1
        assert lr.card_drawn is None
        assert lr.tax_amount == 0
        assert lr.sent_to_jail is False

    def test_current_player_property(self):
        game = _make_game()
        assert game.current_player is game.players[0]
        game.current_player_index = 2
        assert game.current_player is game.players[2]

    def test_player_move_forward_exact_40(self):
        """Moving exactly 40 spaces should wrap to same position and pass GO."""
        game = _make_game()
        player = game.players[0]
        player.position = 0
        passed_go = game.move_player(player, 40)
        assert player.position == 0
        # 40 % 40 == 0, which is NOT < 0, so passed_go should be False
        assert passed_go is False

    def test_four_railroads_rent(self):
        game = _make_game()
        owner = game.players[1]
        for pos in [5, 15, 25, 35]:
            game.assign_property(owner, pos)

        player = game.players[0]
        player.position = 5
        result = game.process_landing(player)
        assert result.rent_owed == 200  # 4 railroads
