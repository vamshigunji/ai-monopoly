"""Event bus for broadcasting game events to subscribers.

The EventBus implements a publish-subscribe pattern for distributing game events
to multiple consumers (e.g., WebSocket clients, logging systems, analytics).

Key features:
- Type-safe event subscriptions per EventType
- Wildcard subscriptions (subscribe to all events)
- Thread-safe async event handling using asyncio
- Automatic unsubscribe on consumer disconnect
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Awaitable

from monopoly.engine.types import EventType, GameEvent

logger = logging.getLogger(__name__)


# Type alias for event callbacks
EventCallback = Callable[[GameEvent], Awaitable[None]]

# Sentinel value for wildcard subscriptions
WILDCARD = "*"


class EventBus:
    """
    Async event bus for distributing game events to subscribers.

    The event bus maintains separate subscription lists for each event type,
    plus a wildcard subscription list for consumers that want all events.

    Thread-safety is achieved through asyncio's event loop, which guarantees
    that async operations are executed sequentially within a single thread.
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty subscription lists."""
        # Map of EventType -> list of callbacks
        self._subscribers: dict[EventType, list[EventCallback]] = defaultdict(list)
        # List of callbacks that receive all events
        self._wildcard_subscribers: list[EventCallback] = []
        # Lock for thread-safe modifications to subscriber lists
        self._lock = asyncio.Lock()

    async def subscribe(
        self,
        event_type: EventType | str,
        callback: EventCallback,
    ) -> None:
        """
        Register a callback to be invoked when events of a specific type are emitted.

        Args:
            event_type: The type of event to subscribe to, or "*" for all events.
            callback: An async function that accepts a GameEvent and returns None.
                      The callback should not raise exceptions; if it does, the
                      exception will be logged but will not affect other subscribers.

        Example:
            async def handle_dice_roll(event: GameEvent):
                print(f"Dice rolled: {event.data}")

            await bus.subscribe(EventType.DICE_ROLLED, handle_dice_roll)
        """
        async with self._lock:
            if event_type == WILDCARD:
                if callback not in self._wildcard_subscribers:
                    self._wildcard_subscribers.append(callback)
            else:
                if isinstance(event_type, str):
                    # Convert string to EventType if needed
                    event_type = EventType[event_type.upper()]
                if callback not in self._subscribers[event_type]:
                    self._subscribers[event_type].append(callback)

    async def unsubscribe(
        self,
        event_type: EventType | str,
        callback: EventCallback,
    ) -> None:
        """
        Remove a callback from the subscription list.

        Args:
            event_type: The event type to unsubscribe from, or "*" for wildcard.
            callback: The callback function to remove.

        Note:
            If the callback was not subscribed, this method does nothing.
            It's safe to call unsubscribe multiple times with the same callback.
        """
        async with self._lock:
            if event_type == WILDCARD:
                if callback in self._wildcard_subscribers:
                    self._wildcard_subscribers.remove(callback)
            else:
                if isinstance(event_type, str):
                    event_type = EventType[event_type.upper()]
                if event_type in self._subscribers:
                    if callback in self._subscribers[event_type]:
                        self._subscribers[event_type].remove(callback)

    async def emit(self, event: GameEvent) -> None:
        """
        Emit an event to all subscribers.

        This method invokes all callbacks registered for the event's type,
        plus all wildcard subscribers. Callbacks are executed concurrently
        using asyncio.gather().

        Args:
            event: The GameEvent to broadcast.

        Note:
            If a callback raises an exception, the exception is caught and logged,
            but other callbacks will still be invoked. The event bus guarantees
            best-effort delivery to all subscribers.

        Example:
            event = GameEvent(
                event_type=EventType.DICE_ROLLED,
                player_id=0,
                data={"die1": 4, "die2": 3, "total": 7, "doubles": False},
                turn_number=1,
            )
            await bus.emit(event)
        """
        # Gather all callbacks that should receive this event
        callbacks_to_invoke: list[EventCallback] = []

        async with self._lock:
            # Add type-specific subscribers
            if event.event_type in self._subscribers:
                callbacks_to_invoke.extend(self._subscribers[event.event_type])
            # Add wildcard subscribers
            callbacks_to_invoke.extend(self._wildcard_subscribers)

        # Invoke all callbacks concurrently
        if callbacks_to_invoke:
            # Create tasks for all callbacks
            tasks = [self._safe_invoke(callback, event) for callback in callbacks_to_invoke]
            # Wait for all callbacks to complete (or fail)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_invoke(self, callback: EventCallback, event: GameEvent) -> None:
        """
        Invoke a callback with exception handling.

        This wrapper ensures that exceptions in one callback don't affect others.
        Exceptions are logged but not re-raised.

        Args:
            callback: The callback to invoke.
            event: The event to pass to the callback.
        """
        try:
            await callback(event)
        except Exception as e:
            logger.warning(f"EventBus callback failed for {event.event_type}: {e}")

    async def clear_all_subscribers(self) -> None:
        """
        Remove all subscribers from the event bus.

        This is primarily useful for testing and cleanup when shutting down
        a game session.
        """
        async with self._lock:
            self._subscribers.clear()
            self._wildcard_subscribers.clear()

    def subscriber_count(self, event_type: EventType | str | None = None) -> int:
        """
        Get the number of subscribers for a specific event type or all subscribers.

        Args:
            event_type: The event type to count, "*" for wildcard count, or None for total.

        Returns:
            The number of subscribers.

        Note:
            This method is synchronous and does not acquire the lock, so the count
            may be stale if subscriptions are being modified concurrently. It's
            intended for debugging and monitoring, not for synchronization.
        """
        if event_type is None:
            # Count all subscribers across all types plus wildcards
            total = len(self._wildcard_subscribers)
            for subscribers in self._subscribers.values():
                total += len(subscribers)
            return total
        elif event_type == WILDCARD:
            return len(self._wildcard_subscribers)
        else:
            if isinstance(event_type, str):
                event_type = EventType[event_type.upper()]
            return len(self._subscribers.get(event_type, []))
