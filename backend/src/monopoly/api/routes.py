"""REST API routes for Monopoly AI Agents."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

from monopoly.api.models import (
    AgentConfig,
    AgentInfo,
    AgentsResponse,
    ErrorResponse,
    GameControlResponse,
    GameHistoryResponse,
    GameState,
    SetSpeedRequest,
    SetSpeedResponse,
    StartGameRequest,
    StartGameResponse,
)
from monopoly.api.storage import game_storage
from monopoly.agents.gemini_agent import GeminiAgent
from monopoly.agents.openai_agent import OpenAIAgent
from monopoly.agents.personalities import PERSONALITIES, get_personality
from monopoly.engine.game import Game
from monopoly.orchestrator.event_bus import EventBus
from monopoly.orchestrator.game_runner import GameRunner

router = APIRouter()


# ── Helper Functions ──


def create_agent_from_config(player_id: int, config: AgentConfig | None = None, event_bus = None):
    """Create an AI agent from configuration."""
    # Use default personality if no config provided
    if config is None:
        personality = get_personality(player_id)
        # Map full model names to API model names
        model_map = {
            "gemini-2.0-flash": "gemini-flash",
            "gemini-2.0-flash": "gemini-flash",
        }
        api_model = model_map.get(personality.model, personality.model)

        config = AgentConfig(
            name=personality.name,
            model=api_model,
            personality=personality.archetype.split()[0].lower(),
            avatar=personality.avatar,
            color=personality.color,
        )

    # Get personality config
    personality = get_personality(player_id)

    # Map model string to agent class
    import os
    if config.model in ["gpt-4o", "gpt-4o-mini"]:
        return OpenAIAgent(
            player_id=player_id,
            personality=personality,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            event_bus=event_bus,
        )
    elif config.model in ["gemini-pro", "gemini-flash", "gemini-2.0-flash"]:
        return GeminiAgent(
            player_id=player_id,
            personality=personality,
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            event_bus=event_bus,
        )
    else:
        raise ValueError(f"Unknown model: {config.model}")


def serialize_player_summary(player_id: int, config: AgentConfig) -> dict[str, Any]:
    """Serialize a player summary for the start game response."""
    return {
        "id": player_id,
        "name": config.name,
        "model": config.model,
        "personality": config.personality,
        "avatar": config.avatar or "default",
        "color": config.color or "#CCCCCC",
        "cash": 1500,
        "position": 0,
    }


# ── Endpoints ──


@router.get("/games")
async def list_games() -> dict[str, Any]:
    """
    List all active games in storage.

    Useful for debugging and monitoring.
    """
    games = game_storage.list_games()
    return {
        "games": games,
        "count": len(games),
    }


@router.post("/game/start", response_model=StartGameResponse, status_code=201)
async def start_game(request: StartGameRequest) -> StartGameResponse:
    """
    Start a new Monopoly game with 4 AI agents.

    Creates a new game instance, initializes agents, and starts the game loop
    in the background.
    """
    # Validate request
    if request.num_players != 4:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Only 4-player games are supported",
                code="INVALID_PLAYER_COUNT",
                details={"num_players": request.num_players},
            ).model_dump(),
        )

    if request.agents and len(request.agents) != 4:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Must provide exactly 4 agent configurations, got {len(request.agents)}",
                code="INVALID_AGENT_CONFIG",
                details={"agent_count": len(request.agents)},
            ).model_dump(),
        )

    # Generate game ID
    game_id = str(uuid.uuid4())

    # Create event bus first (needed for agents)
    event_bus = EventBus()

    # Create agent configurations
    agent_configs = request.agents or [None] * 4
    agents = []
    player_summaries = []

    try:
        for i, agent_config in enumerate(agent_configs):
            # Get or create config
            if agent_config is None:
                personality = get_personality(i)
                # Map full model names to API model names
                model_map = {
                    "gemini-2.0-flash": "gemini-flash",
                    "gemini-2.0-flash": "gemini-flash",
                }
                api_model = model_map.get(personality.model, personality.model)

                agent_config = AgentConfig(
                    name=personality.name,
                    model=api_model,
                    personality=personality.archetype.split()[0].lower(),
                    avatar=personality.avatar,
                    color=personality.color,
                )

            # Create agent with event_bus
            agent = create_agent_from_config(i, agent_config, event_bus)
            agents.append(agent)

            # Create player summary
            player_summaries.append(serialize_player_summary(i, agent_config))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=f"Failed to create agents: {str(e)}",
                code="GAME_CREATION_FAILED",
                details={"error": str(e)},
            ).model_dump(),
        )

    # Create game engine
    try:
        game_runner = GameRunner(
            agents=agents,
            seed=request.seed,
            speed=request.speed,
            event_bus=event_bus,
        )

        # Store game runner
        game_storage.add_game(game_id, game_runner, event_bus)

        # Set up event history listener
        event_history = game_storage.get_event_history(game_id)

        async def history_listener(event: Any) -> None:
            """Add events to history."""
            if event_history:
                event_history.add_event(event, game_runner.game.turn_number)

        await event_bus.subscribe("*", history_listener)

        # Start game loop in background with error handling
        async def run_game_with_error_handling() -> None:
            """Run game with error handling to prevent silent failures."""
            try:
                logger.info(f"Starting game loop for game {game_id}")
                await game_runner.run_game()
                logger.info(f"Game {game_id} completed successfully")
            except Exception as e:
                logger.error(f"Game {game_id} failed with error: {e}", exc_info=True)
                # Keep game in storage for post-mortem analysis
                # Game state will show as failed in logs

        asyncio.create_task(run_game_with_error_handling())

        # Return response
        return StartGameResponse(
            game_id=game_id,
            players=player_summaries,
            status="in_progress",
            seed=request.seed or game_runner.seed,
            created_at=game_storage.get_created_at(game_id),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=f"Failed to start game: {str(e)}",
                code="GAME_CREATION_FAILED",
                details={"error": str(e)},
            ).model_dump(),
        )


@router.get("/game/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: str) -> Any:
    """
    Get the complete current game state.

    Returns all game information including players, board state, and current turn.
    """
    logger.debug(f"State request for game {game_id}")
    logger.debug(f"Active games in storage: {game_storage.list_games()}")

    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        logger.warning(f"Game {game_id} not found in storage. Active games: {game_storage.list_games()}")
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Game {game_id} not found",
                code="GAME_NOT_FOUND",
                details={"game_id": game_id},
            ).model_dump(),
        )

    # Get state from game runner
    state = game_runner.get_state()

    # Convert players to include additional agent metadata
    players = []
    for p in state["players"]:
        # Get personality for this player
        personality = get_personality(p["id"])
        players.append({
            **p,
            "get_out_of_jail_cards": p.get("jail_cards", 0),
            "consecutive_doubles": 0,  # Not tracked in current state
            "color": personality.color,
            "avatar": personality.avatar,
            "personality": personality.archetype.split()[0].lower(),
            "model": personality.model,
        })

    # Serialize board (simplified for now - full implementation needed)
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
            "color_group": None,
            "price": None,
            "rent_schedule": None,
            "house_cost": None,
            "mortgage_value": None,
            "tax_amount": None,
        }

        # Add property-specific data
        if space.property_data:
            space_dict.update({
                "color_group": space.property_data.color_group.name,
                "price": space.property_data.price,
                "rent_schedule": list(space.property_data.rent),
                "house_cost": space.property_data.house_cost,
                "mortgage_value": space.property_data.mortgage_value,
            })
        elif space.railroad_data:
            space_dict.update({
                "price": space.railroad_data.price,
                "mortgage_value": space.railroad_data.mortgage_value,
            })
        elif space.utility_data:
            space_dict.update({
                "price": space.utility_data.price,
                "mortgage_value": space.utility_data.mortgage_value,
            })
        elif space.tax_data:
            space_dict["tax_amount"] = space.tax_data.amount

        # Add houses and mortgage status
        for p in state["players"]:
            if i in p["mortgaged"]:
                space_dict["is_mortgaged"] = True
            if i in p["houses"]:
                space_dict["houses"] = p["houses"][i]

        board.append(space_dict)

    # Convert last_roll to API format (rename is_doubles to doubles)
    last_roll = state["last_roll"]
    if last_roll and "is_doubles" in last_roll:
        last_roll = {
            "die1": last_roll["die1"],
            "die2": last_roll["die2"],
            "total": last_roll["total"],
            "doubles": last_roll["is_doubles"],
        }

    # Convert to API response format
    return {
        "game_id": game_id,
        "status": "in_progress" if game_runner._running else ("paused" if game_runner._paused else "finished"),
        "turn_number": state["turn_number"],
        "current_player_id": state["current_player"],
        "turn_phase": state["turn_phase"],
        "speed": game_runner.speed,
        "players": players,
        "board": board,
        "bank": {
            "houses_available": game_runner.game.bank.houses_available,
            "hotels_available": game_runner.game.bank.hotels_available,
        },
        "last_roll": last_roll,
        "created_at": game_storage.get_created_at(game_id),
    }


@router.get("/game/{game_id}/history", response_model=GameHistoryResponse)
async def get_game_history(
    game_id: str,
    since: int = Query(0, ge=0, description="Return events with sequence >= since"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of events"),
    event_type: str | None = Query(None, description="Filter by event type (comma-separated)"),
) -> GameHistoryResponse:
    """
    Get the event history for a game.

    Supports filtering by sequence number, event type, and limit.
    """
    event_history = game_storage.get_event_history(game_id)
    if not event_history:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Game {game_id} not found",
                code="GAME_NOT_FOUND",
                details={"game_id": game_id},
            ).model_dump(),
        )

    # Parse event types filter
    event_types = None
    if event_type:
        event_types = [t.strip() for t in event_type.split(",")]

    # Get events from event history
    events = event_history.get_events(since=since, limit=limit, event_types=event_types)

    return GameHistoryResponse(
        game_id=game_id,
        events=[
            {
                "event": e.event,
                "data": e.data,
                "timestamp": e.timestamp,
                "turn_number": e.turn_number,
                "sequence": e.sequence,
            }
            for e in events
        ],
        total_events=event_history.get_event_count(),
        has_more=event_history.get_event_count() > (since + len(events)),
    )


@router.post("/game/{game_id}/pause", response_model=GameControlResponse)
async def pause_game(game_id: str) -> GameControlResponse:
    """
    Pause a running game.

    The game loop stops after the current turn completes.
    """
    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Game {game_id} not found",
                code="GAME_NOT_FOUND",
                details={"game_id": game_id},
            ).model_dump(),
        )

    if not game_runner._running or game_runner._paused:
        raise HTTPException(
            status_code=409,
            detail=ErrorResponse(
                error="Game is not currently running",
                code="GAME_NOT_RUNNING",
                details={"status": "paused" if game_runner._paused else "finished"},
            ).model_dump(),
        )

    game_runner.pause()

    return GameControlResponse(
        game_id=game_id,
        status="paused",
        turn_number=game_runner.game.turn_number,
    )


@router.post("/game/{game_id}/resume", response_model=GameControlResponse)
async def resume_game(game_id: str) -> GameControlResponse:
    """
    Resume a paused game.
    """
    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Game {game_id} not found",
                code="GAME_NOT_FOUND",
                details={"game_id": game_id},
            ).model_dump(),
        )

    if not game_runner._paused:
        raise HTTPException(
            status_code=409,
            detail=ErrorResponse(
                error="Game is not currently paused",
                code="GAME_NOT_PAUSED",
                details={"status": "running" if game_runner._running else "finished"},
            ).model_dump(),
        )

    game_runner.resume()

    return GameControlResponse(
        game_id=game_id,
        status="in_progress",
        turn_number=game_runner.game.turn_number,
    )


@router.post("/game/{game_id}/speed", response_model=SetSpeedResponse)
async def set_game_speed(game_id: str, request: SetSpeedRequest) -> SetSpeedResponse:
    """
    Change the game speed (delay between turns).
    """
    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Game {game_id} not found",
                code="GAME_NOT_FOUND",
                details={"game_id": game_id},
            ).model_dump(),
        )

    if not 0.25 <= request.speed <= 5.0:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Speed must be between 0.25 and 5.0, got {request.speed}",
                code="INVALID_SPEED",
                details={"speed": request.speed},
            ).model_dump(),
        )

    game_runner.set_speed(request.speed)

    return SetSpeedResponse(
        game_id=game_id,
        speed=request.speed,
    )


@router.get("/game/{game_id}/agents", response_model=AgentsResponse)
async def get_agents(game_id: str) -> AgentsResponse:
    """
    Get detailed information about all AI agents in the game.

    Includes personality descriptions, behavioral parameters, and configuration.
    """
    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Game {game_id} not found",
                code="GAME_NOT_FOUND",
                details={"game_id": game_id},
            ).model_dump(),
        )

    # Get agent info from personalities
    agents_info = []
    for i in range(4):
        personality = get_personality(i)

        # Map personality to description
        descriptions = {
            0: "An aggressive negotiator who buys everything in sight, trades ruthlessly, and intimidates opponents into bad deals. Favors monopoly acquisition at any cost.",
            1: "An analytical strategist who calculates expected values for every decision, builds methodically, and only accepts trades with clear mathematical advantage.",
            2: "A charismatic bluffer who makes lopsided trade offers sound amazing, takes unpredictable risks, and uses charm to manipulate other agents.",
            3: "A conservative builder who hoards cash, avoids risky trades, and only develops properties when holding complete monopolies with ample reserves.",
        }

        # Map to style parameters
        risk_map = {0: "high", 1: "medium", 2: "high", 3: "low"}
        trading_map = {0: "very_high", 1: "medium", 2: "very_high", 3: "low"}
        building_map = {0: "opportunistic", 1: "methodical", 2: "unpredictable", 3: "patient"}
        speech_patterns = {
            0: "Threatening, confident, uses ultimatums",
            1: "Precise, data-driven, quotes probabilities",
            2: "Persuasive, flattering, changes the subject",
            3: "Cautious, brief, politely declines most offers",
        }

        agents_info.append(
            AgentInfo(
                id=i,
                name=personality.name,
                model=personality.model,
                personality=personality.archetype.split()[0].lower(),
                avatar=personality.avatar,
                color=personality.color,
                description=descriptions[i],
                style={
                    "risk_tolerance": risk_map[i],
                    "trading_aggression": trading_map[i],
                    "building_strategy": building_map[i],
                    "speech_pattern": speech_patterns[i],
                },
            )
        )

    return AgentsResponse(
        game_id=game_id,
        agents=agents_info,
    )
