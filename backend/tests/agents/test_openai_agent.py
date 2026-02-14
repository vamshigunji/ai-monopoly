"""Tests for OpenAI agent with mocked LLM calls."""

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
from monopoly.agents.openai_agent import OpenAIAgent
from monopoly.agents.personalities import SHARK
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
        my_player_id=0,
        turn_number=10,
        my_cash=1000,
        my_position=24,
        my_properties=[21, 23],
        my_houses={},
        my_mortgaged=set(),
        my_jail_cards=1,
        my_in_jail=False,
        my_jail_turns=0,
        opponents=[
            OpponentView(
                player_id=1,
                name="The Professor",
                cash=1200,
                position=5,
                property_count=3,
                properties=[16, 18, 6],
                is_bankrupt=False,
                in_jail=False,
                jail_cards=0,
                net_worth=1800,
            ),
            OpponentView(
                player_id=2,
                name="The Hustler",
                cash=800,
                position=15,
                property_count=2,
                properties=[5, 25],
                is_bankrupt=False,
                in_jail=False,
                jail_cards=0,
                net_worth=1200,
            ),
        ],
        property_ownership={21: 0, 23: 0, 16: 1, 18: 1, 6: 1, 5: 2, 25: 2},
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
        name="Illinois Avenue",
        position=24,
        color_group=ColorGroup.RED,
        price=240,
        mortgage_value=120,
        rent=(20, 100, 300, 750, 925, 1100),
        house_cost=150,
    )


def _make_tool_call_response(arguments: dict, tool_name: str = "test"):
    """Helper to create a mock OpenAI tool call response."""
    tool_call = MagicMock()
    tool_call.function.arguments = json.dumps(arguments)
    tool_call.function.name = tool_name

    message = MagicMock()
    message.tool_calls = [tool_call]

    choice = MagicMock()
    choice.message = message

    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage

    return response


@pytest.fixture
def mock_openai_client():
    """Create a mocked OpenAI async client."""
    client = AsyncMock()
    return client


@pytest.fixture
def agent(mock_openai_client):
    """Create an OpenAI agent with mocked client."""
    with patch("monopoly.agents.openai_agent.openai.AsyncOpenAI") as mock_cls:
        mock_cls.return_value = mock_openai_client
        agent = OpenAIAgent(
            player_id=0,
            personality=SHARK,
            api_key="test-key",
        )
        agent.client = mock_openai_client
        return agent


# ── decide_buy_or_auction tests ──


@pytest.mark.asyncio
async def test_buy_decision_buy(agent, game_view, property_data, mock_openai_client):
    """Agent decides to buy a property."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "buy": True,
                "public_speech": "Mine now.",
                "private_thought": "Completes my red set.",
            },
            "buy_decision",
        )
    )

    result = await agent.decide_buy_or_auction(game_view, property_data)
    assert result is True


@pytest.mark.asyncio
async def test_buy_decision_auction(agent, game_view, property_data, mock_openai_client):
    """Agent decides to auction a property."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "buy": False,
                "public_speech": "Let's auction.",
                "private_thought": "Too expensive right now.",
            },
            "buy_decision",
        )
    )

    result = await agent.decide_buy_or_auction(game_view, property_data)
    assert result is False


@pytest.mark.asyncio
async def test_buy_decision_fallback_on_error(
    agent, game_view, property_data, mock_openai_client
):
    """Agent falls back to heuristic when LLM fails."""
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    # Cash is $1000, price is $240, so 2x=$480 <= 1000 → should buy
    result = await agent.decide_buy_or_auction(game_view, property_data)
    assert result is True


# ── decide_auction_bid tests ──


@pytest.mark.asyncio
async def test_auction_bid(agent, game_view, property_data, mock_openai_client):
    """Agent places a bid."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "bid": 200,
                "public_speech": "Two hundred.",
                "private_thought": "Worth it for the reds.",
            },
            "auction_bid_decision",
        )
    )

    result = await agent.decide_auction_bid(game_view, property_data, current_bid=150)
    assert result == 200


@pytest.mark.asyncio
async def test_auction_bid_exceeds_cash(
    agent, game_view, property_data, mock_openai_client
):
    """Agent bid exceeding cash is capped to 0."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "bid": 5000,
                "public_speech": "All in!",
                "private_thought": "Going big.",
            },
            "auction_bid_decision",
        )
    )

    result = await agent.decide_auction_bid(game_view, property_data, current_bid=100)
    assert result == 0  # Rejected: bid > cash


@pytest.mark.asyncio
async def test_auction_bid_pass(agent, game_view, property_data, mock_openai_client):
    """Agent passes on auction."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "bid": 0,
                "public_speech": "Not interested.",
                "private_thought": "Too rich for me.",
            },
            "auction_bid_decision",
        )
    )

    result = await agent.decide_auction_bid(game_view, property_data, current_bid=300)
    assert result == 0


# ── decide_jail_action tests ──


@pytest.mark.asyncio
async def test_jail_action_pay_fine(agent, mock_openai_client):
    """Agent pays fine to leave jail."""
    jail_view = GameView(
        my_player_id=0, turn_number=10, my_cash=500, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=True, my_jail_turns=1, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "action": "pay_fine",
                "public_speech": "I'm out.",
                "private_thought": "Need to keep moving.",
            },
            "jail_action_decision",
        )
    )

    result = await agent.decide_jail_action(jail_view)
    assert result == JailAction.PAY_FINE


@pytest.mark.asyncio
async def test_jail_action_use_card(agent, mock_openai_client):
    """Agent uses Get Out of Jail Free card."""
    jail_view = GameView(
        my_player_id=0, turn_number=10, my_cash=500, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=1, my_in_jail=True, my_jail_turns=1, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "action": "use_card",
                "public_speech": "Playing my card.",
                "private_thought": "Save the $50.",
            },
            "jail_action_decision",
        )
    )

    result = await agent.decide_jail_action(jail_view)
    assert result == JailAction.USE_CARD


@pytest.mark.asyncio
async def test_jail_action_roll_doubles(agent, mock_openai_client):
    """Agent tries to roll doubles."""
    jail_view = GameView(
        my_player_id=0, turn_number=10, my_cash=500, my_position=10,
        my_properties=[], my_houses={}, my_mortgaged=set(),
        my_jail_cards=0, my_in_jail=True, my_jail_turns=1, opponents=[],
        property_ownership={}, houses_on_board={}, bank_houses_remaining=32,
        bank_hotels_remaining=12, last_dice_roll=None, recent_events=[],
    )

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "action": "roll_doubles",
                "public_speech": "Let's try my luck.",
                "private_thought": "Save cash if possible.",
            },
            "jail_action_decision",
        )
    )

    result = await agent.decide_jail_action(jail_view)
    assert result == JailAction.ROLL_DOUBLES


# ── decide_trade tests ──


@pytest.mark.asyncio
async def test_trade_propose(agent, game_view, mock_openai_client):
    """Agent proposes a trade."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "propose_trade": True,
                "target_player": 1,
                "offer_properties": [21],
                "request_properties": [16],
                "offer_cash": 50,
                "request_cash": 0,
                "offer_jail_cards": 0,
                "request_jail_cards": 0,
                "public_speech": "How about a deal, Professor?",
                "private_thought": "I need orange more than red right now.",
            },
            "trade_decision",
        )
    )

    result = await agent.decide_trade(game_view)
    assert result is not None
    assert result.proposer_id == 0
    assert result.receiver_id == 1
    assert result.offered_properties == [21]
    assert result.requested_properties == [16]
    assert result.offered_cash == 50


@pytest.mark.asyncio
async def test_trade_skip(agent, game_view, mock_openai_client):
    """Agent skips trading."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "propose_trade": False,
                "public_speech": "Not now.",
                "private_thought": "No good trades available.",
            },
            "trade_decision",
        )
    )

    result = await agent.decide_trade(game_view)
    assert result is None


@pytest.mark.asyncio
async def test_trade_fallback_on_error(agent, game_view, mock_openai_client):
    """Agent returns None when trade LLM call fails."""
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_trade(game_view)
    assert result is None


# ── respond_to_trade tests ──


@pytest.mark.asyncio
async def test_respond_trade_accept(agent, game_view, mock_openai_client):
    """Agent accepts a trade."""
    proposal = TradeProposal(
        proposer_id=1,
        receiver_id=0,
        offered_properties=[16],
        requested_properties=[21],
        offered_cash=100,
    )

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "accept": True,
                "public_speech": "Deal.",
                "private_thought": "Good value for me.",
            },
            "trade_response_decision",
        )
    )

    result = await agent.respond_to_trade(game_view, proposal)
    assert result is True


@pytest.mark.asyncio
async def test_respond_trade_reject(agent, game_view, mock_openai_client):
    """Agent rejects a trade."""
    proposal = TradeProposal(
        proposer_id=1,
        receiver_id=0,
        offered_properties=[6],
        requested_properties=[21, 23],
    )

    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "accept": False,
                "public_speech": "No chance.",
                "private_thought": "Terrible deal.",
            },
            "trade_response_decision",
        )
    )

    result = await agent.respond_to_trade(game_view, proposal)
    assert result is False


@pytest.mark.asyncio
async def test_respond_trade_fallback_on_error(agent, game_view, mock_openai_client):
    """Agent rejects trade when LLM fails."""
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    proposal = TradeProposal(proposer_id=1, receiver_id=0, offered_properties=[6])
    result = await agent.respond_to_trade(game_view, proposal)
    assert result is False


# ── decide_pre_roll tests ──


@pytest.mark.asyncio
async def test_pre_roll_no_actions(agent, game_view, mock_openai_client):
    """Agent does nothing before rolling."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "builds": [],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Let's roll.",
                "private_thought": "No actions needed.",
            },
            "pre_roll_decision",
        )
    )

    result = await agent.decide_pre_roll(game_view)
    assert isinstance(result, PreRollAction)
    assert len(result.builds) == 0
    assert result.mortgages == []
    assert result.unmortgages == []
    assert result.end_phase is True


@pytest.mark.asyncio
async def test_pre_roll_with_builds(agent, game_view, mock_openai_client):
    """Agent builds houses before rolling."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "builds": [
                    {"position": 21, "type": "house"},
                    {"position": 23, "type": "house"},
                ],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Building up my reds.",
                "private_thought": "Houses before roll to maximize rent.",
            },
            "pre_roll_decision",
        )
    )

    result = await agent.decide_pre_roll(game_view)
    assert isinstance(result, PreRollAction)
    assert len(result.builds) == 2
    assert result.builds[0].position == 21
    assert result.builds[0].build_hotel is False
    assert result.builds[1].position == 23


@pytest.mark.asyncio
async def test_pre_roll_with_mortgage(agent, game_view, mock_openai_client):
    """Agent mortgages a property before rolling."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "builds": [],
                "mortgages": [23],
                "unmortgages": [],
                "public_speech": "Need some liquidity.",
                "private_thought": "Mortgage before rolling to have cash reserves.",
            },
            "pre_roll_decision",
        )
    )

    result = await agent.decide_pre_roll(game_view)
    assert result.mortgages == [23]
    assert len(result.builds) == 0


@pytest.mark.asyncio
async def test_pre_roll_fallback_on_error(agent, game_view, mock_openai_client):
    """Agent returns empty action when pre-roll LLM fails."""
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_pre_roll(game_view)
    assert isinstance(result, PreRollAction)
    assert len(result.builds) == 0
    assert result.end_phase is True


# ── decide_post_roll tests ──


@pytest.mark.asyncio
async def test_post_roll_with_builds(agent, game_view, mock_openai_client):
    """Agent builds houses after rolling."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "builds": [
                    {"position": 21, "type": "house"},
                    {"position": 23, "type": "house"},
                ],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Building time.",
                "private_thought": "Houses on reds will pay off.",
            },
            "post_roll_decision",
        )
    )

    result = await agent.decide_post_roll(game_view)
    assert isinstance(result, PostRollAction)
    assert len(result.builds) == 2
    assert result.builds[0].position == 21
    assert result.builds[0].build_hotel is False
    assert result.builds[1].position == 23


@pytest.mark.asyncio
async def test_post_roll_with_mortgage(agent, game_view, mock_openai_client):
    """Agent mortgages properties after rolling."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "builds": [],
                "mortgages": [21],
                "unmortgages": [],
                "public_speech": "Need some cash.",
                "private_thought": "Mortgage to fund future building.",
            },
            "post_roll_decision",
        )
    )

    result = await agent.decide_post_roll(game_view)
    assert result.mortgages == [21]
    assert len(result.builds) == 0


@pytest.mark.asyncio
async def test_post_roll_hotel(agent, game_view, mock_openai_client):
    """Agent builds a hotel."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "builds": [{"position": 21, "type": "hotel"}],
                "mortgages": [],
                "unmortgages": [],
                "public_speech": "Hotel time!",
                "private_thought": "Max rent on Kentucky.",
            },
            "post_roll_decision",
        )
    )

    result = await agent.decide_post_roll(game_view)
    assert len(result.builds) == 1
    assert result.builds[0].build_hotel is True


@pytest.mark.asyncio
async def test_post_roll_fallback_on_error(agent, game_view, mock_openai_client):
    """Agent returns empty action when post-roll LLM fails."""
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_post_roll(game_view)
    assert isinstance(result, PostRollAction)
    assert len(result.builds) == 0
    assert result.end_phase is True


# ── decide_bankruptcy_resolution tests ──


@pytest.mark.asyncio
async def test_bankruptcy_sell_and_mortgage(agent, game_view, mock_openai_client):
    """Agent sells houses and mortgages to raise funds."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "sell_houses": [21],
                "sell_hotels": [],
                "mortgage": [23],
                "declare_bankruptcy": False,
                "public_speech": "I'm not done yet.",
                "private_thought": "Selling to survive.",
            },
            "bankruptcy_decision",
        )
    )

    result = await agent.decide_bankruptcy_resolution(game_view, amount_owed=500)
    assert result.sell_houses == [21]
    assert result.mortgage == [23]
    assert result.declare_bankruptcy is False


@pytest.mark.asyncio
async def test_bankruptcy_declare(agent, game_view, mock_openai_client):
    """Agent declares bankruptcy."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "sell_houses": [],
                "sell_hotels": [],
                "mortgage": [],
                "declare_bankruptcy": True,
                "public_speech": "I'm out.",
                "private_thought": "Can't recover from this.",
            },
            "bankruptcy_decision",
        )
    )

    result = await agent.decide_bankruptcy_resolution(game_view, amount_owed=2000)
    assert result.declare_bankruptcy is True


@pytest.mark.asyncio
async def test_bankruptcy_fallback_on_error(agent, game_view, mock_openai_client):
    """Agent declares bankruptcy when LLM fails."""
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await agent.decide_bankruptcy_resolution(game_view, amount_owed=500)
    assert result.declare_bankruptcy is True


# ── Context recording tests ──


@pytest.mark.asyncio
async def test_context_recorded_on_buy(
    agent, game_view, property_data, mock_openai_client
):
    """Public speech and private thought are recorded after buy decision."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "buy": True,
                "public_speech": "I'll take it.",
                "private_thought": "Good investment.",
            },
            "buy_decision",
        )
    )

    await agent.decide_buy_or_auction(game_view, property_data)

    public = agent.context.get_all_public_messages()
    private = agent.context.get_all_private_thoughts()
    assert len(public) == 1
    assert public[0].message == "I'll take it."
    assert len(private) == 1
    assert private[0].thought == "Good investment."


@pytest.mark.asyncio
async def test_context_recorded_on_trade(agent, game_view, mock_openai_client):
    """Public speech and private thought are recorded after trade decision."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "propose_trade": False,
                "public_speech": "No deals today.",
                "private_thought": "Waiting for better options.",
            },
            "trade_decision",
        )
    )

    await agent.decide_trade(game_view)

    public = agent.context.get_all_public_messages()
    assert len(public) == 1
    assert public[0].message == "No deals today."
    assert public[0].context == "negotiation"


# ── Token usage tracking tests ──


@pytest.mark.asyncio
async def test_token_usage_tracked(
    agent, game_view, property_data, mock_openai_client
):
    """Token usage is accumulated across calls."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_tool_call_response(
            {
                "buy": True,
                "public_speech": "Mine.",
                "private_thought": "Good.",
            },
            "buy_decision",
        )
    )

    await agent.decide_buy_or_auction(game_view, property_data)
    assert agent.token_usage["prompt_tokens"] == 100
    assert agent.token_usage["completion_tokens"] == 50

    # Second call accumulates
    await agent.decide_buy_or_auction(game_view, property_data)
    assert agent.token_usage["prompt_tokens"] == 200
    assert agent.token_usage["completion_tokens"] == 100
