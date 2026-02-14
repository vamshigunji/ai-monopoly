"""Tests for context manager — public/private separation and sliding window."""

import pytest

from monopoly.agents.context import ChatMessage, ContextManager, PrivateThought


def test_context_manager_init():
    """Test context manager initialization."""
    def dummy_summarizer(messages):
        return "summary"

    ctx = ContextManager(agent_id=0, summarizer_fn=dummy_summarizer)
    assert ctx.agent_id == 0
    assert len(ctx.public_log) == 0
    assert len(ctx.private_log) == 0


def test_add_public_message():
    """Test adding public messages."""
    ctx = ContextManager(agent_id=0, summarizer_fn=lambda m: "")

    msg = ChatMessage(
        player_id=0,
        player_name="Test Agent",
        message="Hello world",
        turn_number=1,
        context="general",
    )
    ctx.add_public_message(msg)

    assert len(ctx.public_log) == 1
    assert ctx.public_log[0].message == "Hello world"


def test_add_private_thought():
    """Test adding private thoughts."""
    ctx = ContextManager(agent_id=0, summarizer_fn=lambda m: "")

    thought = PrivateThought(
        thought="I should buy Boardwalk",
        turn_number=1,
        category="strategy",
    )
    ctx.add_private_thought(thought)

    assert len(ctx.private_log) == 1
    assert ctx.private_log[0].thought == "I should buy Boardwalk"


@pytest.mark.asyncio
async def test_get_public_context_recent_only():
    """Test public context with only recent messages (no summarization)."""

    async def async_summarizer(m):
        return "summary"

    ctx = ContextManager(agent_id=0, summarizer_fn=async_summarizer)

    # Add 5 messages
    for i in range(5):
        ctx.add_public_message(
            ChatMessage(
                player_id=0,
                player_name="Agent",
                message=f"Message {i}",
                turn_number=i,
                context="general",
            )
        )

    # All 5 should appear verbatim (under the 10-message limit)
    context = await ctx.get_public_context(current_turn=5)
    assert "Message 0" in context
    assert "Message 4" in context
    assert "summary" not in context.lower()


@pytest.mark.asyncio
async def test_get_public_context_with_summarization():
    """Test public context triggers summarization for old messages."""
    summarized = False

    async def track_summarizer(messages):
        nonlocal summarized
        summarized = True
        return f"Summary of {len(messages)} messages"

    ctx = ContextManager(agent_id=0, summarizer_fn=track_summarizer)

    # Add 15 messages (exceeds 10-message window)
    for i in range(15):
        ctx.add_public_message(
            ChatMessage(
                player_id=0,
                player_name="Agent",
                message=f"Message {i}",
                turn_number=i,
                context="general",
            )
        )

    # Request context at turn 15 (should summarize turns 0-4, show 5-14 verbatim)
    context = await ctx.get_public_context(current_turn=15)

    assert summarized, "Summarizer should have been called"
    assert "Summary of" in context
    assert "Message 14" in context  # Most recent message should appear verbatim


def test_get_private_context_limits_to_5():
    """Test private context only includes last 5 thoughts."""
    ctx = ContextManager(agent_id=0, summarizer_fn=lambda m: "")

    # Add 10 thoughts
    for i in range(10):
        ctx.add_private_thought(
            PrivateThought(
                thought=f"Thought {i}",
                turn_number=i,
                category="strategy",
            )
        )

    context = ctx.get_private_context()

    # Only last 5 should appear
    assert "Thought 5" in context
    assert "Thought 9" in context
    assert "Thought 0" not in context
    assert "Thought 4" not in context


def test_get_private_context_empty():
    """Test private context when no thoughts exist."""
    ctx = ContextManager(agent_id=0, summarizer_fn=lambda m: "")

    context = ctx.get_private_context()
    assert "No previous strategic thoughts" in context


def test_clear():
    """Test clearing all context."""
    ctx = ContextManager(agent_id=0, summarizer_fn=lambda m: "")

    ctx.add_public_message(
        ChatMessage(0, "Agent", "Test", 1, "general")
    )
    ctx.add_private_thought(
        PrivateThought("Test thought", 1, "strategy")
    )

    ctx.clear()

    assert len(ctx.public_log) == 0
    assert len(ctx.private_log) == 0
    assert len(ctx.summaries) == 0
