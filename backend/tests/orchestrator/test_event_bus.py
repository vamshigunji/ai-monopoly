"""Tests for the EventBus publish-subscribe system."""

from __future__ import annotations

import asyncio
import pytest

from monopoly.engine.types import EventType, GameEvent
from monopoly.orchestrator.event_bus import EventBus, WILDCARD


class TestEventBusBasics:
    """Test basic subscription and emission functionality."""

    @pytest.mark.asyncio
    async def test_subscribe_and_emit(self):
        """Test that a subscribed callback receives emitted events."""
        bus = EventBus()
        received_events = []

        async def callback(event: GameEvent):
            received_events.append(event)

        await bus.subscribe(EventType.DICE_ROLLED, callback)

        event = GameEvent(
            event_type=EventType.DICE_ROLLED,
            player_id=0,
            data={"die1": 4, "die2": 3},
            turn_number=1,
        )
        await bus.emit(event)

        assert len(received_events) == 1
        assert received_events[0] == event

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self):
        """Test that multiple subscribers all receive the same event."""
        bus = EventBus()
        received_1 = []
        received_2 = []

        async def callback_1(event: GameEvent):
            received_1.append(event)

        async def callback_2(event: GameEvent):
            received_2.append(event)

        await bus.subscribe(EventType.PLAYER_MOVED, callback_1)
        await bus.subscribe(EventType.PLAYER_MOVED, callback_2)

        event = GameEvent(
            event_type=EventType.PLAYER_MOVED,
            player_id=1,
            data={"new_position": 7},
            turn_number=1,
        )
        await bus.emit(event)

        assert len(received_1) == 1
        assert len(received_2) == 1
        assert received_1[0] == event
        assert received_2[0] == event

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test that unsubscribed callbacks no longer receive events."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            received.append(event)

        await bus.subscribe(EventType.RENT_PAID, callback)

        # Emit first event
        event1 = GameEvent(
            event_type=EventType.RENT_PAID,
            player_id=0,
            data={"amount": 100},
            turn_number=1,
        )
        await bus.emit(event1)
        assert len(received) == 1

        # Unsubscribe
        await bus.unsubscribe(EventType.RENT_PAID, callback)

        # Emit second event
        event2 = GameEvent(
            event_type=EventType.RENT_PAID,
            player_id=0,
            data={"amount": 200},
            turn_number=2,
        )
        await bus.emit(event2)

        # Should still only have the first event
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_event_type_isolation(self):
        """Test that subscribers only receive events of their subscribed type."""
        bus = EventBus()
        dice_events = []
        move_events = []

        async def dice_callback(event: GameEvent):
            dice_events.append(event)

        async def move_callback(event: GameEvent):
            move_events.append(event)

        await bus.subscribe(EventType.DICE_ROLLED, dice_callback)
        await bus.subscribe(EventType.PLAYER_MOVED, move_callback)

        # Emit dice event
        dice_event = GameEvent(event_type=EventType.DICE_ROLLED, player_id=0, turn_number=1)
        await bus.emit(dice_event)

        # Emit move event
        move_event = GameEvent(event_type=EventType.PLAYER_MOVED, player_id=0, turn_number=1)
        await bus.emit(move_event)

        assert len(dice_events) == 1
        assert len(move_events) == 1
        assert dice_events[0].event_type == EventType.DICE_ROLLED
        assert move_events[0].event_type == EventType.PLAYER_MOVED


class TestWildcardSubscriptions:
    """Test wildcard subscription functionality."""

    @pytest.mark.asyncio
    async def test_wildcard_receives_all_events(self):
        """Test that wildcard subscribers receive all event types."""
        bus = EventBus()
        all_events = []

        async def wildcard_callback(event: GameEvent):
            all_events.append(event)

        await bus.subscribe(WILDCARD, wildcard_callback)

        # Emit various event types
        event1 = GameEvent(event_type=EventType.DICE_ROLLED, player_id=0, turn_number=1)
        event2 = GameEvent(event_type=EventType.PLAYER_MOVED, player_id=0, turn_number=1)
        event3 = GameEvent(event_type=EventType.PROPERTY_PURCHASED, player_id=1, turn_number=1)

        await bus.emit(event1)
        await bus.emit(event2)
        await bus.emit(event3)

        assert len(all_events) == 3
        assert all_events[0].event_type == EventType.DICE_ROLLED
        assert all_events[1].event_type == EventType.PLAYER_MOVED
        assert all_events[2].event_type == EventType.PROPERTY_PURCHASED

    @pytest.mark.asyncio
    async def test_wildcard_and_specific_subscribers(self):
        """Test that both wildcard and specific subscribers receive events."""
        bus = EventBus()
        all_events = []
        dice_events = []

        async def wildcard_callback(event: GameEvent):
            all_events.append(event)

        async def dice_callback(event: GameEvent):
            dice_events.append(event)

        await bus.subscribe(WILDCARD, wildcard_callback)
        await bus.subscribe(EventType.DICE_ROLLED, dice_callback)

        dice_event = GameEvent(event_type=EventType.DICE_ROLLED, player_id=0, turn_number=1)
        move_event = GameEvent(event_type=EventType.PLAYER_MOVED, player_id=0, turn_number=1)

        await bus.emit(dice_event)
        await bus.emit(move_event)

        # Wildcard subscriber receives both events
        assert len(all_events) == 2
        # Specific subscriber only receives dice event
        assert len(dice_events) == 1
        assert dice_events[0].event_type == EventType.DICE_ROLLED

    @pytest.mark.asyncio
    async def test_unsubscribe_wildcard(self):
        """Test unsubscribing from wildcard events."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            received.append(event)

        await bus.subscribe(WILDCARD, callback)

        event1 = GameEvent(event_type=EventType.TURN_STARTED, player_id=0, turn_number=1)
        await bus.emit(event1)
        assert len(received) == 1

        await bus.unsubscribe(WILDCARD, callback)

        event2 = GameEvent(event_type=EventType.TURN_STARTED, player_id=0, turn_number=2)
        await bus.emit(event2)
        assert len(received) == 1  # No new event received


class TestExceptionHandling:
    """Test that exceptions in callbacks don't break the event bus."""

    @pytest.mark.asyncio
    async def test_callback_exception_doesnt_affect_others(self):
        """Test that if one callback raises an exception, others still execute."""
        bus = EventBus()
        good_callback_invoked = []
        bad_callback_invoked = []

        async def bad_callback(event: GameEvent):
            bad_callback_invoked.append(event)
            raise ValueError("Intentional test error")

        async def good_callback(event: GameEvent):
            good_callback_invoked.append(event)

        await bus.subscribe(EventType.GAME_STARTED, bad_callback)
        await bus.subscribe(EventType.GAME_STARTED, good_callback)

        event = GameEvent(event_type=EventType.GAME_STARTED, turn_number=0)
        await bus.emit(event)

        # Both callbacks should have been invoked despite the exception
        assert len(bad_callback_invoked) == 1
        assert len(good_callback_invoked) == 1


class TestConcurrency:
    """Test concurrent event emission and subscription."""

    @pytest.mark.asyncio
    async def test_concurrent_emissions(self):
        """Test that concurrent event emissions are handled correctly."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            # Simulate some async work
            await asyncio.sleep(0.01)
            received.append(event)

        await bus.subscribe(EventType.AGENT_SPOKE, callback)

        # Emit multiple events concurrently
        events = [
            GameEvent(event_type=EventType.AGENT_SPOKE, player_id=i, turn_number=1)
            for i in range(5)
        ]

        await asyncio.gather(*[bus.emit(event) for event in events])

        assert len(received) == 5

    @pytest.mark.asyncio
    async def test_subscribe_during_emission(self):
        """Test that subscribing during emission doesn't cause issues."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            received.append(event)

        # Subscribe to one type
        await bus.subscribe(EventType.DICE_ROLLED, callback)

        # Emit an event
        event1 = GameEvent(event_type=EventType.DICE_ROLLED, player_id=0, turn_number=1)
        emission_task = asyncio.create_task(bus.emit(event1))

        # Subscribe to another type while emission is happening
        await bus.subscribe(EventType.PLAYER_MOVED, callback)

        await emission_task

        # Should have received the first event
        assert len(received) == 1


class TestSubscriberCount:
    """Test subscriber counting functionality."""

    @pytest.mark.asyncio
    async def test_subscriber_count_single_type(self):
        """Test counting subscribers for a specific event type."""
        bus = EventBus()

        async def callback1(event: GameEvent):
            pass

        async def callback2(event: GameEvent):
            pass

        assert bus.subscriber_count(EventType.DICE_ROLLED) == 0

        await bus.subscribe(EventType.DICE_ROLLED, callback1)
        assert bus.subscriber_count(EventType.DICE_ROLLED) == 1

        await bus.subscribe(EventType.DICE_ROLLED, callback2)
        assert bus.subscriber_count(EventType.DICE_ROLLED) == 2

    @pytest.mark.asyncio
    async def test_subscriber_count_wildcard(self):
        """Test counting wildcard subscribers."""
        bus = EventBus()

        async def callback(event: GameEvent):
            pass

        assert bus.subscriber_count(WILDCARD) == 0

        await bus.subscribe(WILDCARD, callback)
        assert bus.subscriber_count(WILDCARD) == 1

    @pytest.mark.asyncio
    async def test_subscriber_count_total(self):
        """Test counting total subscribers across all types."""
        bus = EventBus()

        async def callback(event: GameEvent):
            pass

        await bus.subscribe(EventType.DICE_ROLLED, callback)
        await bus.subscribe(EventType.PLAYER_MOVED, callback)
        await bus.subscribe(WILDCARD, callback)

        # Total should be 3 (one per subscription)
        assert bus.subscriber_count() == 3


class TestClearSubscribers:
    """Test clearing all subscribers."""

    @pytest.mark.asyncio
    async def test_clear_all_subscribers(self):
        """Test that clear_all_subscribers removes all subscriptions."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            received.append(event)

        await bus.subscribe(EventType.DICE_ROLLED, callback)
        await bus.subscribe(EventType.PLAYER_MOVED, callback)
        await bus.subscribe(WILDCARD, callback)

        assert bus.subscriber_count() == 3

        await bus.clear_all_subscribers()

        assert bus.subscriber_count() == 0
        assert bus.subscriber_count(EventType.DICE_ROLLED) == 0
        assert bus.subscriber_count(WILDCARD) == 0

        # Emit event and verify nothing is received
        event = GameEvent(event_type=EventType.DICE_ROLLED, player_id=0, turn_number=1)
        await bus.emit(event)
        assert len(received) == 0


class TestDuplicateSubscriptions:
    """Test handling of duplicate subscriptions."""

    @pytest.mark.asyncio
    async def test_no_duplicate_subscriptions(self):
        """Test that subscribing the same callback twice doesn't create duplicates."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            received.append(event)

        # Subscribe the same callback twice
        await bus.subscribe(EventType.GAME_STARTED, callback)
        await bus.subscribe(EventType.GAME_STARTED, callback)

        # Should only have one subscription
        assert bus.subscriber_count(EventType.GAME_STARTED) == 1

        event = GameEvent(event_type=EventType.GAME_STARTED, turn_number=0)
        await bus.emit(event)

        # Should only receive event once
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_safe_double_unsubscribe(self):
        """Test that unsubscribing twice doesn't cause errors."""
        bus = EventBus()

        async def callback(event: GameEvent):
            pass

        await bus.subscribe(EventType.GAME_OVER, callback)
        assert bus.subscriber_count(EventType.GAME_OVER) == 1

        # Unsubscribe twice
        await bus.unsubscribe(EventType.GAME_OVER, callback)
        await bus.unsubscribe(EventType.GAME_OVER, callback)

        # Should work without error
        assert bus.subscriber_count(EventType.GAME_OVER) == 0


class TestStringEventTypeConversion:
    """Test that string event types are converted to EventType enums."""

    @pytest.mark.asyncio
    async def test_subscribe_with_string(self):
        """Test subscribing with a string event type name."""
        bus = EventBus()
        received = []

        async def callback(event: GameEvent):
            received.append(event)

        # Subscribe using string
        await bus.subscribe("DICE_ROLLED", callback)

        event = GameEvent(event_type=EventType.DICE_ROLLED, player_id=0, turn_number=1)
        await bus.emit(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_with_string(self):
        """Test unsubscribing with a string event type name."""
        bus = EventBus()

        async def callback(event: GameEvent):
            pass

        await bus.subscribe(EventType.PLAYER_MOVED, callback)
        assert bus.subscriber_count(EventType.PLAYER_MOVED) == 1

        # Unsubscribe using string
        await bus.unsubscribe("PLAYER_MOVED", callback)
        assert bus.subscriber_count(EventType.PLAYER_MOVED) == 0

    @pytest.mark.asyncio
    async def test_subscriber_count_with_string(self):
        """Test counting subscribers with a string event type name."""
        bus = EventBus()

        async def callback(event: GameEvent):
            pass

        await bus.subscribe(EventType.RENT_PAID, callback)

        # Count using string
        assert bus.subscriber_count("RENT_PAID") == 1
