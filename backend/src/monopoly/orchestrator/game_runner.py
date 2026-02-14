"""GameRunner orchestrates the full Monopoly game loop.

Integrates the game engine, AI agents, turn manager, and event bus to run a
complete game from start to finish.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from monopoly.agents.base import (
    AgentInterface,
    GameView,
    OpponentView,
    PreRollAction,
    PostRollAction,
    BuildOrder,
)
from monopoly.agents.random_agent import RandomAgent
from monopoly.engine.game import Game
from monopoly.engine.types import (
    EventType,
    GameEvent,
    GamePhase,
    JailAction,
    PropertyData,
    RailroadData,
    TradeProposal,
    TurnPhase,
    UtilityData,
)
from monopoly.engine.board import PROPERTIES, RAILROADS, UTILITIES


logger = logging.getLogger(__name__)


@dataclass
class GameStats:
    """Statistics about the game run."""

    turns_completed: int = 0
    trades_proposed: int = 0
    trades_accepted: int = 0
    properties_purchased: int = 0
    bankruptcies: int = 0
    agent_errors: dict[int, int] = field(default_factory=dict)
    fallback_uses: dict[int, int] = field(default_factory=dict)


class GameRunner:
    """Orchestrates the full game loop with AI agents.

    Responsibilities:
    - Initialize game with seed
    - Manage game loop until completion
    - Call agents at appropriate decision points
    - Handle agent errors with RandomAgent fallback
    - Build GameView from Game state for agents
    - Emit events to EventBus (if provided)
    - Support pause/resume and speed control
    """

    def __init__(
        self,
        agents: list[AgentInterface],
        seed: Optional[int] = None,
        speed: float = 1.0,
        event_bus=None,
    ):
        """Initialize game runner.

        Args:
            agents: List of 4 AI agents (must implement AgentInterface)
            seed: Random seed for deterministic gameplay (optional)
            speed: Speed multiplier for turn delays (1.0 = normal, 0.5 = slower)
            event_bus: EventBus instance for broadcasting events (optional)
        """
        if len(agents) != 4:
            raise ValueError(f"Expected 4 agents, got {len(agents)}")

        self.game = Game(num_players=4, seed=seed)
        self.agents = agents
        self.seed = seed
        self.speed = speed
        self.event_bus = event_bus

        # Fallback agents for error handling
        self._fallback_agents = [RandomAgent(i) for i in range(4)]

        # Game control
        self._paused = False
        self._running = False

        # Statistics
        self.stats = GameStats()

        logger.info(
            f"GameRunner initialized with seed={seed}, speed={speed}, "
            f"agents={[type(a).__name__ for a in agents]}"
        )

    # ── Game State Queries ──────────────────────────────────────────────

    def get_state(self) -> dict:
        """Get current game state snapshot.

        Returns:
            dict with game state including players, properties, turn info
        """
        return {
            "turn_number": self.game.turn_number,
            "current_player": self.game.current_player_index,
            "phase": self.game.phase.name,
            "turn_phase": self.game.turn_phase.name,
            "players": [
                {
                    "id": p.player_id,
                    "name": p.name,
                    "cash": p.cash,
                    "position": p.position,
                    "properties": list(p.properties),
                    "houses": dict(p.houses),
                    "mortgaged": list(p.mortgaged),
                    "jail_cards": p.get_out_of_jail_cards,
                    "in_jail": p.in_jail,
                    "jail_turns": p.jail_turns,
                    "is_bankrupt": p.is_bankrupt,
                    "net_worth": p.net_worth(self.game.board),
                }
                for p in self.game.players
            ],
            "property_ownership": dict(self.game._property_owners),
            "bank_houses": self.game.bank.houses_available,
            "bank_hotels": self.game.bank.hotels_available,
            "last_roll": (
                {
                    "die1": self.game.last_roll.die1,
                    "die2": self.game.last_roll.die2,
                    "total": self.game.last_roll.total,
                    "is_doubles": self.game.last_roll.is_doubles,
                }
                if self.game.last_roll
                else None
            ),
            "stats": {
                "turns_completed": self.stats.turns_completed,
                "trades_proposed": self.stats.trades_proposed,
                "trades_accepted": self.stats.trades_accepted,
                "properties_purchased": self.stats.properties_purchased,
                "bankruptcies": self.stats.bankruptcies,
            },
        }

    def get_history(self, since: int = 0) -> list[GameEvent]:
        """Get event history since a given index.

        Args:
            since: Starting index (0 = all events)

        Returns:
            List of GameEvent objects
        """
        return self.game.get_events_since(since)

    # ── Game Control ────────────────────────────────────────────────────

    def pause(self) -> None:
        """Pause the game loop."""
        self._paused = True
        logger.info("Game paused")
        self._emit_event(EventType.GAME_OVER, data={"reason": "paused"})

    def resume(self) -> None:
        """Resume the game loop."""
        self._paused = False
        logger.info("Game resumed")

    def stop(self) -> None:
        """Stop the game loop permanently. The current turn will finish, then the loop exits."""
        self._running = False
        self._paused = False
        logger.info("Game stopped")

    def set_speed(self, multiplier: float) -> None:
        """Set game speed multiplier.

        Args:
            multiplier: Speed multiplier (0.1 to 10.0)
        """
        if not 0.1 <= multiplier <= 10.0:
            raise ValueError(f"Speed multiplier must be between 0.1 and 10.0, got {multiplier}")
        self.speed = multiplier
        logger.info(f"Game speed set to {multiplier}x")

    # ── Main Game Loop ──────────────────────────────────────────────────

    async def run_game(self, max_turns: int = 1000) -> dict:
        """Run the complete game loop until completion or max turns.

        Args:
            max_turns: Maximum number of turns before forcing game end

        Returns:
            dict with final game state and winner info
        """
        self._running = True
        self._emit_event(EventType.GAME_STARTED, data={"seed": self.seed})

        logger.info(f"Starting game (max_turns={max_turns})")

        try:
            while not self.game.is_over() and self.game.turn_number < max_turns:
                if self._paused:
                    await asyncio.sleep(0.1)
                    continue

                await self._run_turn()

                # Turn delay based on speed
                delay = 0.5 / self.speed
                await asyncio.sleep(delay)

            # Game completed
            winner = self.game.get_winner()

            # If no winner by elimination, pick richest player (max turns reached)
            if not winner:
                active = self.game.get_active_players()
                if active:
                    winner = max(active, key=lambda p: p.net_worth(self.game.board))

            winner_info = (
                {
                    "player_id": winner.player_id,
                    "name": winner.name,
                    "net_worth": winner.net_worth(self.game.board),
                }
                if winner
                else None
            )

            logger.info(
                f"Game finished after {self.game.turn_number} turns. "
                f"Winner: {winner.name if winner else 'None'}"
            )

            self._emit_event(
                EventType.GAME_OVER,
                data={
                    "turns": self.game.turn_number,
                    "winner": winner_info,
                    "reason": "completed" if self.game.is_over() else "max_turns_reached",
                },
            )

            return {
                "completed": True,
                "turns": self.game.turn_number,
                "winner": winner_info,
                "stats": self.stats,
            }

        except Exception as e:
            logger.error(f"Game loop error: {e}", exc_info=True)
            self._emit_event(EventType.GAME_OVER, data={"reason": "error", "error": str(e)})
            raise
        finally:
            self._running = False

    async def _run_turn(self) -> None:
        """Execute a single player's turn."""
        player = self.game.current_player
        player_id = player.player_id

        if player.is_bankrupt:
            self.game.advance_turn()
            return

        self.stats.turns_completed += 1
        self._emit_event(EventType.TURN_STARTED, player_id=player_id, data={"turn_number": self.game.turn_number})

        logger.debug(f"Turn {self.game.turn_number}: Player {player_id} ({player.name})")

        try:
            # Handle jail if player is in jail
            if player.in_jail:
                await self._handle_jail_turn(player)
                if player.in_jail:  # Still in jail after attempting to leave
                    self.game.advance_turn()
                    return

            # PRE-ROLL phase
            self.game.turn_phase = TurnPhase.PRE_ROLL
            await self._handle_pre_roll_phase(player)

            # ROLL phase
            self.game.turn_phase = TurnPhase.ROLL
            dice_roll = self.game.roll_dice()
            self._emit_event(
                EventType.DICE_ROLLED,
                player_id=player_id,
                data={
                    "die1": dice_roll.die1,
                    "die2": dice_roll.die2,
                    "total": dice_roll.total,
                    "doubles": dice_roll.is_doubles,
                },
            )

            passed_go = self.game.move_player(player, dice_roll.total)
            if passed_go:
                self._emit_event(EventType.PASSED_GO, player_id=player_id, data={"salary": 200})

            # LANDED phase
            self.game.turn_phase = TurnPhase.LANDED
            await self._handle_landing(player)

            # POST-ROLL phase
            self.game.turn_phase = TurnPhase.POST_ROLL
            await self._handle_post_roll_phase(player)

        except Exception as e:
            logger.error(f"Error in turn for player {player_id}: {e}", exc_info=True)
            self.stats.agent_errors[player_id] = self.stats.agent_errors.get(player_id, 0) + 1

        # Advance to next player
        self.game.advance_turn()

    # ── Agent Timeout Helper ────────────────────────────────────────────

    AGENT_TIMEOUT = 30.0  # seconds

    async def _call_agent_with_timeout(self, coro, player_id: int):
        """Call an agent coroutine with timeout protection."""
        try:
            return await asyncio.wait_for(coro, timeout=self.AGENT_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Agent {player_id} timed out after {self.AGENT_TIMEOUT}s")
            raise

    def _record_fallback(self, player_id: int, decision: str) -> None:
        """Record a fallback use and emit a thought about it."""
        self.stats.fallback_uses[player_id] = self.stats.fallback_uses.get(player_id, 0) + 1
        self._emit_event(
            EventType.AGENT_THOUGHT,
            player_id=player_id,
            data={"thought": f"[FALLBACK] Agent failed on {decision}, using safe default."},
        )

    # ── Turn Phase Handlers ─────────────────────────────────────────────

    async def _handle_jail_turn(self, player) -> None:
        """Handle jail logic at start of turn."""
        game_view = self._build_game_view(player.player_id)
        agent = self.agents[player.player_id]

        try:
            jail_action = await self._call_agent_with_timeout(
                agent.decide_jail_action(game_view), player.player_id
            )
        except Exception as e:
            logger.warning(f"Agent {player.player_id} jail decision failed: {e}")
            jail_action = await self._fallback_agents[player.player_id].decide_jail_action(game_view)
            self._record_fallback(player.player_id, "jail_action")

        result_roll = self.game.handle_jail_turn(player, jail_action)

        if not player.in_jail:
            self._emit_event(
                EventType.PLAYER_FREED,
                player_id=player.player_id,
                data={"method": jail_action.name, "rolled_doubles": result_roll is not None if result_roll else False},
            )

    async def _handle_pre_roll_phase(self, player) -> None:
        """Handle PRE_ROLL phase actions."""
        game_view = self._build_game_view(player.player_id)
        agent = self.agents[player.player_id]

        try:
            action = await self._call_agent_with_timeout(
                agent.decide_pre_roll(game_view), player.player_id
            )
        except Exception as e:
            logger.warning(f"Agent {player.player_id} pre-roll decision failed: {e}")
            action = await self._fallback_agents[player.player_id].decide_pre_roll(game_view)
            self._record_fallback(player.player_id, "pre_roll")

        await self._execute_phase_action(player, action)

    async def _handle_post_roll_phase(self, player) -> None:
        """Handle POST_ROLL phase actions."""
        game_view = self._build_game_view(player.player_id)
        agent = self.agents[player.player_id]

        try:
            action = await self._call_agent_with_timeout(
                agent.decide_post_roll(game_view), player.player_id
            )
        except Exception as e:
            logger.warning(f"Agent {player.player_id} post-roll decision failed: {e}")
            action = await self._fallback_agents[player.player_id].decide_post_roll(game_view)
            self._record_fallback(player.player_id, "post_roll")

        await self._execute_phase_action(player, action)

    async def _execute_phase_action(self, player, action: PreRollAction | PostRollAction) -> None:
        """Execute bundled phase actions (trades, builds, mortgages)."""
        # Handle trades
        for trade_proposal in action.trades:
            await self._handle_trade_proposal(trade_proposal)

        # Handle building
        for build_order in action.builds:
            self._handle_build(player, build_order)

        # Handle mortgages
        for position in action.mortgages:
            if self.game.mortgage_property(player, position):
                self._emit_event(
                    EventType.PROPERTY_MORTGAGED,
                    player_id=player.player_id,
                    data={"position": position, "value": self._get_property_mortgage_value(position)},
                )

        # Handle unmortgages
        for position in action.unmortgages:
            if self.game.unmortgage_property(player, position):
                self._emit_event(
                    EventType.PROPERTY_UNMORTGAGED,
                    player_id=player.player_id,
                    data={"position": position, "cost": int(self._get_property_mortgage_value(position) * 1.1)},
                )

    async def _handle_landing(self, player) -> None:
        """Handle landing on a space."""
        landing_result = self.game.process_landing(player)

        # Emit landing event
        space = self.game.board.get_space(player.position)
        self._emit_event(
            EventType.PLAYER_MOVED,
            player_id=player.player_id,
            data={"position": player.position, "space_name": space.name},
        )

        # Handle buy decision if property is unowned
        if landing_result.requires_buy_decision:
            await self._handle_buy_decision(player, landing_result.position)

        # Handle rent payment
        if landing_result.rent_owed > 0:
            self._emit_event(
                EventType.RENT_PAID,
                player_id=player.player_id,
                data={"amount": landing_result.rent_owed, "to_player": landing_result.rent_to_player},
            )

        # Handle tax payment
        if landing_result.tax_amount > 0:
            self._emit_event(
                EventType.TAX_PAID,
                player_id=player.player_id,
                data={"amount": landing_result.tax_amount, "space": space.name},
            )

        # Handle Go To Jail
        if landing_result.sent_to_jail:
            self._emit_event(EventType.PLAYER_JAILED, player_id=player.player_id)

    async def _handle_buy_decision(self, player, position: int) -> None:
        """Handle agent decision to buy or auction property."""
        game_view = self._build_game_view(player.player_id)
        property_data = self._get_property_data(position)
        agent = self.agents[player.player_id]

        try:
            should_buy = await self._call_agent_with_timeout(
                agent.decide_buy_or_auction(game_view, property_data), player.player_id
            )
        except Exception as e:
            logger.warning(f"Agent {player.player_id} buy decision failed: {e}")
            should_buy = await self._fallback_agents[player.player_id].decide_buy_or_auction(game_view, property_data)
            self._record_fallback(player.player_id, "buy_decision")

        if should_buy:
            success = self.game.buy_property(player, position)
            if success:
                self.stats.properties_purchased += 1
                space = self.game.board.get_space(position)
                self._emit_event(
                    EventType.PROPERTY_PURCHASED,
                    player_id=player.player_id,
                    data={"position": position, "name": space.name, "price": property_data.price},
                )
        else:
            # Handle auction
            await self._handle_auction(position)

    async def _handle_auction(self, position: int) -> None:
        """Run an auction for a property."""
        self._emit_event(EventType.AUCTION_STARTED, data={"position": position})

        property_data = self._get_property_data(position)
        bids: dict[int, int] = {}

        # Get bids from all non-bankrupt players
        for player in self.game.get_active_players():
            game_view = self._build_game_view(player.player_id)
            agent = self.agents[player.player_id]
            current_bid = max(bids.values()) if bids else 0

            try:
                bid = await self._call_agent_with_timeout(
                    agent.decide_auction_bid(game_view, property_data, current_bid), player.player_id
                )
            except Exception as e:
                logger.warning(f"Agent {player.player_id} auction bid failed: {e}")
                bid = await self._fallback_agents[player.player_id].decide_auction_bid(
                    game_view, property_data, current_bid
                )
                self._record_fallback(player.player_id, "auction_bid")

            if bid > current_bid:
                bids[player.player_id] = bid
                self._emit_event(EventType.AUCTION_BID, player_id=player.player_id, data={"bid": bid})

        # Award to highest bidder
        if bids:
            winner_id = self.game.auction_property(position, bids)
            if winner_id is not None:
                space = self.game.board.get_space(position)
                self.stats.properties_purchased += 1
                self._emit_event(
                    EventType.AUCTION_WON,
                    player_id=winner_id,
                    data={"position": position, "name": space.name, "bid": bids[winner_id]},
                )

    async def _handle_trade_proposal(self, proposal: TradeProposal) -> None:
        """Handle a trade proposal between two players."""
        self.stats.trades_proposed += 1
        self._emit_event(
            EventType.TRADE_PROPOSED,
            player_id=proposal.proposer_id,
            data={
                "receiver_id": proposal.receiver_id,
                "offered_properties": proposal.offered_properties,
                "requested_properties": proposal.requested_properties,
                "offered_cash": proposal.offered_cash,
                "requested_cash": proposal.requested_cash,
            },
        )

        # Get receiver's response
        receiver = self.game.players[proposal.receiver_id]
        game_view = self._build_game_view(proposal.receiver_id)
        agent = self.agents[proposal.receiver_id]

        try:
            accepted = await self._call_agent_with_timeout(
                agent.respond_to_trade(game_view, proposal), proposal.receiver_id
            )
        except Exception as e:
            logger.warning(f"Agent {proposal.receiver_id} trade response failed: {e}")
            accepted = await self._fallback_agents[proposal.receiver_id].respond_to_trade(game_view, proposal)
            self._record_fallback(proposal.receiver_id, "trade_response")

        if accepted:
            success, error = self.game.execute_trade(proposal)
            if success:
                self.stats.trades_accepted += 1
                self._emit_event(
                    EventType.TRADE_ACCEPTED,
                    player_id=proposal.proposer_id,
                    data={
                        "receiver_id": proposal.receiver_id,
                        "offered_properties": proposal.offered_properties,
                        "requested_properties": proposal.requested_properties,
                        "offered_cash": proposal.offered_cash,
                        "requested_cash": proposal.requested_cash,
                    },
                )
            else:
                logger.warning(f"Trade validation failed: {error}")
                self._emit_event(EventType.TRADE_REJECTED, player_id=proposal.proposer_id, data={"reason": error})
        else:
            self._emit_event(EventType.TRADE_REJECTED, player_id=proposal.proposer_id)

    def _handle_build(self, player, build_order: BuildOrder) -> None:
        """Execute a build order."""
        if build_order.build_hotel:
            success = self.game.build_hotel(player, build_order.position)
            if success:
                space = self.game.board.get_space(build_order.position)
                self._emit_event(
                    EventType.HOTEL_BUILT,
                    player_id=player.player_id,
                    data={"position": build_order.position, "name": space.name},
                )
        else:
            success = self.game.build_house(player, build_order.position)
            if success:
                space = self.game.board.get_space(build_order.position)
                house_count = player.houses.get(build_order.position, 0)
                self._emit_event(
                    EventType.HOUSE_BUILT,
                    player_id=player.player_id,
                    data={"position": build_order.position, "name": space.name, "houses": house_count},
                )

    # ── GameView Construction ───────────────────────────────────────────

    def _build_game_view(self, player_id: int) -> GameView:
        """Build a GameView for a specific player.

        Filters game state to show only information the player should see.
        """
        player = self.game.players[player_id]

        # Build opponent views
        opponents = []
        for p in self.game.players:
            if p.player_id != player_id:
                opponents.append(
                    OpponentView(
                        player_id=p.player_id,
                        name=p.name,
                        cash=p.cash,
                        position=p.position,
                        property_count=len(p.properties),
                        properties=list(p.properties),
                        is_bankrupt=p.is_bankrupt,
                        in_jail=p.in_jail,
                        jail_cards=p.get_out_of_jail_cards,
                        net_worth=p.net_worth(self.game.board),
                    )
                )

        # Build property ownership map
        property_ownership = {pos: owner_id for pos, owner_id in self.game._property_owners.items()}

        # Build houses on board map
        houses_on_board = {}
        for p in self.game.players:
            for pos, count in p.houses.items():
                houses_on_board[pos] = count

        # Get recent events (last 20)
        recent_events = self.game.events[-20:] if len(self.game.events) > 20 else self.game.events

        return GameView(
            my_player_id=player_id,
            turn_number=self.game.turn_number,
            my_cash=player.cash,
            my_position=player.position,
            my_properties=list(player.properties),
            my_houses=dict(player.houses),
            my_mortgaged=set(player.mortgaged),
            my_jail_cards=player.get_out_of_jail_cards,
            my_in_jail=player.in_jail,
            my_jail_turns=player.jail_turns,
            opponents=opponents,
            property_ownership=property_ownership,
            houses_on_board=houses_on_board,
            bank_houses_remaining=self.game.bank.houses_available,
            bank_hotels_remaining=self.game.bank.hotels_available,
            last_dice_roll=self.game.last_roll,
            recent_events=recent_events,
        )

    # ── Helper Methods ──────────────────────────────────────────────────

    def _get_property_data(self, position: int) -> PropertyData | RailroadData | UtilityData:
        """Get property data for a position."""
        if position in PROPERTIES:
            return PROPERTIES[position]
        elif position in RAILROADS:
            return RAILROADS[position]
        elif position in UTILITIES:
            return UTILITIES[position]
        else:
            raise ValueError(f"Position {position} is not a purchasable property")

    def _get_property_mortgage_value(self, position: int) -> int:
        """Get mortgage value for a property."""
        prop_data = self._get_property_data(position)
        return prop_data.mortgage_value

    def _emit_event(self, event_type: EventType, player_id: int = -1, data: dict | None = None) -> None:
        """Emit an event to the event bus if available."""
        if self.event_bus is not None:
            event = GameEvent(
                event_type=event_type, player_id=player_id, data=data or {}, turn_number=self.game.turn_number
            )
            try:
                # EventBus emit is async, so we schedule it as a task
                if hasattr(self.event_bus, "emit"):
                    import asyncio
                    asyncio.create_task(self.event_bus.emit(event))
                elif hasattr(self.event_bus, "publish"):
                    import asyncio
                    asyncio.create_task(self.event_bus.publish(event))
            except Exception as e:
                logger.warning(f"Failed to emit event {event_type}: {e}")
