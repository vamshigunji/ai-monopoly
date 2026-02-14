"""Turn Manager — coordinates the phases of a single player's turn."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from monopoly.engine.types import (
    EventType,
    JailAction,
    TurnPhase,
)

if TYPE_CHECKING:
    from monopoly.agents.base import AgentInterface, GameView
    from monopoly.engine.game import Game, LandingResult
    from monopoly.engine.player import Player

logger = logging.getLogger(__name__)


class TurnManager:
    """Manages the execution of a single player's turn through all phases.

    The turn manager coordinates:
    - Turn phase transitions (PRE_ROLL -> ROLL -> LANDED -> POST_ROLL -> END_TURN)
    - Jail handling (agent decides action)
    - Dice rolling and movement
    - Landing processing (buy/auction decisions)
    - Doubles detection (roll again or go to jail on 3rd)
    - Event emission at phase transitions
    """

    def __init__(self, game: Game) -> None:
        """Initialize the turn manager.

        Args:
            game: The game instance to manage turns for
        """
        self.game = game
        self.consecutive_doubles = 0
        self.rolled_this_turn = False

    async def execute_turn(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Execute a complete turn for a player.

        Args:
            player: The player taking their turn
            agent: The agent making decisions for this player
            game_view: The filtered game view for this player
        """
        logger.info(f"Starting turn for Player {player.player_id} ({player.name})")

        # Reset turn state
        self.rolled_this_turn = False

        # Handle jail if player is in jail
        if player.in_jail:
            await self._handle_jail_turn(player, agent, game_view)
            # If still in jail after handling, turn ends
            if player.in_jail:
                logger.info(f"Player {player.player_id} remains in jail, turn ends")
                self.game.turn_phase = TurnPhase.END_TURN
                return

        # PRE_ROLL phase
        await self._handle_pre_roll_phase(player, agent, game_view)

        # ROLL phase
        await self._handle_roll_phase(player, agent, game_view)

        # LANDED phase
        await self._handle_landed_phase(player, agent, game_view)

        # POST_ROLL phase
        await self._handle_post_roll_phase(player, agent, game_view)

        # END_TURN phase
        await self._handle_end_turn_phase(player, agent, game_view)

    async def _handle_jail_turn(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle a turn when the player is in jail.

        Args:
            player: The jailed player
            agent: The agent making decisions
            game_view: The filtered game view
        """
        logger.info(f"Player {player.player_id} is in jail (turn {player.jail_turns}/{3})")

        # Ask agent how to handle jail
        action = await agent.decide_jail_action(game_view)
        logger.info(f"Player {player.player_id} chose jail action: {action}")

        # Process the jail action
        roll = self.game.handle_jail_turn(player, action)

        # If player rolled doubles and got out, they can use that roll
        if roll is not None and roll.is_doubles:
            self.rolled_this_turn = True
            # Player is already freed by handle_jail_turn if they rolled doubles
            # They can continue their turn with this roll
            logger.info(f"Player {player.player_id} rolled doubles and escaped jail: {roll.total}")

    async def _handle_pre_roll_phase(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle the PRE_ROLL phase of a turn.

        In this phase, the player can:
        - Propose trades
        - Build houses/hotels
        - Mortgage/unmortgage properties

        Args:
            player: The current player
            agent: The agent making decisions
            game_view: The filtered game view
        """
        self.game.turn_phase = TurnPhase.PRE_ROLL
        logger.info(f"PRE_ROLL phase for Player {player.player_id}")

        # Get pre-roll action from agent
        action = await agent.decide_pre_roll(game_view)

        # Execute builds
        for build in action.builds:
            if build.build_hotel:
                success = self.game.build_hotel(player, build.position)
                if success:
                    logger.info(f"Player {player.player_id} built hotel at position {build.position}")
                else:
                    logger.warning(f"Player {player.player_id} failed to build hotel at position {build.position}")
            else:
                success = self.game.build_house(player, build.position)
                if success:
                    logger.info(f"Player {player.player_id} built house at position {build.position}")
                else:
                    logger.warning(f"Player {player.player_id} failed to build house at position {build.position}")

        # Execute mortgages
        for position in action.mortgages:
            success = self.game.mortgage_property(player, position)
            if success:
                logger.info(f"Player {player.player_id} mortgaged property at position {position}")
            else:
                logger.warning(f"Player {player.player_id} failed to mortgage property at position {position}")

        # Execute unmortgages
        for position in action.unmortgages:
            success = self.game.unmortgage_property(player, position)
            if success:
                logger.info(f"Player {player.player_id} unmortgaged property at position {position}")
            else:
                logger.warning(f"Player {player.player_id} failed to unmortgage property at position {position}")

        # Execute trades
        for trade in action.trades:
            success, reason = self.game.execute_trade(trade)
            if success:
                logger.info(f"Player {player.player_id} executed trade successfully")
            else:
                logger.warning(f"Player {player.player_id} trade failed: {reason}")

    async def _handle_roll_phase(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle the ROLL phase of a turn.

        Roll the dice and move the player.

        Args:
            player: The current player
            agent: The agent making decisions
            game_view: The filtered game view
        """
        self.game.turn_phase = TurnPhase.ROLL
        logger.info(f"ROLL phase for Player {player.player_id}")

        # If player already rolled (from jail), skip rolling
        if not self.rolled_this_turn:
            # Roll dice
            roll = self.game.roll_dice()
            logger.info(f"Player {player.player_id} rolled {roll.die1} and {roll.die2} = {roll.total} (doubles: {roll.is_doubles})")

            # Track consecutive doubles
            if roll.is_doubles:
                self.consecutive_doubles += 1
                logger.info(f"Player {player.player_id} rolled doubles (consecutive: {self.consecutive_doubles})")

                # Check for 3rd consecutive double -> jail
                if self.consecutive_doubles >= 3:
                    logger.info(f"Player {player.player_id} rolled 3 consecutive doubles, sending to jail")
                    self.game._send_to_jail(player)
                    self.game.turn_phase = TurnPhase.END_TURN
                    self.consecutive_doubles = 0
                    return
            else:
                self.consecutive_doubles = 0

            # Move player
            self.game.move_player(player, roll.total)
            logger.info(f"Player {player.player_id} moved to position {player.position}")
        else:
            # Player already rolled from jail, just move them
            if self.game.last_roll:
                self.game.move_player(player, self.game.last_roll.total)
                logger.info(f"Player {player.player_id} used jail roll, moved to position {player.position}")

    async def _handle_landed_phase(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle the LANDED phase of a turn.

        Process landing on a space and handle any required decisions:
        - Buy or auction unowned properties
        - Pay rent
        - Draw cards
        - Pay taxes

        Args:
            player: The current player
            agent: The agent making decisions
            game_view: The filtered game view
        """
        self.game.turn_phase = TurnPhase.LANDED
        logger.info(f"LANDED phase for Player {player.player_id} at position {player.position}")

        # Process landing
        landing_result = self.game.process_landing(player)

        # Handle buy decision if needed
        if landing_result.requires_buy_decision:
            space = self.game.board.get_space(player.position)
            logger.info(f"Player {player.player_id} landed on unowned property: {space.name}")

            # Get property data
            property_data = space.property_data or space.railroad_data or space.utility_data

            if property_data:
                # Ask agent whether to buy
                should_buy = await agent.decide_buy_or_auction(game_view, property_data)

                if should_buy:
                    # Try to buy
                    success = self.game.buy_property(player, player.position)
                    if success:
                        logger.info(f"Player {player.player_id} bought {space.name}")
                    else:
                        logger.warning(f"Player {player.player_id} failed to buy {space.name}")
                else:
                    # Go to auction
                    logger.info(f"Player {player.player_id} chose to auction {space.name}")
                    await self._handle_auction(player.position, agent, game_view)

        # Handle rent payment if needed
        if landing_result.rent_owed > 0:
            logger.info(f"Player {player.player_id} owes ${landing_result.rent_owed} rent to Player {landing_result.rent_to_player}")

            # Check if player can afford rent
            if player.cash >= landing_result.rent_owed:
                self.game.pay_rent(player, landing_result.rent_to_player, landing_result.rent_owed)
            else:
                # Player cannot afford rent - need bankruptcy resolution
                logger.warning(f"Player {player.player_id} cannot afford rent of ${landing_result.rent_owed}, cash: ${player.cash}")
                await self._handle_bankruptcy(player, agent, game_view, landing_result.rent_owed, landing_result.rent_to_player)

    async def _handle_post_roll_phase(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle the POST_ROLL phase of a turn.

        Same options as PRE_ROLL:
        - Propose trades
        - Build houses/hotels
        - Mortgage/unmortgage properties

        Args:
            player: The current player
            agent: The agent making decisions
            game_view: The filtered game view
        """
        self.game.turn_phase = TurnPhase.POST_ROLL
        logger.info(f"POST_ROLL phase for Player {player.player_id}")

        # Get post-roll action from agent
        action = await agent.decide_post_roll(game_view)

        # Execute builds
        for build in action.builds:
            if build.build_hotel:
                success = self.game.build_hotel(player, build.position)
                if success:
                    logger.info(f"Player {player.player_id} built hotel at position {build.position}")
                else:
                    logger.warning(f"Player {player.player_id} failed to build hotel at position {build.position}")
            else:
                success = self.game.build_house(player, build.position)
                if success:
                    logger.info(f"Player {player.player_id} built house at position {build.position}")
                else:
                    logger.warning(f"Player {player.player_id} failed to build house at position {build.position}")

        # Execute mortgages
        for position in action.mortgages:
            success = self.game.mortgage_property(player, position)
            if success:
                logger.info(f"Player {player.player_id} mortgaged property at position {position}")
            else:
                logger.warning(f"Player {player.player_id} failed to mortgage property at position {position}")

        # Execute unmortgages
        for position in action.unmortgages:
            success = self.game.unmortgage_property(player, position)
            if success:
                logger.info(f"Player {player.player_id} unmortgaged property at position {position}")
            else:
                logger.warning(f"Player {player.player_id} failed to unmortgage property at position {position}")

        # Execute trades
        for trade in action.trades:
            success, reason = self.game.execute_trade(trade)
            if success:
                logger.info(f"Player {player.player_id} executed trade successfully")
            else:
                logger.warning(f"Player {player.player_id} trade failed: {reason}")

    async def _handle_end_turn_phase(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle the END_TURN phase.

        Check for doubles and determine if player rolls again or turn advances.

        Args:
            player: The current player
            agent: The agent making decisions
            game_view: The filtered game view
        """
        self.game.turn_phase = TurnPhase.END_TURN
        logger.info(f"END_TURN phase for Player {player.player_id}")

        # Check if player rolled doubles and should roll again
        if self.game.last_roll and self.game.last_roll.is_doubles and self.consecutive_doubles < 3:
            logger.info(f"Player {player.player_id} rolled doubles, will roll again")
            # Reset for next roll
            self.rolled_this_turn = False
            # Execute another turn immediately (recursive call)
            await self.execute_turn(player, agent, game_view)
        else:
            # Turn is complete, reset consecutive doubles for next player
            self.consecutive_doubles = 0

    async def _handle_auction(
        self,
        position: int,
        agent: AgentInterface,
        game_view: GameView,
    ) -> None:
        """Handle an auction for a property.

        Note: This is a simplified auction implementation.
        A full implementation would need to get bids from all agents.

        Args:
            position: The position of the property being auctioned
            agent: The current agent
            game_view: The filtered game view
        """
        logger.info(f"Starting auction for property at position {position}")

        # Emit auction started event
        self.game._emit(EventType.AUCTION_STARTED, data={
            "position": position,
            "name": self.game.board.get_space(position).name,
        })

        # For now, simplified auction - just skip
        # A full implementation would need access to all agents to get bids
        # This would typically be handled by the GameRunner
        logger.warning("Auction handling requires all agents - skipping for now")

    async def _handle_bankruptcy(
        self,
        player: Player,
        agent: AgentInterface,
        game_view: GameView,
        amount_owed: int,
        creditor_id: int | None,
    ) -> None:
        """Handle a player who cannot afford a payment.

        The player must:
        - Sell houses/hotels
        - Mortgage properties
        - Declare bankruptcy if still unable to pay

        Args:
            player: The player in debt
            agent: The agent making decisions
            game_view: The filtered game view
            amount_owed: The amount the player owes
            creditor_id: The player ID owed to (or None if owed to bank)
        """
        logger.warning(f"Player {player.player_id} owes ${amount_owed} but only has ${player.cash}")

        # Ask agent how to resolve bankruptcy
        action = await agent.decide_bankruptcy_resolution(game_view, amount_owed)

        # Execute sell houses
        for position in action.sell_houses:
            success = self.game.sell_house(player, position)
            if success:
                logger.info(f"Player {player.player_id} sold house at position {position}")

        # Execute sell hotels
        for position in action.sell_hotels:
            success = self.game.sell_hotel(player, position)
            if success:
                logger.info(f"Player {player.player_id} sold hotel at position {position}")

        # Execute mortgages
        for position in action.mortgage:
            success = self.game.mortgage_property(player, position)
            if success:
                logger.info(f"Player {player.player_id} mortgaged property at position {position}")

        # Check if player can now afford the payment
        if player.cash >= amount_owed:
            logger.info(f"Player {player.player_id} raised enough cash to pay debt")
            if creditor_id is not None:
                self.game.pay_rent(player, creditor_id, amount_owed)
            else:
                player.remove_cash(amount_owed)
        else:
            # Player still cannot afford - must declare bankruptcy
            logger.info(f"Player {player.player_id} declares bankruptcy")
            self.game.declare_bankruptcy(player, creditor_id)
