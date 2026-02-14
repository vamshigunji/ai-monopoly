"""Comprehensive tests for the Monopoly trade execution module."""

import pytest

from monopoly.engine.board import Board
from monopoly.engine.player import Player
from monopoly.engine.rules import Rules
from monopoly.engine.trade import execute_trade
from monopoly.engine.types import EventType, TradeProposal


@pytest.fixture
def board():
    return Board()


@pytest.fixture
def rules(board):
    return Rules(board)


@pytest.fixture
def player_a():
    p = Player(player_id=0, name="Alice")
    p.add_property(1)   # Mediterranean Avenue
    p.add_property(3)   # Baltic Avenue
    return p


@pytest.fixture
def player_b():
    p = Player(player_id=1, name="Bob")
    p.add_property(6)   # Oriental Avenue
    p.add_property(8)   # Vermont Avenue
    return p


class TestSimplePropertyTrade:
    """Tests for basic property-for-property trades."""

    def test_trade_single_property(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[6],
        )
        events = execute_trade(proposal, player_a, player_b, rules)

        assert not player_a.owns_property(1)
        assert player_a.owns_property(6)
        assert not player_b.owns_property(6)
        assert player_b.owns_property(1)
        assert len(events) == 1
        assert events[0].event_type == EventType.TRADE_ACCEPTED

    def test_trade_multiple_properties(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1, 3], requested_properties=[6, 8],
        )
        events = execute_trade(proposal, player_a, player_b, rules)

        assert player_a.owns_property(6)
        assert player_a.owns_property(8)
        assert player_b.owns_property(1)
        assert player_b.owns_property(3)

    def test_trade_preserves_other_properties(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[6],
        )
        execute_trade(proposal, player_a, player_b, rules)

        # Untouched properties remain
        assert player_a.owns_property(3)
        assert player_b.owns_property(8)


class TestTradeWithCash:
    """Tests for trades involving cash."""

    def test_trade_property_for_cash(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_cash=200,
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert not player_a.owns_property(1)
        assert player_b.owns_property(1)
        assert player_a.cash == 1700  # 1500 + 200
        assert player_b.cash == 1300  # 1500 - 200

    def test_trade_cash_for_property(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_cash=150, requested_properties=[6],
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert player_a.owns_property(6)
        assert player_a.cash == 1350
        assert player_b.cash == 1650

    def test_trade_with_both_cash_directions(self, rules, player_a, player_b):
        """Both players offer cash (net cash transfer)."""
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[6],
            offered_cash=50, requested_cash=0,
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert player_a.cash == 1450  # 1500 - 50
        assert player_b.cash == 1550  # 1500 + 50


class TestTradeWithJailCards:
    """Tests for trades involving Get Out of Jail Free cards."""

    def test_trade_jail_card(self, rules):
        player_a = Player(player_id=0, name="Alice")
        player_a.get_out_of_jail_cards = 2
        player_b = Player(player_id=1, name="Bob")
        player_b.add_property(6)

        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_jail_cards=1, requested_properties=[6],
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert player_a.get_out_of_jail_cards == 1
        assert player_b.get_out_of_jail_cards == 1
        assert player_a.owns_property(6)

    def test_trade_jail_card_for_cash(self, rules):
        player_a = Player(player_id=0, name="Alice")
        player_a.get_out_of_jail_cards = 1
        player_b = Player(player_id=1, name="Bob")

        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_jail_cards=1, requested_cash=50,
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert player_a.get_out_of_jail_cards == 0
        assert player_b.get_out_of_jail_cards == 1
        assert player_a.cash == 1550
        assert player_b.cash == 1450


class TestMortgagedPropertyTrade:
    """Tests for trading mortgaged properties."""

    def test_mortgaged_property_transfer_charges_fee(self, rules):
        player_a = Player(player_id=0, name="Alice")
        player_a.add_property(1)  # Mediterranean, mortgage_value=30
        player_a.mortgage_property(1)

        player_b = Player(player_id=1, name="Bob")

        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_cash=100,
        )
        execute_trade(proposal, player_a, player_b, rules)

        # Receiver gets the property (still mortgaged) and pays 10% fee
        assert player_b.owns_property(1)
        assert player_b.is_mortgaged(1)
        # Fee = 10% of $30 mortgage = $3
        # Bob: 1500 - 100 (trade cash) - 3 (fee) = 1397
        assert player_b.cash == 1397

    def test_mortgaged_property_stays_mortgaged_after_trade(self, rules):
        player_a = Player(player_id=0, name="Alice")
        player_a.add_property(39)  # Boardwalk, mortgage_value=200
        player_a.mortgage_property(39)

        player_b = Player(player_id=1, name="Bob")

        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[39],
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert player_b.is_mortgaged(39)
        # Fee = 10% of $200 = $20
        assert player_b.cash == 1480


class TestTradeEvents:
    """Tests for events emitted during trade execution."""

    def test_trade_emits_accepted_event(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[6],
        )
        events = execute_trade(proposal, player_a, player_b, rules)

        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.TRADE_ACCEPTED
        assert event.player_id == 0
        assert event.data["proposer_id"] == 0
        assert event.data["receiver_id"] == 1
        assert event.data["offered_properties"] == [1]
        assert event.data["requested_properties"] == [6]

    def test_trade_event_includes_cash_amounts(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], offered_cash=100,
            requested_properties=[6],
        )
        events = execute_trade(proposal, player_a, player_b, rules)

        assert events[0].data["offered_cash"] == 100
        assert events[0].data["requested_cash"] == 0


class TestTradePortfolioUpdates:
    """Tests that portfolios are correctly updated after trades."""

    def test_both_players_portfolios_updated(self, rules, player_a, player_b):
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_properties=[1], requested_properties=[6],
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert 1 not in player_a.properties
        assert 6 in player_a.properties
        assert 6 not in player_b.properties
        assert 1 in player_b.properties

    def test_empty_offered_properties(self, rules, player_a, player_b):
        """Trade where only one side offers properties (cash for property)."""
        proposal = TradeProposal(
            proposer_id=0, receiver_id=1,
            offered_cash=300, requested_properties=[6],
        )
        execute_trade(proposal, player_a, player_b, rules)

        assert player_a.owns_property(6)
        assert not player_b.owns_property(6)
        assert player_a.cash == 1200
        assert player_b.cash == 1800
