"""Integration tests for WebSocket endpoint.

Uses TestClient WebSocket support with manually-injected
RandomAgent game runners to avoid needing real LLM API keys.
"""

from __future__ import annotations

import json
import time

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
def game_id():
    """Create a game with RandomAgents and return its ID."""
    agents = [RandomAgent(i) for i in range(4)]
    event_bus = EventBus()
    runner = GameRunner(agents=agents, seed=42, speed=100.0, event_bus=event_bus)
    runner._running = True

    gid = "test-ws-game-001"
    game_storage.add_game(gid, runner, event_bus)

    yield gid

    game_storage.remove_game(gid)


# ── WebSocket Connection Tests ──


def test_websocket_connect_valid_game(client, game_id):
    """Connecting to a valid game should receive game_state_sync."""
    with client.websocket_connect(f"/ws/game/{game_id}") as ws:
        data = ws.receive_json()
        assert data["event"] == "game_state_sync"
        assert data["data"]["game_id"] == game_id
        assert len(data["data"]["players"]) == 4
        assert data["data"]["turn_number"] >= 0


def test_websocket_connect_invalid_game(client):
    """Connecting to a non-existent game should fail."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/game/nonexistent") as ws:
            ws.receive_json()


def test_websocket_sync_has_board(client, game_id):
    """The game_state_sync message should include board data."""
    with client.websocket_connect(f"/ws/game/{game_id}") as ws:
        data = ws.receive_json()
        assert "board" in data["data"]
        assert len(data["data"]["board"]) == 40
        # First space should be GO
        assert data["data"]["board"][0]["name"] == "GO"


def test_websocket_sync_has_bank(client, game_id):
    """The game_state_sync should include bank state."""
    with client.websocket_connect(f"/ws/game/{game_id}") as ws:
        data = ws.receive_json()
        bank = data["data"]["bank"]
        assert bank["houses_available"] == 32
        assert bank["hotels_available"] == 12


def test_websocket_speed_control(client, game_id):
    """Client can send speed control messages."""
    with client.websocket_connect(f"/ws/game/{game_id}") as ws:
        # Receive initial sync
        ws.receive_json()

        # Send speed change
        ws.send_json({"action": "set_speed", "data": {"speed": 3.0}})

        # Allow server to process the message
        time.sleep(0.1)

        # Verify speed was changed
        runner = game_storage.get_game(game_id)
        assert runner.speed == 3.0
