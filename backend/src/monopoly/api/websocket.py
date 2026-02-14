"""WebSocket endpoint for real-time game events."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from monopoly.api.storage import game_storage, EnrichedEvent
from monopoly.engine.types import GameEvent

websocket_router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for game event streaming.

    Each game can have multiple connected clients. When an event is emitted,
    all connected clients receive it.
    """

    def __init__(self) -> None:
        # Map game_id → list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str) -> None:
        """
        Accept a new WebSocket connection and subscribe to game events.

        Args:
            websocket: The WebSocket connection
            game_id: Game identifier
        """
        await websocket.accept()

        if game_id not in self.active_connections:
            self.active_connections[game_id] = []

        self.active_connections[game_id].append(websocket)

    def disconnect(self, websocket: WebSocket, game_id: str) -> bool:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            game_id: Game identifier

        Returns:
            True if this was the last connection for the game
        """
        if game_id in self.active_connections:
            if websocket in self.active_connections[game_id]:
                self.active_connections[game_id].remove(websocket)

            # Clean up empty lists
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
                return True

        return False

    async def send_event(self, game_id: str, event: dict[str, Any]) -> None:
        """
        Send an event to all connected clients for a game.

        Args:
            game_id: Game identifier
            event: Event data to send as JSON
        """
        if game_id not in self.active_connections:
            return

        # Send to all connections
        disconnected = []
        for connection in self.active_connections[game_id]:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(event)
                else:
                    disconnected.append(connection)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, game_id)


# Global connection manager
manager = ConnectionManager()


async def send_game_state_sync(websocket: WebSocket, game_id: str) -> None:
    """
    Send initial game state sync message to a newly connected client.

    Args:
        websocket: The WebSocket connection
        game_id: Game identifier
    """
    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        return

    # Get current game state
    state = game_runner.get_state()

    # Serialize board state
    board = []
    for i in range(40):
        space = game_runner.game.board.get_space(i)
        space_dict = {
            "position": i,
            "name": space.name,
            "type": space.space_type.name,
            "owner_id": state["property_ownership"].get(i),
            "houses": 0,
            "is_mortgaged": False,
        }
        # Add houses and mortgage status from player state
        for p in state["players"]:
            if i in p["mortgaged"]:
                space_dict["is_mortgaged"] = True
            if i in p["houses"]:
                space_dict["houses"] = p["houses"][i]
        board.append(space_dict)

    # Send as game_state_sync event
    sync_event = {
        "event": "game_state_sync",
        "data": {
            "game_id": game_id,
            "status": "in_progress" if game_runner._running else ("paused" if game_runner._paused else "finished"),
            "turn_number": state["turn_number"],
            "current_player_id": state["current_player"],
            "turn_phase": state["turn_phase"],
            "speed": game_runner.speed,
            "players": state["players"],
            "board": board,
            "bank": {
                "houses_available": state["bank_houses"],
                "hotels_available": state["bank_hotels"],
            },
            "last_roll": state["last_roll"],
        },
        "timestamp": game_storage.get_created_at(game_id),
        "turn_number": state["turn_number"],
        "sequence": 0,
    }

    await websocket.send_json(sync_event)


async def send_error_and_close(websocket: WebSocket, error: str, code: str, close_code: int = 1008) -> None:
    """
    Send an error message and close the WebSocket connection.

    Args:
        websocket: The WebSocket connection
        error: Human-readable error message
        code: Machine-readable error code
        close_code: WebSocket close code
    """
    error_event = {
        "event": "error",
        "data": {
            "error": error,
            "code": code,
        },
        "timestamp": "",
        "turn_number": 0,
        "sequence": -1,
    }

    try:
        await websocket.send_json(error_event)
    except Exception:
        pass

    try:
        await websocket.close(code=close_code)
    except Exception:
        pass


@websocket_router.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str) -> None:
    """
    WebSocket endpoint for real-time game events.

    URL: ws://localhost:8000/ws/game/{game_id}

    On connect:
    1. Validates that game_id exists
    2. Sends full game state as first message (game_state_sync event)
    3. Streams all subsequent game events in real time

    Client can send control messages:
    - {"action": "pause"}
    - {"action": "resume"}
    - {"action": "set_speed", "data": {"speed": 2.0}}
    """
    # Validate game exists
    game_runner = game_storage.get_game(game_id)
    event_bus = game_storage.get_event_bus(game_id)

    if not game_runner or not event_bus:
        await send_error_and_close(
            websocket,
            error="Game not found",
            code="GAME_NOT_FOUND",
            close_code=4404,
        )
        return

    # Accept connection
    await manager.connect(websocket, game_id)

    # Send initial state sync
    await send_game_state_sync(websocket, game_id)

    # Get event history to subscribe to new events
    event_history = game_storage.get_event_history(game_id)

    # Create event listener for this connection
    async def event_listener(event: GameEvent) -> None:
        """Forward events from event bus to WebSocket."""
        # Convert to enriched event
        if event_history:
            enriched = event_history.add_event(event, game_runner.game.turn_number)
            event_data = {
                "event": enriched.event,
                "data": enriched.data,
                "timestamp": enriched.timestamp,
                "turn_number": enriched.turn_number,
                "sequence": enriched.sequence,
            }
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(event_data)
            except Exception:
                # Connection closed, will be cleaned up
                pass

    # Subscribe to event bus
    await event_bus.subscribe("*", event_listener)

    try:
        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle control messages
                action = message.get("action")
                if action == "pause":
                    game_runner.pause()
                elif action == "resume":
                    game_runner.resume()
                elif action == "set_speed":
                    speed = message.get("data", {}).get("speed", 1.0)
                    if 0.25 <= speed <= 5.0:
                        game_runner.set_speed(speed)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Invalid JSON, ignore
                pass
            except Exception:
                # Other error, ignore and continue
                pass

    finally:
        # Cleanup
        await event_bus.unsubscribe("*", event_listener)
        was_last = manager.disconnect(websocket, game_id)

        # Stop the game when the last viewer disconnects (browser closed/refreshed)
        if was_last and game_runner._running:
            game_runner.stop()
            game_storage.remove_game(game_id)
