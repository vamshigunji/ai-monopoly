"""Tests for fallback random agent."""

import pytest

from monopoly.agents.base import GameView, OpponentView
from monopoly.agents.random_agent import RandomAgent
from monopoly.engine.types import PropertyData, ColorGroup, TradeProposal


@pytest.fixture
def game_view():
    """Create a basic game view for testing."""
    return GameView(
        my_player_id=0,
        turn_number=5,
        my_cash=1000,
        my_position=10,
        my_properties=[],
        my_houses={},
        my_mortgaged=set(),
        my_jail_cards=0,
        my_in_jail=False,
        my_jail_turns=0,
        opponents=[],
        property_ownership={},
        houses_on_board={},
        bank_houses_remaining=32,
        bank_hotels_remaining=12,
        last_dice_roll=None,
        recent_events=[],
    )


@pytest.fixture
def property_data():
    """Create sample property data."""
    return PropertyData(
        name="Boardwalk",
        position=39,
        color_group=ColorGroup.DARK_BLUE,
        price=400,
        mortgage_value=200,
        rent=(50, 200, 600, 1400, 1700, 2000),
        house_cost=200,
    )


@pytest.mark.asyncio
async def test_random_agent_buy_decision_affordable(property_data):
    """Random agent buys if it has 2x the price."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=800,  # Exactly 2x the $400 price
        my_position=10, my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=False, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    decision = await agent.decide_buy_or_auction(game_view, property_data)
    assert decision is True


@pytest.mark.asyncio
async def test_random_agent_buy_decision_not_affordable(property_data):
    """Random agent auctions if it doesn't have 2x the price."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=700,  # Less than 2x the $400 price
        my_position=10, my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=False, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    decision = await agent.decide_buy_or_auction(game_view, property_data)
    assert decision is False


@pytest.mark.asyncio
async def test_random_agent_auction_bid(property_data):
    """Random agent bids list price if affordable."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=500,
        my_position=10, my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=False, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    bid = await agent.decide_auction_bid(game_view, property_data, current_bid=100)
    assert bid == 110  # current_bid + 10


@pytest.mark.asyncio
async def test_random_agent_auction_pass(property_data):
    """Random agent passes if bid would exceed list price."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=500,
        my_position=10, my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=False, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    # Current bid already at or above list price
    bid = await agent.decide_auction_bid(game_view, property_data, current_bid=400)
    assert bid == 0


@pytest.mark.asyncio
async def test_random_agent_never_trades(game_view):
    """Random agent never proposes trades."""
    agent = RandomAgent(player_id=0)

    proposal = await agent.decide_trade(game_view)
    assert proposal is None


@pytest.mark.asyncio
async def test_random_agent_always_rejects_trades(game_view):
    """Random agent always rejects incoming trades."""
    agent = RandomAgent(player_id=0)

    trade = TradeProposal(
        proposer_id=1,
        receiver_id=0,
        offered_properties=[5],
        requested_properties=[10],
    )

    response = await agent.respond_to_trade(game_view, trade)
    assert response is False


@pytest.mark.asyncio
async def test_random_agent_jail_use_card():
    """Random agent uses card if available."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=1000, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=1, my_in_jail=True, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    action = await agent.decide_jail_action(game_view)
    from monopoly.engine.types import JailAction
    assert action == JailAction.USE_CARD


@pytest.mark.asyncio
async def test_random_agent_jail_pay_fine():
    """Random agent pays fine if affordable and no card."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=100, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=True, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    action = await agent.decide_jail_action(game_view)
    from monopoly.engine.types import JailAction
    assert action == JailAction.PAY_FINE


@pytest.mark.asyncio
async def test_random_agent_jail_roll_doubles():
    """Random agent rolls doubles if no card and can't afford fine."""
    agent = RandomAgent(player_id=0)
    game_view = GameView(
        my_player_id=0, turn_number=5, my_cash=30,  # Can't afford $50 fine
        my_position=10, my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=True, my_jail_turns=0, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    action = await agent.decide_jail_action(game_view)
    from monopoly.engine.types import JailAction
    assert action == JailAction.ROLL_DOUBLES


@pytest.mark.asyncio
async def test_random_agent_pre_roll_does_nothing(game_view):
    """Random agent does nothing in pre-roll phase."""
    agent = RandomAgent(player_id=0)

    action = await agent.decide_pre_roll(game_view)
    assert action.end_phase is True
    assert len(action.trades) == 0
    assert len(action.builds) == 0


@pytest.mark.asyncio
async def test_random_agent_post_roll_does_nothing(game_view):
    """Random agent does nothing in post-roll phase."""
    agent = RandomAgent(player_id=0)

    action = await agent.decide_post_roll(game_view)
    assert action.end_phase is True
    assert len(action.trades) == 0
    assert len(action.builds) == 0


@pytest.mark.asyncio
async def test_random_agent_bankruptcy_immediate(game_view):
    """Random agent immediately declares bankruptcy."""
    agent = RandomAgent(player_id=0)

    action = await agent.decide_bankruptcy_resolution(game_view, amount_owed=500)
    assert action.declare_bankruptcy is True
    assert len(action.sell_houses) == 0
    assert len(action.mortgage) == 0
