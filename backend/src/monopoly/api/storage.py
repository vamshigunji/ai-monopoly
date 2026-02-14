"""In-memory storage for game sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from monopoly.engine.types import GameEvent
from monopoly.orchestrator.event_bus import EventBus
from monopoly.orchestrator.game_runner import GameRunner


@dataclass
class EnrichedEvent:
    """A game event enriched with timestamp and sequence number."""

    event: str  # Event type name (uppercase with underscores, e.g. DICE_ROLLED)
    data: dict[str, Any]
    timestamp: str  # ISO 8601
    turn_number: int
    sequence: int


class EventHistory:
    """Tracks event history for a game with sequence numbers."""

    def __init__(self) -> None:
        self._events: list[EnrichedEvent] = []
        self._sequence_counter: int = 0

    def add_event(self, event: GameEvent, turn_number: int) -> EnrichedEvent:
        """Add an event to history and return enriched version."""
        # Include player_id in data if not already there
        event_data = dict(event.data)
        if "player_id" not in event_data and event.player_id is not None:
            event_data["player_id"] = event.player_id

        enriched = EnrichedEvent(
            event=event.event_type.name,  # Keep uppercase to match frontend expectations
            data=event_data,
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            turn_number=turn_number,
            sequence=self._sequence_counter,
        )
        self._sequence_counter += 1
        self._events.append(enriched)
        return enriched

    def get_events(
        self,
        since: int = 0,
        limit: int = 1000,
        event_types: list[str] | None = None,
    ) -> list[EnrichedEvent]:
        """Get events from history with filtering."""
        filtered = [e for e in self._events if e.sequence >= since]

        if event_types:
            filtered = [e for e in filtered if e.event in event_types]

        return filtered[:limit]

    def get_event_count(self) -> int:
        """Get total number of events."""
        return len(self._events)


class GameStorage:
    """
    In-memory storage for active game sessions.

    Maps game_id → (GameRunner, EventBus, EventHistory, created_at)
    """

    def __init__(self) -> None:
        self._games: Dict[str, GameRunner] = {}
        self._event_buses: Dict[str, EventBus] = {}
        self._event_histories: Dict[str, EventHistory] = {}
        self._created_at: Dict[str, str] = {}

    def add_game(self, game_id: str, game_runner: GameRunner, event_bus: EventBus) -> None:
        """
        Add a new game session to storage.

        Args:
            game_id: Unique game identifier
            game_runner: GameRunner instance
            event_bus: EventBus instance
        """
        self._games[game_id] = game_runner
        self._event_buses[game_id] = event_bus
        self._event_histories[game_id] = EventHistory()
        self._created_at[game_id] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def get_game(self, game_id: str) -> GameRunner | None:
        """
        Get a game runner by ID.

        Args:
            game_id: Game identifier

        Returns:
            GameRunner if found, None otherwise
        """
        return self._games.get(game_id)

    def get_event_bus(self, game_id: str) -> EventBus | None:
        """
        Get an event bus by game ID.

        Args:
            game_id: Game identifier

        Returns:
            EventBus if found, None otherwise
        """
        return self._event_buses.get(game_id)

    def get_event_history(self, game_id: str) -> EventHistory | None:
        """
        Get event history by game ID.

        Args:
            game_id: Game identifier

        Returns:
            EventHistory if found, None otherwise
        """
        return self._event_histories.get(game_id)

    def get_created_at(self, game_id: str) -> str | None:
        """
        Get the creation timestamp for a game.

        Args:
            game_id: Game identifier

        Returns:
            ISO 8601 timestamp string if found, None otherwise
        """
        return self._created_at.get(game_id)

    def remove_game(self, game_id: str) -> None:
        """
        Remove a game from storage.

        Args:
            game_id: Game identifier
        """
        self._games.pop(game_id, None)
        self._event_buses.pop(game_id, None)
        self._event_histories.pop(game_id, None)
        self._created_at.pop(game_id, None)

    def list_games(self) -> list[str]:
        """
        Get list of all active game IDs.

        Returns:
            List of game ID strings
        """
        return list(self._games.keys())

    def count(self) -> int:
        """
        Get the number of active games.

        Returns:
            Number of games in storage
        """
        return len(self._games)


# Global storage instance
game_storage = GameStorage()
