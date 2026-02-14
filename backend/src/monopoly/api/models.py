"""Pydantic models for API requests and responses."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── Request Models ──


class AgentConfig(BaseModel):
    """Configuration for a single AI agent."""

    name: str = Field(..., description="Display name for the agent")
    model: Literal["gpt-4o", "gpt-4o-mini", "gemini-2.0-flash", "gemini-pro", "gemini-flash"] = Field(
        ..., description="LLM model identifier"
    )
    personality: Literal["aggressive", "analytical", "charismatic", "conservative"] = Field(
        ..., description="Personality archetype"
    )
    avatar: str | None = Field(None, description="Avatar identifier for UI")
    color: str | None = Field(None, description="Hex color code")


class StartGameRequest(BaseModel):
    """Request to start a new game."""

    num_players: int = Field(4, ge=4, le=4, description="Number of players (always 4)")
    seed: int | None = Field(None, description="Random seed for deterministic replays")
    speed: float = Field(1.0, ge=0.25, le=5.0, description="Game speed multiplier")
    agents: list[AgentConfig] | None = Field(
        None, description="Agent configurations (must have exactly 4 if provided)"
    )


class SetSpeedRequest(BaseModel):
    """Request to change game speed."""

    speed: float = Field(..., ge=0.25, le=5.0, description="New speed multiplier")


# ── Response Models ──


class PlayerSummary(BaseModel):
    """Summary of a player's initial state."""

    id: int
    name: str
    model: str
    personality: str
    avatar: str
    color: str
    cash: int
    position: int


class StartGameResponse(BaseModel):
    """Response from starting a new game."""

    game_id: str
    players: list[PlayerSummary]
    status: Literal["in_progress"]
    seed: Optional[int] = None
    created_at: str


class DiceRoll(BaseModel):
    """Result of rolling two dice."""

    die1: int
    die2: int
    total: int
    doubles: bool


class PlayerState(BaseModel):
    """Complete state of a player."""

    id: int
    name: str
    position: int
    cash: int
    properties: list[int]
    houses: dict[str, int]
    mortgaged: list[int]
    in_jail: bool
    jail_turns: int
    get_out_of_jail_cards: int
    is_bankrupt: bool
    net_worth: int
    consecutive_doubles: int
    color: str
    avatar: str
    personality: str
    model: str | None = None


class BoardSpaceState(BaseModel):
    """State of a single board space."""

    position: int
    name: str
    type: str
    owner_id: int | None = None
    houses: int = 0
    is_mortgaged: bool = False
    color_group: str | None = None
    price: int | None = None
    rent_schedule: list[int] | None = None
    house_cost: int | None = None
    mortgage_value: int | None = None
    tax_amount: int | None = None


class BankState(BaseModel):
    """State of the bank's building inventory."""

    houses_available: int
    hotels_available: int


class GameState(BaseModel):
    """Complete game state."""

    game_id: str
    status: Literal["setup", "in_progress", "paused", "finished"]
    turn_number: int
    current_player_id: int
    turn_phase: str
    speed: float
    players: list[PlayerState]
    board: list[BoardSpaceState]
    bank: BankState
    last_roll: DiceRoll | None
    created_at: str | None = None


class GameEvent(BaseModel):
    """A game event from the event history."""

    event: str
    data: dict[str, Any]
    timestamp: str
    turn_number: int
    sequence: int


class GameHistoryResponse(BaseModel):
    """Response containing game event history."""

    game_id: str
    events: list[GameEvent]
    total_events: int
    has_more: bool


class GameControlResponse(BaseModel):
    """Response from pause/resume endpoints."""

    game_id: str
    status: Literal["in_progress", "paused", "finished"]
    turn_number: int


class SetSpeedResponse(BaseModel):
    """Response from speed change endpoint."""

    game_id: str
    speed: float


class AgentStyle(BaseModel):
    """Agent behavioral style parameters."""

    risk_tolerance: Literal["low", "medium", "high"]
    trading_aggression: Literal["low", "medium", "high", "very_high"]
    building_strategy: Literal["patient", "methodical", "opportunistic", "unpredictable"]
    speech_pattern: str


class AgentInfo(BaseModel):
    """Detailed information about an AI agent."""

    id: int
    name: str
    model: str
    personality: str
    avatar: str
    color: str
    description: str
    style: AgentStyle


class AgentsResponse(BaseModel):
    """Response containing all agent information."""

    game_id: str
    agents: list[AgentInfo]


# ── Error Models ──


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    code: str
    details: dict[str, Any] = Field(default_factory=dict)
