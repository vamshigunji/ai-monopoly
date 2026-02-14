"""Context management for AI agents — public/private conversation history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ChatMessage:
    """A public speech message from an agent (visible to all agents)."""

    player_id: int
    player_name: str
    message: str
    turn_number: int
    context: str  # "negotiation", "reaction", "taunt", "general"


@dataclass
class PrivateThought:
    """A private thought from an agent (visible only to itself and debug UI)."""

    thought: str
    turn_number: int
    category: str  # "strategy", "valuation", "opponent_analysis",
    # "trade_evaluation", "risk_assessment"


class ContextManager:
    """Manages public and private context for an agent.

    Uses a sliding window strategy to keep prompt sizes manageable:
    - Last 10 turns of public conversation are included verbatim
    - Older public conversations are summarized in batches
    - Last 5 private thoughts are included verbatim
    - Older private thoughts are discarded (personality provides continuity)
    """

    MAX_PUBLIC_MESSAGES = 10  # Last N turns of public speech
    MAX_PRIVATE_THOUGHTS = 5  # Last N private thoughts

    def __init__(self, agent_id: int, summarizer_fn: Callable[[list[ChatMessage]], str]):
        """Initialize context manager.

        Args:
            agent_id: The ID of the agent this context belongs to
            summarizer_fn: Function to summarize old public messages.
                           Takes list[ChatMessage], returns summary string.
        """
        self.agent_id = agent_id
        self.public_log: list[ChatMessage] = []
        self.private_log: list[PrivateThought] = []
        self.summaries: list[str] = []
        self._summarizer = summarizer_fn
        self._last_summarized_turn = -1

    def add_public_message(self, message: ChatMessage) -> None:
        """Add a public message to the log."""
        self.public_log.append(message)

    def add_private_thought(self, thought: PrivateThought) -> None:
        """Add a private thought to the log."""
        self.private_log.append(thought)

    async def get_public_context(self, current_turn: int) -> str:
        """Build the public history string for the prompt.

        Returns recent messages verbatim, plus summaries of older messages.
        """
        # Recent entries: last 10 turns, verbatim
        recent_cutoff = max(0, current_turn - self.MAX_PUBLIC_MESSAGES)
        recent = [e for e in self.public_log if e.turn_number >= recent_cutoff]

        # Older entries: summarize if not already summarized
        older = [e for e in self.public_log if e.turn_number < recent_cutoff]
        if older and self._last_summarized_turn < recent_cutoff - 1:
            # Summarize messages we haven't summarized yet
            to_summarize = [
                e for e in older if e.turn_number > self._last_summarized_turn
            ]
            if to_summarize:
                summary = await self._summarizer(to_summarize)
                self.summaries.append(summary)
                self._last_summarized_turn = to_summarize[-1].turn_number

        # Build the context string
        parts = []
        if self.summaries:
            parts.append("Earlier in the game:")
            parts.extend(self.summaries)
            parts.append("")

        if recent:
            parts.append("Recent table talk:")
            for entry in recent:
                parts.append(
                    f"- Turn {entry.turn_number}, {entry.player_name}: \"{entry.message}\""
                )
        else:
            parts.append("(No recent table talk)")

        return "\n".join(parts)

    def get_private_context(self) -> str:
        """Build the private history string for the prompt.

        Returns the last 5 private thoughts.
        """
        recent = self.private_log[-self.MAX_PRIVATE_THOUGHTS :]
        if not recent:
            return "(No previous strategic thoughts)"

        lines = ["Your previous strategic thoughts:"]
        for entry in recent:
            lines.append(f"- Turn {entry.turn_number}: \"{entry.thought}\"")
        return "\n".join(lines)

    def get_all_public_messages(self) -> list[ChatMessage]:
        """Get all public messages (for testing/debugging)."""
        return self.public_log.copy()

    def get_all_private_thoughts(self) -> list[PrivateThought]:
        """Get all private thoughts (for testing/debugging)."""
        return self.private_log.copy()

    def clear(self) -> None:
        """Clear all context (for testing)."""
        self.public_log.clear()
        self.private_log.clear()
        self.summaries.clear()
        self._last_summarized_turn = -1
