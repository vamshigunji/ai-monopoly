"""Integration tests for FastAPI REST API endpoints.

Uses TestClient with manually-injected RandomAgent game runners
to avoid needing real LLM API keys.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from monopoly.agents.random_agent import RandomAgent
from monopoly.api.main import app
from monopoly.api.storage import game_storage
from monopoly.orchestrator.event_bus import EventBus
from monopoly.orchestrator.game_runner import GameRunner


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def game_id(client):
    """Create a game with RandomAgents and return its ID.

    Manually injects a GameRunner into storage since the
    /game/start endpoint requires real LLM API keys.
    """
    agents = [RandomAgent(i) for i in range(4)]
    event_bus = EventBus()
    runner = GameRunner(agents=agents, seed=42, speed=100.0, event_bus=event_bus)
    runner._running = True  # Simulate running state

    gid = "test-game-001"
    game_storage.add_game(gid, runner, event_bus)

    yield gid

    # Cleanup
    game_storage.remove_game(gid)


# ── Health / Root Endpoints ──


def test_root_endpoint(client):
    """Root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["service"] == "Monopoly AI Agents API"


def test_health_endpoint(client):
    """Health check returns healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ── List Games ──


def test_list_games_empty(client):
    """List games returns empty when no games exist."""
    response = client.get("/api/games")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["games"], list)
    assert data["count"] >= 0


def test_list_games_with_game(client, game_id):
    """List games includes an active game."""
    response = client.get("/api/games")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert game_id in data["games"]


# ── Game State ──


def test_get_state_valid_game(client, game_id):
    """Getting state of a valid game returns 200."""
    response = client.get(f"/api/game/{game_id}/state")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == game_id
    assert len(data["players"]) == 4
    assert data["turn_number"] >= 0
    assert len(data["board"]) == 40


def test_get_state_missing_game(client):
    """Getting state of a non-existent game returns 404."""
    response = client.get("/api/game/nonexistent/state")
    assert response.status_code == 404


# ── Game Agents ──


def test_get_agents_valid_game(client, game_id):
    """Getting agents of a valid game returns 200 with 4 agents."""
    response = client.get(f"/api/game/{game_id}/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == game_id
    assert len(data["agents"]) == 4
    # Each agent should have required fields
    for agent in data["agents"]:
        assert "name" in agent
        assert "model" in agent
        assert "personality" in agent


def test_get_agents_missing_game(client):
    """Getting agents of a non-existent game returns 404."""
    response = client.get("/api/game/nonexistent/agents")
    assert response.status_code == 404


# ── Speed Control ──


def test_set_speed_valid(client, game_id):
    """Setting a valid speed returns success."""
    response = client.post(f"/api/game/{game_id}/speed", json={"speed": 2.0})
    assert response.status_code == 200
    data = response.json()
    assert data["speed"] == 2.0


def test_set_speed_invalid(client, game_id):
    """Setting an invalid speed returns error (422 from Pydantic or 400 from route)."""
    response = client.post(f"/api/game/{game_id}/speed", json={"speed": 100.0})
    assert response.status_code in (400, 422)


def test_set_speed_missing_game(client):
    """Setting speed on non-existent game returns 404."""
    response = client.post("/api/game/nonexistent/speed", json={"speed": 1.0})
    assert response.status_code == 404
