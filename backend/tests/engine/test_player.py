"""Comprehensive tests for the Monopoly player module."""

import pytest

from monopoly.engine.board import Board
from monopoly.engine.player import Player, STARTING_CASH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def player():
    """Create a fresh player for each test."""
    return Player(player_id=0, name="TestPlayer")


@pytest.fixture
def board():
    """Create a board instance for net worth calculations."""
    return Board()


# ===========================================================================
# 1. Starting state
# ===========================================================================

class TestStartingState:
    """Player must start with $1500 at position 0, with no properties or jail status."""

    def test_starting_cash(self, player):
        assert player.cash == 1500

    def test_starting_cash_matches_constant(self, player):
        assert player.cash == STARTING_CASH

    def test_starting_position(self, player):
        assert player.position == 0

    def test_starting_properties_empty(self, player):
        assert player.properties == []

    def test_starting_houses_empty(self, player):
        assert player.houses == {}

    def test_starting_mortgaged_empty(self, player):
        assert player.mortgaged == set()

    def test_starting_not_in_jail(self, player):
        assert player.in_jail is False

    def test_starting_jail_turns_zero(self, player):
        assert player.jail_turns == 0

    def test_starting_no_jail_cards(self, player):
        assert player.get_out_of_jail_cards == 0

    def test_starting_not_bankrupt(self, player):
        assert player.is_bankrupt is False

    def test_starting_consecutive_doubles_zero(self, player):
        assert player.consecutive_doubles == 0

    def test_player_id(self, player):
        assert player.player_id == 0

    def test_player_name(self, player):
        assert player.name == "TestPlayer"

    def test_custom_player_id_and_name(self):
        p = Player(player_id=3, name="Alice")
        assert p.player_id == 3
        assert p.name == "Alice"
        assert p.cash == STARTING_CASH


# ===========================================================================
# 2. Cash management: add_cash and remove_cash
# ===========================================================================

class TestCashManagement:
    """add_cash and remove_cash must correctly modify the player's balance."""

    def test_add_cash(self, player):
        player.add_cash(200)
        assert player.cash == 1700

    def test_add_cash_zero(self, player):
        player.add_cash(0)
        assert player.cash == 1500

    def test_add_cash_multiple_times(self, player):
        player.add_cash(100)
        player.add_cash(200)
        player.add_cash(300)
        assert player.cash == 2100

    def test_add_large_amount(self, player):
        player.add_cash(10000)
        assert player.cash == 11500

    def test_remove_cash_success(self, player):
        result = player.remove_cash(500)
        assert result is True
        assert player.cash == 1000

    def test_remove_cash_exact_balance(self, player):
        result = player.remove_cash(1500)
        assert result is True
        assert player.cash == 0

    def test_remove_cash_zero(self, player):
        result = player.remove_cash(0)
        assert result is True
        assert player.cash == 1500

    def test_remove_cash_insufficient_funds(self, player):
        result = player.remove_cash(1501)
        assert result is False
        assert player.cash == 1500  # Unchanged

    def test_remove_cash_insufficient_leaves_balance_unchanged(self, player):
        player.remove_cash(1000)  # Down to 500
        result = player.remove_cash(501)
        assert result is False
        assert player.cash == 500

    def test_remove_cash_after_add(self, player):
        player.add_cash(300)
        result = player.remove_cash(1800)
        assert result is True
        assert player.cash == 0

    def test_sequential_add_and_remove(self, player):
        player.add_cash(500)    # 2000
        player.remove_cash(200) # 1800
        player.add_cash(100)    # 1900
        player.remove_cash(400) # 1500
        assert player.cash == 1500


# ===========================================================================
# 3. Property management: add, remove, owns
# ===========================================================================

class TestPropertyManagement:
    """add_property, remove_property, and owns_property."""

    def test_add_property(self, player):
        player.add_property(1)
        assert 1 in player.properties

    def test_add_multiple_properties(self, player):
        player.add_property(1)
        player.add_property(3)
        player.add_property(5)
        assert player.properties == [1, 3, 5]

    def test_add_duplicate_property_is_noop(self, player):
        player.add_property(1)
        player.add_property(1)
        assert player.properties == [1]

    def test_owns_property_true(self, player):
        player.add_property(5)
        assert player.owns_property(5) is True

    def test_owns_property_false(self, player):
        assert player.owns_property(5) is False

    def test_remove_property(self, player):
        player.add_property(1)
        player.add_property(3)
        player.remove_property(1)
        assert player.properties == [3]
        assert player.owns_property(1) is False

    def test_remove_nonexistent_property_is_noop(self, player):
        player.add_property(1)
        player.remove_property(99)  # Not owned
        assert player.properties == [1]

    def test_remove_property_clears_mortgage(self, player):
        player.add_property(1)
        player.mortgage_property(1)
        assert player.is_mortgaged(1) is True
        player.remove_property(1)
        assert player.is_mortgaged(1) is False

    def test_remove_property_clears_houses(self, player):
        player.add_property(1)
        player.set_houses(1, 3)
        assert player.get_house_count(1) == 3
        player.remove_property(1)
        assert player.get_house_count(1) == 0

    def test_add_all_properties_of_color_group(self, player):
        # Add all brown properties
        player.add_property(1)
        player.add_property(3)
        assert player.owns_property(1) is True
        assert player.owns_property(3) is True


# ===========================================================================
# 4. Mortgage / unmortgage tracking
# ===========================================================================

class TestMortgageTracking:
    """mortgage_property, unmortgage_property, and is_mortgaged."""

    def test_mortgage_property(self, player):
        player.add_property(1)
        player.mortgage_property(1)
        assert player.is_mortgaged(1) is True

    def test_unmortgage_property(self, player):
        player.add_property(1)
        player.mortgage_property(1)
        player.unmortgage_property(1)
        assert player.is_mortgaged(1) is False

    def test_is_mortgaged_default_false(self, player):
        player.add_property(1)
        assert player.is_mortgaged(1) is False

    def test_mortgage_multiple_properties(self, player):
        player.add_property(1)
        player.add_property(3)
        player.add_property(5)
        player.mortgage_property(1)
        player.mortgage_property(5)
        assert player.is_mortgaged(1) is True
        assert player.is_mortgaged(3) is False
        assert player.is_mortgaged(5) is True

    def test_unmortgage_only_target(self, player):
        player.add_property(1)
        player.add_property(3)
        player.mortgage_property(1)
        player.mortgage_property(3)
        player.unmortgage_property(1)
        assert player.is_mortgaged(1) is False
        assert player.is_mortgaged(3) is True

    def test_unmortgage_non_mortgaged_is_noop(self, player):
        player.add_property(1)
        player.unmortgage_property(1)  # Not mortgaged
        assert player.is_mortgaged(1) is False

    def test_double_mortgage_is_idempotent(self, player):
        player.add_property(1)
        player.mortgage_property(1)
        player.mortgage_property(1)
        assert player.is_mortgaged(1) is True
        # Unmortgage once should clear it
        player.unmortgage_property(1)
        assert player.is_mortgaged(1) is False


# ===========================================================================
# 5. House count tracking
# ===========================================================================

class TestHouseCountTracking:
    """get_house_count and set_houses."""

    def test_initial_house_count_is_zero(self, player):
        player.add_property(1)
        assert player.get_house_count(1) == 0

    def test_set_houses(self, player):
        player.add_property(1)
        player.set_houses(1, 3)
        assert player.get_house_count(1) == 3

    def test_set_houses_to_hotel(self, player):
        player.add_property(1)
        player.set_houses(1, 5)
        assert player.get_house_count(1) == 5

    def test_set_houses_to_zero_removes_entry(self, player):
        player.add_property(1)
        player.set_houses(1, 3)
        player.set_houses(1, 0)
        assert player.get_house_count(1) == 0
        assert 1 not in player.houses

    def test_set_houses_overwrites_previous(self, player):
        player.add_property(1)
        player.set_houses(1, 2)
        player.set_houses(1, 4)
        assert player.get_house_count(1) == 4

    def test_house_count_for_unowned_property(self, player):
        assert player.get_house_count(99) == 0

    def test_multiple_properties_with_houses(self, player):
        player.add_property(1)
        player.add_property(3)
        player.set_houses(1, 2)
        player.set_houses(3, 4)
        assert player.get_house_count(1) == 2
        assert player.get_house_count(3) == 4

    @pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 5])
    def test_all_valid_house_counts(self, player, count):
        player.add_property(1)
        player.set_houses(1, count)
        assert player.get_house_count(1) == count


# ===========================================================================
# 6. Jail mechanics: send_to_jail, release_from_jail
# ===========================================================================

class TestJailMechanics:
    """send_to_jail and release_from_jail state transitions."""

    def test_send_to_jail(self, player):
        player.position = 30  # Go To Jail space
        player.send_to_jail()
        assert player.in_jail is True
        assert player.position == 10
        assert player.jail_turns == 0

    def test_send_to_jail_resets_consecutive_doubles(self, player):
        player.consecutive_doubles = 2
        player.send_to_jail()
        assert player.consecutive_doubles == 0

    def test_send_to_jail_from_any_position(self, player):
        player.position = 7  # Chance space
        player.send_to_jail()
        assert player.position == 10
        assert player.in_jail is True

    def test_release_from_jail(self, player):
        player.send_to_jail()
        player.release_from_jail()
        assert player.in_jail is False
        assert player.jail_turns == 0

    def test_release_from_jail_keeps_position(self, player):
        player.send_to_jail()
        player.release_from_jail()
        # Player stays at position 10 (Jail / Just Visiting)
        assert player.position == 10

    def test_jail_turns_can_be_incremented(self, player):
        player.send_to_jail()
        player.jail_turns = 1
        assert player.jail_turns == 1
        player.jail_turns = 2
        assert player.jail_turns == 2

    def test_send_to_jail_resets_jail_turns(self, player):
        player.send_to_jail()
        player.jail_turns = 2
        player.release_from_jail()
        player.send_to_jail()  # Jailed again
        assert player.jail_turns == 0

    def test_release_clears_jail_turns(self, player):
        player.send_to_jail()
        player.jail_turns = 3
        player.release_from_jail()
        assert player.jail_turns == 0


# ===========================================================================
# 7. Movement: move_to, move_forward, passing GO detection
# ===========================================================================

class TestMovement:
    """move_to and move_forward with GO-passing detection."""

    # --- move_to ---

    def test_move_to_simple(self, player):
        passed_go = player.move_to(5)
        assert player.position == 5
        assert passed_go is False

    def test_move_to_jail(self, player):
        passed_go = player.move_to(10)
        assert player.position == 10
        assert passed_go is False

    def test_move_to_wraps_around(self, player):
        player.position = 35
        passed_go = player.move_to(3)
        assert player.position == 3
        assert passed_go is True

    def test_move_to_go_from_behind(self, player):
        player.position = 39
        passed_go = player.move_to(0)
        assert player.position == 0
        # Moving from 39 to 0: position < old_position AND position != old_position
        assert passed_go is True

    def test_move_to_same_position(self, player):
        player.position = 10
        passed_go = player.move_to(10)
        assert player.position == 10
        assert passed_go is False

    def test_move_to_position_0_from_0(self, player):
        player.position = 0
        passed_go = player.move_to(0)
        assert player.position == 0
        assert passed_go is False

    def test_move_to_wraps_large_position(self, player):
        passed_go = player.move_to(45)
        assert player.position == 5

    def test_move_to_backward_on_board(self, player):
        """Going from position 5 to position 3 means wrapping past GO (clockwise
        interpretation in move_to)."""
        player.position = 5
        passed_go = player.move_to(3)
        assert player.position == 3
        assert passed_go is True  # 3 < 5

    # --- move_forward ---

    def test_move_forward_simple(self, player):
        passed_go = player.move_forward(7)
        assert player.position == 7
        assert passed_go is False

    def test_move_forward_from_position(self, player):
        player.position = 20
        passed_go = player.move_forward(10)
        assert player.position == 30
        assert passed_go is False

    def test_move_forward_past_go(self, player):
        player.position = 35
        passed_go = player.move_forward(7)
        assert player.position == 2
        assert passed_go is True

    def test_move_forward_exactly_to_go(self, player):
        player.position = 35
        passed_go = player.move_forward(5)
        # (35 + 5) % 40 = 0; 0 < 35 -> True
        assert player.position == 0
        assert passed_go is True

    def test_move_forward_wraps_around(self, player):
        player.position = 38
        passed_go = player.move_forward(12)
        # (38 + 12) % 40 = 10
        assert player.position == 10
        assert passed_go is True

    def test_move_forward_typical_dice_roll(self, player):
        player.position = 0
        passed_go = player.move_forward(6)
        assert player.position == 6
        assert passed_go is False

    def test_move_forward_maximum_dice_roll(self, player):
        player.position = 0
        passed_go = player.move_forward(12)
        assert player.position == 12
        assert passed_go is False

    def test_move_forward_from_go_to_jail_space(self, player):
        player.position = 25
        passed_go = player.move_forward(5)
        assert player.position == 30
        assert passed_go is False

    def test_move_forward_zero_spaces(self, player):
        player.position = 15
        passed_go = player.move_forward(0)
        assert player.position == 15
        assert passed_go is False

    def test_move_forward_full_lap(self, player):
        player.position = 0
        passed_go = player.move_forward(40)
        # (0 + 40) % 40 = 0; 0 < 0 is False
        assert player.position == 0
        assert passed_go is False

    def test_move_forward_39_to_0(self, player):
        player.position = 39
        passed_go = player.move_forward(1)
        assert player.position == 0
        assert passed_go is True


# ===========================================================================
# 8. Net worth calculation
# ===========================================================================

class TestNetWorth:
    """net_worth calculates cash + property values + building values."""

    def test_net_worth_starting(self, player, board):
        assert player.net_worth(board) == 1500

    def test_net_worth_with_property(self, player, board):
        player.add_property(1)  # Mediterranean Avenue, price $60
        # 1500 + 60 = 1560
        assert player.net_worth(board) == 1560

    def test_net_worth_with_mortgaged_property(self, player, board):
        player.add_property(1)  # Mediterranean Avenue, mortgage $30
        player.mortgage_property(1)
        # 1500 + 30 (mortgage value) = 1530
        assert player.net_worth(board) == 1530

    def test_net_worth_with_houses(self, player, board):
        player.add_property(1)  # Mediterranean Avenue, price $60, house_cost $50
        player.set_houses(1, 3)
        # 1500 + 60 (property) + 3 * 50 (houses) = 1710
        assert player.net_worth(board) == 1710

    def test_net_worth_with_hotel(self, player, board):
        player.add_property(1)  # Mediterranean Avenue, price $60, house_cost $50
        player.set_houses(1, 5)  # Hotel
        # 1500 + 60 (property) + 5 * 50 (hotel = 4 houses + 1 hotel cost) = 1810
        assert player.net_worth(board) == 1810

    def test_net_worth_with_railroad(self, player, board):
        player.add_property(5)  # Reading Railroad, price $200
        # 1500 + 200 = 1700
        assert player.net_worth(board) == 1700

    def test_net_worth_with_mortgaged_railroad(self, player, board):
        player.add_property(5)  # Reading Railroad, mortgage $100
        player.mortgage_property(5)
        # 1500 + 100 = 1600
        assert player.net_worth(board) == 1600

    def test_net_worth_with_utility(self, player, board):
        player.add_property(12)  # Electric Company, price $150
        # 1500 + 150 = 1650
        assert player.net_worth(board) == 1650

    def test_net_worth_with_mortgaged_utility(self, player, board):
        player.add_property(12)  # Electric Company, mortgage $75
        player.mortgage_property(12)
        # 1500 + 75 = 1575
        assert player.net_worth(board) == 1575

    def test_net_worth_complex_portfolio(self, player, board):
        """Multiple properties, some mortgaged, some with houses."""
        player.add_property(1)   # Mediterranean ($60), 2 houses ($50 each)
        player.set_houses(1, 2)
        player.add_property(3)   # Baltic ($60), mortgaged ($30)
        player.mortgage_property(3)
        player.add_property(5)   # Reading Railroad ($200)
        player.add_property(12)  # Electric Company ($150), mortgaged ($75)
        player.mortgage_property(12)
        player.add_property(39)  # Boardwalk ($400), hotel ($200 * 5)
        player.set_houses(39, 5)

        expected = (
            1500           # cash
            + 60 + 2 * 50   # Mediterranean + 2 houses
            + 30             # Baltic (mortgaged)
            + 200            # Reading Railroad
            + 75             # Electric Company (mortgaged)
            + 400 + 5 * 200  # Boardwalk + hotel
        )
        assert player.net_worth(board) == expected

    def test_net_worth_after_spending_cash(self, player, board):
        player.remove_cash(500)
        player.add_property(1)  # $60
        # 1000 + 60 = 1060
        assert player.net_worth(board) == 1060

    def test_net_worth_zero_cash_with_properties(self, player, board):
        player.remove_cash(1500)
        player.add_property(39)  # Boardwalk $400
        assert player.net_worth(board) == 400

    def test_net_worth_all_railroads(self, player, board):
        for pos in [5, 15, 25, 35]:
            player.add_property(pos)
        # 1500 + 4 * 200 = 2300
        assert player.net_worth(board) == 2300

    def test_net_worth_both_utilities(self, player, board):
        player.add_property(12)
        player.add_property(28)
        # 1500 + 150 + 150 = 1800
        assert player.net_worth(board) == 1800


# ===========================================================================
# 9. Get Out of Jail Free card tracking
# ===========================================================================

class TestGetOutOfJailFreeCards:
    """Tracking the number of Get Out of Jail Free cards."""

    def test_starts_with_zero_cards(self, player):
        assert player.get_out_of_jail_cards == 0

    def test_add_one_card(self, player):
        player.get_out_of_jail_cards += 1
        assert player.get_out_of_jail_cards == 1

    def test_add_two_cards(self, player):
        player.get_out_of_jail_cards += 1
        player.get_out_of_jail_cards += 1
        assert player.get_out_of_jail_cards == 2

    def test_use_card(self, player):
        player.get_out_of_jail_cards = 2
        player.get_out_of_jail_cards -= 1
        assert player.get_out_of_jail_cards == 1

    def test_use_last_card(self, player):
        player.get_out_of_jail_cards = 1
        player.get_out_of_jail_cards -= 1
        assert player.get_out_of_jail_cards == 0


# ===========================================================================
# 10. Bankruptcy state
# ===========================================================================

class TestBankruptcy:
    """Bankrupt players should be flagged."""

    def test_not_bankrupt_by_default(self, player):
        assert player.is_bankrupt is False

    def test_set_bankrupt(self, player):
        player.is_bankrupt = True
        assert player.is_bankrupt is True

    def test_bankrupt_player_can_still_have_cash(self, player):
        """Bankruptcy is a flag; it does not automatically zero out cash."""
        player.is_bankrupt = True
        assert player.cash == 1500  # Still has cash until explicitly removed

    def test_bankrupt_player_state_independent_of_cash(self, player):
        player.remove_cash(1500)
        assert player.cash == 0
        assert player.is_bankrupt is False  # Not automatically bankrupt


# ===========================================================================
# 11. Consecutive doubles tracking
# ===========================================================================

class TestConsecutiveDoubles:
    """Tracking consecutive doubles for jail rule (3 doubles -> jail)."""

    def test_starts_at_zero(self, player):
        assert player.consecutive_doubles == 0

    def test_increment_doubles(self, player):
        player.consecutive_doubles = 1
        assert player.consecutive_doubles == 1
        player.consecutive_doubles = 2
        assert player.consecutive_doubles == 2

    def test_send_to_jail_resets_doubles(self, player):
        player.consecutive_doubles = 3
        player.send_to_jail()
        assert player.consecutive_doubles == 0


# ===========================================================================
# 12. Edge cases and integration-like scenarios
# ===========================================================================

class TestEdgeCases:
    """Edge cases and multi-step scenarios."""

    def test_player_buys_property_and_checks_ownership(self, player, board):
        """Simulate buying Mediterranean Avenue."""
        position = 1
        price = board.get_purchase_price(position)
        assert price == 60
        result = player.remove_cash(price)
        assert result is True
        player.add_property(position)
        assert player.owns_property(position) is True
        assert player.cash == 1440

    def test_player_full_turn_simulation(self, player, board):
        """Simulate: move forward, land on property, buy it."""
        passed_go = player.move_forward(6)  # Land on Oriental Avenue
        assert player.position == 6
        assert passed_go is False

        price = board.get_purchase_price(6)
        assert price == 100
        player.remove_cash(price)
        player.add_property(6)

        assert player.cash == 1400
        assert player.owns_property(6) is True

    def test_jail_cycle(self, player):
        """Go to jail, spend turns, get released."""
        player.position = 30
        player.send_to_jail()
        assert player.position == 10
        assert player.in_jail is True

        player.jail_turns = 1
        player.jail_turns = 2
        player.jail_turns = 3

        player.release_from_jail()
        assert player.in_jail is False
        assert player.jail_turns == 0
        assert player.position == 10

    def test_mortgage_and_unmortgage_cycle(self, player, board):
        """Buy, mortgage, unmortgage a property."""
        player.add_property(1)
        assert player.is_mortgaged(1) is False

        player.mortgage_property(1)
        assert player.is_mortgaged(1) is True

        player.unmortgage_property(1)
        assert player.is_mortgaged(1) is False

    def test_building_houses_then_selling(self, player, board):
        """Build houses and then downgrade."""
        player.add_property(1)
        player.set_houses(1, 1)
        assert player.get_house_count(1) == 1

        player.set_houses(1, 4)
        assert player.get_house_count(1) == 4

        # Upgrade to hotel
        player.set_houses(1, 5)
        assert player.get_house_count(1) == 5

        # Sell down
        player.set_houses(1, 3)
        assert player.get_house_count(1) == 3

        player.set_houses(1, 0)
        assert player.get_house_count(1) == 0

    def test_multiple_players_independent(self):
        """Two players have independent state."""
        p1 = Player(player_id=0, name="Alice")
        p2 = Player(player_id=1, name="Bob")

        p1.add_cash(500)
        p2.remove_cash(500)

        assert p1.cash == 2000
        assert p2.cash == 1000

        p1.add_property(1)
        p2.add_property(3)

        assert p1.owns_property(1) is True
        assert p1.owns_property(3) is False
        assert p2.owns_property(1) is False
        assert p2.owns_property(3) is True

    def test_pass_go_collect_200(self, player):
        """Simulate passing GO: move forward past position 0, add $200."""
        player.position = 38
        passed_go = player.move_forward(4)  # -> position 2
        assert passed_go is True
        if passed_go:
            player.add_cash(200)
        assert player.cash == 1700
        assert player.position == 2

    def test_transfer_property_between_players(self):
        """Simulate a trade: one player gives property to another."""
        p1 = Player(player_id=0, name="Alice")
        p2 = Player(player_id=1, name="Bob")

        p1.add_property(1)
        assert p1.owns_property(1) is True
        assert p2.owns_property(1) is False

        p1.remove_property(1)
        p2.add_property(1)

        assert p1.owns_property(1) is False
        assert p2.owns_property(1) is True

    def test_bankrupt_player_loses_everything(self, player, board):
        """When going bankrupt: flag set, properties removed, cash zeroed."""
        player.add_property(1)
        player.add_property(5)
        player.set_houses(1, 3)

        # Simulate bankruptcy
        player.is_bankrupt = True
        player.remove_cash(player.cash)
        for pos in list(player.properties):
            player.remove_property(pos)

        assert player.is_bankrupt is True
        assert player.cash == 0
        assert player.properties == []
        assert player.houses == {}
