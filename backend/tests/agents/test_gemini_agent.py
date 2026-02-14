"""Tests for Gemini agent with mocked LLM calls."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from monopoly.agents.base import (
    BuildOrder,
    GameView,
    OpponentView,
    PostRollAction,
    PreRollAction,
)
from monopoly.agents.context import ContextManager
from monopoly.agents.gemini_agent import GeminiAgent
from monopoly.agents.personalities import PROFESSOR
from monopoly.engine.types import (
    ColorGroup,
    JailAction,
    PropertyData,
    TradeProposal,
)


@pytest.fixture
def game_view():
    """Create a standard game view for testing."""
    return GameView(
        my_player_id=1,
        turn_number=15,
        my_cash=1100,
        my_position=16,
        my_properties=[16, 18],
        my_houses={},
        my_mortgaged=set(),
        my_jail_cards=0,
        my_in_jail=False,
        my_jail_turns=0,
        opponents=[
            OpponentView(
                player_id=0,
                name="The Shark",
                cash=600,
                position=24,
                property_count=2,
                properties=[21, 23],
                is_bankrupt=False,
                in_jail=False,
                jail_cards=1,
                net_worth=1200,
            ),
            OpponentView(
                player_id=2,
                name="The Hustler",
                cash=900,
                position=5,
                property_count=2,
                properties=[5, 25],
                is_bankrupt=False,
                in_jail=False,
                jail_cards=0,
                net_worth=1300,
            ),
        ],
        property_ownership={16: 1, 18: 1, 21: 0, 23: 0, 5: 2, 25: 2},
        houses_on_board={},
        bank_houses_remaining=32,
        bank_hotels_remaining=12,
        last_dice_roll=None,
        recent_events=[],
    )


@pytest.fixture
def property_data():
    """Sample property data for testing."""
    return PropertyData(
        name="New York Avenue",
        position=19,
        color_group=ColorGroup.ORANGE,
        price=200,
        mortgage_value=100,
        rent=(16, 80, 220, 600, 800, 1000),
        house_cost=100,
    )


def _make_gemini_response(data: dict, prompt_tokens: int = 80, completion_tokens: int = 40):
    """Helper to create a mock Gemini response."""
    response = MagicMock()
    response.text = json.dumps(data)

    usage = MagicMock()
    usage.prompt_token_count = prompt_tokens
    usage.candidates_token_count = completion_tokens
    response.usage_metadata = usage

    return response


@pytest.fixture
def mock_genai_client():
    """Patch google.genai Client for the new SDK."""
    with patch("monopoly.agents.gemini_agent.genai") as mock_genai:
        mock_client = MagicMock()
        mock_aio = MagicMock()
        mock_aio_models = MagicMock()
        mock_aio.models = mock_aio_models
        mock_client.aio = mock_aio
        mock_genai.Client.return_value = mock_client
        yield mock_genai, mock_client, mock_aio_models


@pytest.fixture
def agent(mock_genai_client):
    """Create a Gemini agent with mocked client."""
    mock_genai, mock_client, mock_aio_models = mock_genai_client
    agent = GeminiAgent(
        player_id=1,
        personality=PROFESSOR,
        api_key="test-key",
    )
    return agent


# ── decide_buy_or_auction tests ──


@pytest.mark.asyncio
async def test_buy_decision_buy(agent, game_view, property_data):
    """Agent decides to buy a property."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "buy": True,
                "public_speech": "The expected ROI justifies this purchase.",
                "private_thought": "Orange group has highest ROI near jail.",
            }
        )
    )

    result = await agent.decide_buy_or_auction(game_view, property_data)
    assert result is True


@pytest.mark.asyncio
async def test_buy_decision_auction(agent, game_view, property_data):
    """Agent decides to auction a property."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "buy": False,
                "public_speech": "I'll pass at listed price.",
                "private_thought": "Better to acquire at auction below market.",
            }
        )
    )

    result = await agent.decide_buy_or_auction(game_view, property_data)
    assert result is False


@pytest.mark.asyncio
async def test_buy_decision_fallback_on_error(agent, game_view, property_data):
    """Agent falls back to heuristic when LLM fails."""
    agent.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    # Cash is $1100, price is $200, so 2x=$400 <= 1100 → should buy
    result = await agent.decide_buy_or_auction(game_view, property_data)
    assert result is True


# ── decide_auction_bid tests ──


@pytest.mark.asyncio
async def test_auction_bid(agent, game_view, property_data):
    """Agent places a bid."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "bid": 180,
                "public_speech": "I'll bid $180.",
                "private_thought": "NPV calculation supports this bid.",
            }
        )
    )

    result = await agent.decide_auction_bid(game_view, property_data, current_bid=150)
    assert result == 180


@pytest.mark.asyncio
async def test_auction_bid_exceeds_cash(agent, game_view, property_data):
    """Bid exceeding cash is capped to 0."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "bid": 9999,
                "public_speech": "All in.",
                "private_thought": "Going big.",
            }
        )
    )

    result = await agent.decide_auction_bid(game_view, property_data, current_bid=100)
    assert result == 0


@pytest.mark.asyncio
async def test_auction_bid_pass(agent, game_view, property_data):
    """Agent passes on auction."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "bid": 0,
                "public_speech": "I'll pass.",
                "private_thought": "Not worth the investment.",
            }
        )
    )

    result = await agent.decide_auction_bid(game_view, property_data, current_bid=250)
    assert result == 0


# ── decide_jail_action tests ──


@pytest.mark.asyncio
async def test_jail_action_pay_fine(agent):
    """Agent pays fine to leave jail."""
    jail_view = GameView(
        my_player_id=1, turn_number=15, my_cash=800, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=True, my_jail_turns=1, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "action": "pay_fine",
                "public_speech": "Paying the $50 fine is optimal.",
                "private_thought": "Opportunity cost of jail > $50.",
            }
        )
    )

    result = await agent.decide_jail_action(jail_view)
    assert result == JailAction.PAY_FINE


@pytest.mark.asyncio
async def test_jail_action_use_card(agent):
    """Agent uses Get Out of Jail Free card."""
    jail_view = GameView(
        my_player_id=1, turn_number=15, my_cash=800, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=1, my_in_jail=True, my_jail_turns=1, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "action": "use_card",
                "public_speech": "Using my card.",
                "private_thought": "Preserves $50 cash.",
            }
        )
    )

    result = await agent.decide_jail_action(jail_view)
    assert result == JailAction.USE_CARD


@pytest.mark.asyncio
async def test_jail_action_roll_doubles(agent):
    """Agent rolls doubles."""
    jail_view = GameView(
        my_player_id=1, turn_number=15, my_cash=800, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=True, my_jail_turns=1, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "action": "roll_doubles",
                "public_speech": "I'll try my luck.",
                "private_thought": "16.67% chance of doubles.",
            }
        )
    )

    result = await agent.decide_jail_action(jail_view)
    assert result == JailAction.ROLL_DOUBLES


# ── decide_trade tests ──


@pytest.mark.asyncio
async def test_trade_propose(agent, game_view):
    """Agent proposes a trade."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "propose_trade": True,
                "target_player": 0,
                "offer_properties": [16],
                "request_properties": [21],
                "offer_cash": 100,
                "request_cash": 0,
                "offer_jail_cards": 0,
                "request_jail_cards": 0,
                "public_speech": "A mutually beneficial exchange.",
                "private_thought": "Expected value favors this trade.",
            }
        )
    )

    result = await agent.decide_trade(game_view)
    assert result is not None
    assert result.proposer_id == 1
    assert result.receiver_id == 0
    assert result.offered_properties == [16]
    assert result.requested_properties == [21]
    assert result.offered_cash == 100


@pytest.mark.asyncio
async def test_trade_skip(agent, game_view):
    """Agent skips trading."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "propose_trade": False,
                "public_speech": "No trades at this time.",
                "private_thought": "Current portfolio is optimal.",
            }
        )
    )

    result = await agent.decide_trade(game_view)
    assert result is None


@pytest.mark.asyncio
async def test_trade_fallback_on_error(agent, game_view):
    """Agent returns None when LLM fails."""
    agent.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_trade(game_view)
    assert result is None


# ── respond_to_trade tests ──


@pytest.mark.asyncio
async def test_respond_trade_accept(agent, game_view):
    """Agent accepts a trade."""
    proposal = TradeProposal(
        proposer_id=0,
        receiver_id=1,
        offered_properties=[21],
        requested_properties=[16],
        offered_cash=50,
    )

    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "accept": True,
                "public_speech": "The math checks out. Accepted.",
                "private_thought": "Net positive expected value.",
            }
        )
    )

    result = await agent.respond_to_trade(game_view, proposal)
    assert result is True


@pytest.mark.asyncio
async def test_respond_trade_reject(agent, game_view):
    """Agent rejects a trade."""
    proposal = TradeProposal(
        proposer_id=0,
        receiver_id=1,
        offered_properties=[23],
        requested_properties=[16, 18],
    )

    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "accept": False,
                "public_speech": "The expected value is negative. Declined.",
                "private_thought": "Losing two oranges for one red is suboptimal.",
            }
        )
    )

    result = await agent.respond_to_trade(game_view, proposal)
    assert result is False


@pytest.mark.asyncio
async def test_respond_trade_fallback_on_error(agent, game_view):
    """Agent rejects trade when LLM fails."""
    agent.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    proposal = TradeProposal(proposer_id=0, receiver_id=1, offered_properties=[21])
    result = await agent.respond_to_trade(game_view, proposal)
    assert result is False


# ── decide_pre_roll tests ──


@pytest.mark.asyncio
async def test_pre_roll_no_actions(agent, game_view):
    """Agent does nothing before rolling."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "builds": [],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Proceeding to roll.",
                "private_thought": "No pre-roll actions needed.",
            }
        )
    )

    result = await agent.decide_pre_roll(game_view)
    assert isinstance(result, PreRollAction)
    assert len(result.builds) == 0
    assert result.mortgages == []
    assert result.unmortgages == []
    assert result.end_phase is True


@pytest.mark.asyncio
async def test_pre_roll_with_builds(agent, game_view):
    """Agent builds houses before rolling."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "builds": [
                    {"position": 16, "type": "house"},
                    {"position": 18, "type": "house"},
                ],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Building on orange for optimal ROI.",
                "private_thought": "Houses before roll maximizes rent income.",
            }
        )
    )

    result = await agent.decide_pre_roll(game_view)
    assert isinstance(result, PreRollAction)
    assert len(result.builds) == 2
    assert result.builds[0].position == 16
    assert result.builds[0].build_hotel is False
    assert result.builds[1].position == 18


@pytest.mark.asyncio
async def test_pre_roll_with_mortgage(agent, game_view):
    """Agent mortgages a property before rolling."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "builds": [],
                "mortgages": [18],
                "unmortgages": [],
                "public_speech": "Temporary liquidity adjustment.",
                "private_thought": "Mortgage to build cash reserves before roll.",
            }
        )
    )

    result = await agent.decide_pre_roll(game_view)
    assert result.mortgages == [18]
    assert len(result.builds) == 0


@pytest.mark.asyncio
async def test_pre_roll_fallback_on_error(agent, game_view):
    """Agent returns empty action when pre-roll LLM fails."""
    agent.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_pre_roll(game_view)
    assert isinstance(result, PreRollAction)
    assert len(result.builds) == 0
    assert result.end_phase is True


# ── decide_post_roll tests ──


@pytest.mark.asyncio
async def test_post_roll_with_builds(agent, game_view):
    """Agent builds houses after rolling."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "builds": [
                    {"position": 16, "type": "house"},
                    {"position": 18, "type": "house"},
                ],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Building on orange. Optimal ROI.",
                "private_thought": "Each house yields 15% expected return.",
            }
        )
    )

    result = await agent.decide_post_roll(game_view)
    assert isinstance(result, PostRollAction)
    assert len(result.builds) == 2
    assert result.builds[0].position == 16
    assert result.builds[0].build_hotel is False


@pytest.mark.asyncio
async def test_post_roll_with_mortgage(agent, game_view):
    """Agent mortgages after rolling."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "builds": [],
                "mortgages": [18],
                "unmortgages": [],
                "public_speech": "Temporary liquidity measure.",
                "private_thought": "Mortgage to build reserves.",
            }
        )
    )

    result = await agent.decide_post_roll(game_view)
    assert result.mortgages == [18]


@pytest.mark.asyncio
async def test_post_roll_hotel(agent, game_view):
    """Agent builds a hotel."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "builds": [{"position": 16, "type": "hotel"}],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Hotel on St. James. Maximum rent.",
                "private_thought": "Hotel yields best returns per dollar.",
            }
        )
    )

    result = await agent.decide_post_roll(game_view)
    assert len(result.builds) == 1
    assert result.builds[0].build_hotel is True


@pytest.mark.asyncio
async def test_post_roll_fallback_on_error(agent, game_view):
    """Agent returns empty action when LLM fails."""
    agent.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_post_roll(game_view)
    assert isinstance(result, PostRollAction)
    assert len(result.builds) == 0
    assert result.end_phase is True


# ── decide_bankruptcy_resolution tests ──


@pytest.mark.asyncio
async def test_bankruptcy_sell_and_mortgage(agent, game_view):
    """Agent sells houses and mortgages to survive."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "sell_houses": [16],
                "sell_hotels": [],
                "mortgage": [18],
                "declare_bankruptcy": False,
                "public_speech": "Restructuring assets.",
                "private_thought": "Selling and mortgaging to cover debt.",
            }
        )
    )

    result = await agent.decide_bankruptcy_resolution(game_view, amount_owed=400)
    assert result.sell_houses == [16]
    assert result.mortgage == [18]
    assert result.declare_bankruptcy is False


@pytest.mark.asyncio
async def test_bankruptcy_declare(agent, game_view):
    """Agent declares bankruptcy."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "sell_houses": [],
                "sell_hotels": [],
                "mortgage": [],
                "declare_bankruptcy": True,
                "public_speech": "The numbers don't work. I concede.",
                "private_thought": "Mathematically impossible to recover.",
            }
        )
    )

    result = await agent.decide_bankruptcy_resolution(game_view, amount_owed=5000)
    assert result.declare_bankruptcy is True


@pytest.mark.asyncio
async def test_bankruptcy_fallback_on_error(agent, game_view):
    """Agent declares bankruptcy when LLM fails."""
    agent.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_bankruptcy_resolution(game_view, amount_owed=500)
    assert result.declare_bankruptcy is True


# ── Context recording tests ──


@pytest.mark.asyncio
async def test_context_recorded_on_buy(agent, game_view, property_data):
    """Public speech and private thought are recorded after buy decision."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "buy": True,
                "public_speech": "Statistically sound purchase.",
                "private_thought": "Expected return exceeds cost.",
            }
        )
    )

    await agent.decide_buy_or_auction(game_view, property_data)

    public = agent.context.get_all_public_messages()
    private = agent.context.get_all_private_thoughts()
    assert len(public) == 1
    assert public[0].message == "Statistically sound purchase."
    assert len(private) == 1
    assert private[0].thought == "Expected return exceeds cost."


@pytest.mark.asyncio
async def test_context_recorded_on_trade(agent, game_view):
    """Context is recorded for trade decisions."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "propose_trade": False,
                "public_speech": "No profitable trades available.",
                "private_thought": "All trade proposals are NPV negative.",
            }
        )
    )

    await agent.decide_trade(game_view)

    public = agent.context.get_all_public_messages()
    assert len(public) == 1
    assert public[0].context == "negotiation"


# ── Token usage tracking tests ──


@pytest.mark.asyncio
async def test_token_usage_tracked(agent, game_view, property_data):
    """Token usage is accumulated across calls."""
    agent.client.aio.models.generate_content = AsyncMock(
        return_value=_make_gemini_response(
            {
                "buy": True,
                "public_speech": "Buying.",
                "private_thought": "Good.",
            },
            prompt_tokens=80,
            completion_tokens=40,
        )
    )

    await agent.decide_buy_or_auction(game_view, property_data)
    assert agent.token_usage["prompt_tokens"] == 80
    assert agent.token_usage["completion_tokens"] == 40

    # Second call accumulates
    await agent.decide_buy_or_auction(game_view, property_data)
    assert agent.token_usage["prompt_tokens"] == 160
    assert agent.token_usage["completion_tokens"] == 80
