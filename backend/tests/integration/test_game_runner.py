"""Integration tests for GameRunner with RandomAgents.

These tests exercise the full game loop without LLM calls.
"""

from __future__ import annotations

import asyncio

import pytest

from monopoly.agents.random_agent import RandomAgent
from monopoly.engine.types import EventType, GameEvent
from monopoly.orchestrator.event_bus import EventBus
from monopoly.orchestrator.game_runner import GameRunner


@pytest.fixture
def random_agents():
    """Create 4 RandomAgents."""
    return [RandomAgent(i) for i in range(4)]


@pytest.fixture
def event_bus():
    """Create a fresh EventBus."""
    return EventBus()


@pytest.fixture
def game_runner(random_agents, event_bus):
    """Create a GameRunner with RandomAgents and event bus."""
    return GameRunner(agents=random_agents, seed=42, speed=10.0, event_bus=event_bus)


# ── Full Game Tests ──


@pytest.mark.asyncio
async def test_full_game_completes_within_max_turns(random_agents):
    """A game with RandomAgents should complete within max_turns."""
    runner = GameRunner(agents=random_agents, seed=42, speed=100.0)
    result = await runner.run_game(max_turns=50)

    assert result["completed"] is True
    assert result["turns"] <= 50
    assert result["stats"].turns_completed > 0


@pytest.mark.asyncio
async def test_full_game_deterministic_with_seed(random_agents):
    """Two games with the same seed produce the same number of turns."""
    agents1 = [RandomAgent(i) for i in range(4)]
    agents2 = [RandomAgent(i) for i in range(4)]

    runner1 = GameRunner(agents=agents1, seed=123, speed=100.0)
    runner2 = GameRunner(agents=agents2, seed=123, speed=100.0)

    result1 = await runner1.run_game(max_turns=30)
    result2 = await runner2.run_game(max_turns=30)

    assert result1["turns"] == result2["turns"]


@pytest.mark.asyncio
async def test_game_tracks_properties_purchased(random_agents):
    """Stats should track property purchases over the course of a game."""
    runner = GameRunner(agents=random_agents, seed=42, speed=100.0)
    result = await runner.run_game(max_turns=30)

    assert result["stats"].properties_purchased >= 0
    assert result["stats"].turns_completed > 0


# ── Event Bus Integration ──


@pytest.mark.asyncio
async def test_events_emitted_to_bus(random_agents, event_bus):
    """Events should be emitted through the event bus during gameplay."""
    received_events = []

    async def listener(event: GameEvent) -> None:
        received_events.append(event)

    await event_bus.subscribe("*", listener)

    runner = GameRunner(agents=random_agents, seed=42, speed=100.0, event_bus=event_bus)
    await runner.run_game(max_turns=10)

    # Allow event bus tasks to complete
    await asyncio.sleep(0.1)

    assert len(received_events) > 0
    event_types = {e.event_type for e in received_events}
    assert EventType.GAME_STARTED in event_types
    assert EventType.TURN_STARTED in event_types
    assert EventType.DICE_ROLLED in event_types


# ── Game State Queries ──


@pytest.mark.asyncio
async def test_get_state_returns_valid_state(game_runner):
    """get_state should return complete game state."""
    state = game_runner.get_state()

    assert "turn_number" in state
    assert "current_player" in state
    assert "players" in state
    assert len(state["players"]) == 4
    assert state["bank_houses"] == 32
    assert state["bank_hotels"] == 12

    # Each player should start with $1500
    for p in state["players"]:
        assert p["cash"] == 1500
        assert p["position"] == 0
        assert p["is_bankrupt"] is False


@pytest.mark.asyncio
async def test_get_state_after_turns(random_agents):
    """State should reflect changes after running turns."""
    runner = GameRunner(agents=random_agents, seed=42, speed=100.0)
    await runner.run_game(max_turns=10)

    state = runner.get_state()
    assert state["turn_number"] > 0

    # At least some players should have moved from position 0
    moved = any(p["position"] != 0 for p in state["players"])
    assert moved


# ── Speed Control ──


def test_set_speed_valid(game_runner):
    """Setting a valid speed should update the speed."""
    game_runner.set_speed(2.5)
    assert game_runner.speed == 2.5


def test_set_speed_bounds(game_runner):
    """Setting speed outside bounds should raise ValueError."""
    with pytest.raises(ValueError):
        game_runner.set_speed(0.05)
    with pytest.raises(ValueError):
        game_runner.set_speed(15.0)


# ── Pause / Resume ──


def test_pause_sets_flag(game_runner):
    """Pausing should set the pause flag."""
    game_runner.pause()
    assert game_runner._paused is True


def test_resume_clears_flag(game_runner):
    """Resuming should clear the pause flag."""
    game_runner.pause()
    game_runner.resume()
    assert game_runner._paused is False


# ── Agent count validation ──


def test_wrong_agent_count_raises():
    """GameRunner should reject non-4 agent lists."""
    with pytest.raises(ValueError, match="Expected 4 agents"):
        GameRunner(agents=[RandomAgent(0), RandomAgent(1)], seed=42)
