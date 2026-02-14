"""Base agent interface and shared types for AI agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from monopoly.engine.types import (
    DiceRoll,
    GameEvent,
    JailAction,
    PropertyData,
    RailroadData,
    TradeProposal,
    UtilityData,
)


@dataclass(frozen=True)
class OpponentView:
    """What one player can see about another player (public info only)."""

    player_id: int
    name: str
    cash: int  # cash is visible in Monopoly
    position: int
    property_count: int
    properties: list[int]  # positions (ownership is public)
    is_bankrupt: bool
    in_jail: bool
    jail_cards: int  # count is public knowledge
    net_worth: int


@dataclass(frozen=True)
class GameView:
    """Filtered view of the game state for a specific player.

    Contains full details about the viewing player's own state,
    and public-only information about other players.
    """

    # ── Identity ──
    my_player_id: int
    turn_number: int

    # ── Full own state (private) ──
    my_cash: int
    my_position: int
    my_properties: list[int]  # board positions owned
    my_houses: dict[int, int]  # position -> house count (5=hotel)
    my_mortgaged: set[int]  # positions of mortgaged properties
    my_jail_cards: int  # Get Out of Jail Free cards held
    my_in_jail: bool
    my_jail_turns: int

    # ── Other players (public info only) ──
    opponents: list[OpponentView]

    # ── Board state ──
    property_ownership: dict[int, int]  # position -> player_id (-1 = unowned)
    houses_on_board: dict[int, int]  # position -> house count (public)
    bank_houses_remaining: int  # 32 max
    bank_hotels_remaining: int  # 12 max

    # ── Recent game context ──
    last_dice_roll: Optional[DiceRoll]
    recent_events: list[GameEvent]  # last N events


@dataclass
class BuildOrder:
    """An order to build a house or hotel on a property."""

    position: int
    build_hotel: bool = False  # True = hotel, False = house


@dataclass
class PreRollAction:
    """Bundle of actions to take before rolling."""

    trades: list[TradeProposal] = field(default_factory=list)
    builds: list[BuildOrder] = field(default_factory=list)
    mortgages: list[int] = field(default_factory=list)  # positions to mortgage
    unmortgages: list[int] = field(default_factory=list)  # positions to unmortgage
    end_phase: bool = True  # signal done


@dataclass
class PostRollAction:
    """Bundle of actions to take after landing (same options as pre-roll)."""

    trades: list[TradeProposal] = field(default_factory=list)
    builds: list[BuildOrder] = field(default_factory=list)
    mortgages: list[int] = field(default_factory=list)
    unmortgages: list[int] = field(default_factory=list)
    end_phase: bool = True


@dataclass
class BankruptcyAction:
    """Actions to resolve insufficient funds."""

    sell_houses: list[int] = field(default_factory=list)  # positions
    sell_hotels: list[int] = field(default_factory=list)  # positions
    mortgage: list[int] = field(default_factory=list)  # positions
    declare_bankruptcy: bool = False


class AgentInterface(ABC):
    """Abstract interface that every AI agent must implement.

    Each method receives a GameView (filtered game state) and returns
    a typed decision. Every method is async because LLM calls are I/O-bound.
    """

    @abstractmethod
    async def decide_pre_roll(self, game_view: GameView) -> PreRollAction:
        """Decide what to do before rolling the dice.

        Options include:
        - Propose a trade to another player
        - Build houses/hotels on owned monopolies
        - Mortgage or unmortgage properties
        - Do nothing (end pre-roll phase)

        Called once per turn before the dice roll. The agent may
        request multiple actions bundled into a single PreRollAction.
        """

    @abstractmethod
    async def decide_buy_or_auction(
        self,
        game_view: GameView,
        property: PropertyData | RailroadData | UtilityData,
    ) -> bool:
        """Decide whether to buy the property just landed on.

        Returns True to buy at listed price, False to send to auction.
        Called only when the player lands on an unowned purchasable space.
        The engine verifies the player has sufficient cash before calling.
        """

    @abstractmethod
    async def decide_auction_bid(
        self,
        game_view: GameView,
        property: PropertyData | RailroadData | UtilityData,
        current_bid: int,
    ) -> int:
        """Decide how much to bid in a property auction.

        Returns the bid amount (must exceed current_bid), or 0 to pass.
        Called for each player in turn order during an auction. The engine
        validates that the bid does not exceed the player's cash.
        """

    @abstractmethod
    async def decide_trade(self, game_view: GameView) -> Optional[TradeProposal]:
        """Optionally propose a trade to another player.

        Returns a TradeProposal if the agent wants to trade, or None
        to skip. The proposal specifies:
        - target player
        - properties offered and requested (by board position)
        - cash offered and requested
        - Get Out of Jail Free cards offered and requested

        The engine validates ownership and legality before presenting
        the proposal to the target agent.
        """

    @abstractmethod
    async def respond_to_trade(
        self,
        game_view: GameView,
        proposal: TradeProposal,
    ) -> bool:
        """Accept or reject an incoming trade proposal.

        Returns True to accept, False to reject. The agent sees the
        full proposal details and current game state.
        """

    @abstractmethod
    async def decide_jail_action(self, game_view: GameView) -> JailAction:
        """Decide how to attempt to leave jail.

        Options:
        - JailAction.PAY_FINE: Pay $50 to leave immediately
        - JailAction.USE_CARD: Use a Get Out of Jail Free card
        - JailAction.ROLL_DOUBLES: Try to roll doubles (fail = stay)

        The engine checks card availability and cash before executing.
        After 3 failed roll attempts, the $50 fine is forced.
        """

    @abstractmethod
    async def decide_post_roll(self, game_view: GameView) -> PostRollAction:
        """Decide what to do after the dice roll and landing are resolved.

        Same options as pre-roll: trade, build, mortgage, or do nothing.
        This is the agent's second opportunity per turn to take
        strategic actions.
        """

    @abstractmethod
    async def decide_bankruptcy_resolution(
        self, game_view: GameView, amount_owed: int
    ) -> BankruptcyAction:
        """The player owes more than their cash. They must:
        - Sell houses/hotels
        - Mortgage properties
        - Declare bankruptcy (if unable to pay after selling/mortgaging)
        """
