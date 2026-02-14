"""Fallback random agent that makes valid but unstrategic moves.

Used when LLM calls fail after retries. Makes deterministic, rule-based
decisions without any AI or randomness.
"""

from __future__ import annotations

from typing import Optional

from monopoly.engine.types import (
    JailAction,
    PropertyData,
    RailroadData,
    TradeProposal,
    UtilityData,
)
from monopoly.agents.base import (
    AgentInterface,
    BankruptcyAction,
    GameView,
    PostRollAction,
    PreRollAction,
)


class RandomAgent(AgentInterface):
    """Fallback agent that makes random valid moves.

    No LLM calls. All decisions are deterministic rule-based logic.
    Used as a backup when primary agents fail.
    """

    def __init__(self, player_id: int):
        self.player_id = player_id

    async def decide_pre_roll(self, game_view: GameView) -> PreRollAction:
        """Do nothing before rolling."""
        return PreRollAction()

    async def decide_buy_or_auction(
        self,
        game_view: GameView,
        property: PropertyData | RailroadData | UtilityData,
    ) -> bool:
        """Buy if player has 2x the price in cash, else auction."""
        return game_view.my_cash >= property.price * 2

    async def decide_auction_bid(
        self,
        game_view: GameView,
        property: PropertyData | RailroadData | UtilityData,
        current_bid: int,
    ) -> int:
        """Bid listed price if affordable, else pass."""
        price = property.price
        if current_bid < price and game_view.my_cash >= price:
            return current_bid + 10
        return 0

    async def decide_trade(self, game_view: GameView) -> Optional[TradeProposal]:
        """Never propose trades."""
        return None

    async def respond_to_trade(
        self, game_view: GameView, proposal: TradeProposal
    ) -> bool:
        """Always reject trades."""
        return False

    async def decide_jail_action(self, game_view: GameView) -> JailAction:
        """Use card if available, pay fine if affordable, else roll doubles."""
        if game_view.my_jail_cards > 0:
            return JailAction.USE_CARD
        if game_view.my_cash >= 50:
            return JailAction.PAY_FINE
        return JailAction.ROLL_DOUBLES

    async def decide_post_roll(self, game_view: GameView) -> PostRollAction:
        """Do nothing after rolling."""
        return PostRollAction()

    async def decide_bankruptcy_resolution(
        self, game_view: GameView, amount_owed: int
    ) -> BankruptcyAction:
        """Immediately declare bankruptcy (no selling/mortgaging)."""
        return BankruptcyAction(declare_bankruptcy=True)
