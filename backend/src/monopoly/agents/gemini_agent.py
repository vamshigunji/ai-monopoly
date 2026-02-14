"""Google Gemini agent adapter using structured output."""

from __future__ import annotations

import json
import logging
from typing import Optional

from google import genai
from google.genai import types as genai_types

from monopoly.engine.types import (
    EventType,
    GameEvent,
    JailAction,
    PropertyData,
    RailroadData,
    TradeProposal,
    UtilityData,
)
from monopoly.agents.base import (
    AgentInterface,
    BankruptcyAction,
    BuildOrder,
    GameView,
    PostRollAction,
    PreRollAction,
)
from monopoly.agents.context import ChatMessage, ContextManager, PrivateThought
from monopoly.agents.personalities import PersonalityConfig

logger = logging.getLogger(__name__)


class GeminiAgent(AgentInterface):
    """Agent backed by Google Gemini models (Gemini 1.5 Pro, Flash).

    Uses structured output with response schemas and tracks token usage.
    """

    def __init__(
        self,
        player_id: int,
        personality: PersonalityConfig,
        api_key: str,
        context_manager: Optional[ContextManager] = None,
        event_bus=None,
    ):
        self.player_id = player_id
        self.personality = personality
        self.client = genai.Client(api_key=api_key)
        self.model_name = personality.model
        self.context = context_manager or ContextManager(
            player_id, self._summarize_public_messages
        )
        self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        self.event_bus = event_bus

    async def _emit_thought(self, thought: str, turn_number: int) -> None:
        """Emit a private thought event to the event bus."""
        if self.event_bus:
            event = GameEvent(
                event_type=EventType.AGENT_THOUGHT,
                player_id=self.player_id,
                data={
                    "thought": thought,
                    "prompt_tokens": self.token_usage["prompt_tokens"],
                    "completion_tokens": self.token_usage["completion_tokens"],
                },
                turn_number=turn_number,
            )
            await self.event_bus.emit(event)

    async def _emit_speech(self, message: str, turn_number: int) -> None:
        """Emit a public speech event to the event bus."""
        if self.event_bus:
            event = GameEvent(
                event_type=EventType.AGENT_SPOKE,
                player_id=self.player_id,
                data={"message": message},
                turn_number=turn_number,
            )
            await self.event_bus.emit(event)

    async def _summarize_public_messages(self, messages: list[ChatMessage]) -> str:
        """Summarize old public messages using a cheap model call."""
        if not messages:
            return ""

        # Build a summary prompt
        msg_text = "\n".join(
            [f"Turn {m.turn_number}, {m.player_name}: {m.message}" for m in messages]
        )
        prompt = f"Summarize this Monopoly table talk in 2-3 sentences:\n{msg_text}"

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    maxOutputTokens=150,
                ),
            )
            return response.text or ""
        except Exception as e:
            logger.warning(f"Failed to summarize messages: {e}")
            return f"(Turns {messages[0].turn_number}-{messages[-1].turn_number}: multiple negotiations and reactions)"

    async def _call_llm(self, prompt: str, response_schema: dict) -> dict:
        """Make a single LLM call with structured output and retry logic."""
        for attempt in (1, 2):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        responseMimeType="application/json",
                        responseJsonSchema=response_schema,
                        temperature=self.personality.temperature,
                        maxOutputTokens=500,
                    ),
                )

                # Track token usage
                if response.usage_metadata:
                    self.token_usage["prompt_tokens"] += (
                        response.usage_metadata.prompt_token_count or 0
                    )
                    self.token_usage["completion_tokens"] += (
                        response.usage_metadata.candidates_token_count or 0
                    )

                text = response.text
                if not text:
                    raise ValueError("Empty response from Gemini API")
                return json.loads(text)

            except Exception as e:
                logger.warning(
                    f"Agent {self.player_id} LLM call failed (attempt {attempt}): {e}"
                )
                if attempt == 2:
                    raise

        raise RuntimeError("LLM call failed after 2 attempts")

    async def _build_base_prompt(self, game_view: GameView, decision_context: str) -> str:
        """Build the base system prompt with personality, rules, and state."""
        public_context = await self.context.get_public_context(game_view.turn_number)
        private_context = self.context.get_private_context()

        return f"""{self.personality.system_prompt}

MONOPOLY RULES SUMMARY:
- Board: 40 spaces. Pass GO = collect $200.
- Properties: Buy for listed price or auction. Monopoly = own all in color group.
- Rent: Doubles with monopoly. Houses: must build evenly across color group.
- Houses cost $50-$200 depending on color group. Hotels replace 4 houses.
- Railroads: $25/$50/$100/$200 based on count owned.
- Utilities: 4x or 10x dice roll based on count owned.
- Jail: Pay $50, use card, or try doubles (3 attempts, then forced to pay).
- Mortgage: Receive mortgage value. Unmortgage = mortgage + 10%.
- Bankruptcy: Sell buildings at half price, mortgage properties. If still short, you're out.
- Trading: Properties, cash, jail cards. No buildings on traded properties.
- Housing shortage: Only 32 houses and 12 hotels exist. First come, first served.

CURRENT GAME STATE:
Turn: {game_view.turn_number}
Your cash: ${game_view.my_cash}
Your position: {game_view.my_position}
Your properties: {game_view.my_properties}
Your houses: {game_view.my_houses}
Your jail cards: {game_view.my_jail_cards}
In jail: {game_view.my_in_jail}

Opponents:
{self._format_opponents(game_view.opponents)}

Bank houses: {game_view.bank_houses_remaining}/32
Bank hotels: {game_view.bank_hotels_remaining}/12

{public_context}

{private_context}

{decision_context}"""

    def _format_opponents(self, opponents: list) -> str:
        """Format opponent list for prompt."""
        lines = []
        for opp in opponents:
            lines.append(
                f"- Player {opp.player_id} ({opp.name}): ${opp.cash}, "
                f"position {opp.position}, {len(opp.properties)} properties"
            )
        return "\n".join(lines)

    async def decide_pre_roll(self, game_view: GameView) -> PreRollAction:
        """Decide what to do before rolling."""
        decision_context = f"""
DECISION: Pre-roll phase. You may build houses/hotels, mortgage/unmortgage
properties, or do nothing.

Your cash: ${game_view.my_cash}
Your properties: {game_view.my_properties}
Your houses: {game_view.my_houses}
Bank houses: {game_view.bank_houses_remaining}/32
Bank hotels: {game_view.bank_hotels_remaining}/12

Respond with JSON containing:
- "builds": list of {{"position": int, "type": "house"|"hotel"}}
- "mortgages": list of positions to mortgage
- "unmortgages": list of positions to unmortgage
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "builds": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "position": {"type": "integer"},
                            "type": {"type": "string"},
                        },
                        "required": ["position", "type"],
                    },
                },
                "mortgages": {"type": "array", "items": {"type": "integer"}},
                "unmortgages": {"type": "array", "items": {"type": "integer"}},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": [
                "builds",
                "mortgages",
                "unmortgages",
                "public_speech",
                "private_thought",
            ],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            # Record speech and thought
            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="general",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="strategy",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            builds = [
                BuildOrder(
                    position=b["position"],
                    build_hotel=(b.get("type") == "hotel"),
                )
                for b in result.get("builds", [])
            ]

            return PreRollAction(
                builds=builds,
                mortgages=result.get("mortgages", []),
                unmortgages=result.get("unmortgages", []),
            )

        except Exception as e:
            logger.error(f"Agent {self.player_id} pre_roll failed: {e}")
            return PreRollAction()

    async def decide_buy_or_auction(
        self,
        game_view: GameView,
        property: PropertyData | RailroadData | UtilityData,
    ) -> bool:
        """Decide whether to buy a property."""
        prop_name = property.name
        price = property.price

        decision_context = f"""
DECISION: You landed on {prop_name}, an unowned property.
Price: ${price}. Your cash: ${game_view.my_cash}.

Should you buy this property at full price, or let it go to auction?

Respond with JSON containing:
- "buy": true to buy, false to auction
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "buy": {"type": "boolean"},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": ["buy", "public_speech", "private_thought"],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            # Record speech and thought
            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="reaction",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="valuation",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            return bool(result["buy"])

        except Exception as e:
            logger.error(f"Agent {self.player_id} buy_decision failed: {e}")
            # Fallback: buy if we can afford it with 2x margin
            return game_view.my_cash >= price * 2

    async def decide_auction_bid(
        self,
        game_view: GameView,
        property: PropertyData | RailroadData | UtilityData,
        current_bid: int,
    ) -> int:
        """Decide how much to bid in an auction."""
        prop_name = property.name
        price = property.price

        decision_context = f"""
DECISION: {prop_name} is being auctioned.
Current highest bid: ${current_bid}. Listed price: ${price}.
Your cash: ${game_view.my_cash}.

How much do you bid? Bid 0 to withdraw.

Respond with JSON containing:
- "bid": bid amount (integer, 0 to pass)
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "bid": {"type": "integer"},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": ["bid", "public_speech", "private_thought"],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            # Record speech and thought
            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="reaction",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="valuation",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            bid = int(result["bid"])
            # Validate bid is affordable
            if bid > game_view.my_cash:
                return 0
            return bid

        except Exception as e:
            logger.error(f"Agent {self.player_id} auction_bid failed: {e}")
            # Fallback: bid up to personality's max multiplier
            max_bid = int(price * self.personality.auction_max_multiplier)
            if current_bid < max_bid and game_view.my_cash >= current_bid + 10:
                return current_bid + 10
            return 0

    async def decide_trade(self, game_view: GameView) -> Optional[TradeProposal]:
        """Optionally propose a trade to another player."""
        decision_context = f"""
DECISION: You may propose a trade with any opponent, or skip.

Your tradeable properties (no buildings): {game_view.my_properties}
Your cash: ${game_view.my_cash}
Your Get Out of Jail Free cards: {game_view.my_jail_cards}

Opponents:
{self._format_opponents(game_view.opponents)}

Respond with JSON containing:
- "propose_trade": true to propose, false to skip
- If proposing: "target_player" (int), "offer_properties" (list of positions),
  "request_properties" (list of positions), "offer_cash" (int),
  "request_cash" (int), "offer_jail_cards" (int), "request_jail_cards" (int)
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "propose_trade": {"type": "boolean"},
                "target_player": {"type": "integer"},
                "offer_properties": {"type": "array", "items": {"type": "integer"}},
                "request_properties": {"type": "array", "items": {"type": "integer"}},
                "offer_cash": {"type": "integer"},
                "request_cash": {"type": "integer"},
                "offer_jail_cards": {"type": "integer"},
                "request_jail_cards": {"type": "integer"},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": ["propose_trade", "public_speech", "private_thought"],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="negotiation",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="trade_evaluation",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            if not result.get("propose_trade", False):
                return None

            return TradeProposal(
                proposer_id=self.player_id,
                receiver_id=result.get("target_player", 0),
                offered_properties=result.get("offer_properties", []),
                requested_properties=result.get("request_properties", []),
                offered_cash=result.get("offer_cash", 0),
                requested_cash=result.get("request_cash", 0),
                offered_jail_cards=result.get("offer_jail_cards", 0),
                requested_jail_cards=result.get("request_jail_cards", 0),
            )

        except Exception as e:
            logger.error(f"Agent {self.player_id} trade_decision failed: {e}")
            return None

    async def respond_to_trade(
        self, game_view: GameView, proposal: TradeProposal
    ) -> bool:
        """Accept or reject an incoming trade proposal."""
        decision_context = f"""
DECISION: Player {proposal.proposer_id} is offering you a trade.

They offer:
- Properties: {proposal.offered_properties}
- Cash: ${proposal.offered_cash}
- Jail cards: {proposal.offered_jail_cards}

They request:
- Properties: {proposal.requested_properties}
- Cash: ${proposal.requested_cash}
- Jail cards: {proposal.requested_jail_cards}

Your cash: ${game_view.my_cash}

Do you accept or reject this trade?

Respond with JSON containing:
- "accept": true to accept, false to reject
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "accept": {"type": "boolean"},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": ["accept", "public_speech", "private_thought"],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="negotiation",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="trade_evaluation",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            return bool(result["accept"])

        except Exception as e:
            logger.error(f"Agent {self.player_id} trade_response failed: {e}")
            return False

    async def decide_jail_action(self, game_view: GameView) -> JailAction:
        """Decide how to get out of jail."""
        decision_context = f"""
DECISION: You are in jail (turn {game_view.my_jail_turns} of 3).

Options:
1. pay_fine - Pay $50 to leave immediately
2. use_card - Use a Get Out of Jail Free card (you have {game_view.my_jail_cards})
3. roll_doubles - Try to roll doubles

Respond with JSON containing:
- "action": one of "pay_fine", "use_card", "roll_doubles"
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["pay_fine", "use_card", "roll_doubles"]},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": ["action", "public_speech", "private_thought"],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            # Record speech and thought
            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="general",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="strategy",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            action_str = result["action"]
            if action_str == "pay_fine":
                return JailAction.PAY_FINE
            elif action_str == "use_card":
                return JailAction.USE_CARD
            else:
                return JailAction.ROLL_DOUBLES

        except Exception as e:
            logger.error(f"Agent {self.player_id} jail_action failed: {e}")
            # Fallback: use card if available, otherwise roll
            if game_view.my_jail_cards > 0:
                return JailAction.USE_CARD
            return JailAction.ROLL_DOUBLES

    async def decide_post_roll(self, game_view: GameView) -> PostRollAction:
        """Decide what to do after rolling — build, mortgage, or do nothing."""
        decision_context = f"""
DECISION: Post-roll phase. You may build houses/hotels, mortgage/unmortgage
properties, or do nothing.

Your cash: ${game_view.my_cash}
Your properties: {game_view.my_properties}
Your houses: {game_view.my_houses}
Bank houses: {game_view.bank_houses_remaining}/32
Bank hotels: {game_view.bank_hotels_remaining}/12

Respond with JSON containing:
- "builds": list of {{"position": int, "type": "house"|"hotel"}}
- "mortgages": list of positions to mortgage
- "unmortgages": list of positions to unmortgage
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "builds": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "position": {"type": "integer"},
                            "type": {"type": "string"},
                        },
                        "required": ["position", "type"],
                    },
                },
                "mortgages": {"type": "array", "items": {"type": "integer"}},
                "unmortgages": {"type": "array", "items": {"type": "integer"}},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": [
                "builds",
                "mortgages",
                "unmortgages",
                "public_speech",
                "private_thought",
            ],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="general",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="strategy",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            builds = [
                BuildOrder(
                    position=b["position"],
                    build_hotel=(b.get("type") == "hotel"),
                )
                for b in result.get("builds", [])
            ]

            return PostRollAction(
                builds=builds,
                mortgages=result.get("mortgages", []),
                unmortgages=result.get("unmortgages", []),
            )

        except Exception as e:
            logger.error(f"Agent {self.player_id} post_roll failed: {e}")
            return PostRollAction()

    async def decide_bankruptcy_resolution(
        self, game_view: GameView, amount_owed: int
    ) -> BankruptcyAction:
        """Decide how to resolve insufficient funds."""
        decision_context = f"""
DECISION: You owe ${amount_owed} but only have ${game_view.my_cash}.
You must sell houses/hotels or mortgage properties to raise funds.
If you cannot raise enough, you must declare bankruptcy.

Your properties: {game_view.my_properties}
Your houses: {game_view.my_houses}

Respond with JSON containing:
- "sell_houses": list of positions to sell houses from
- "sell_hotels": list of positions to sell hotels from
- "mortgage": list of positions to mortgage
- "declare_bankruptcy": true to give up, false to try to pay
- "public_speech": what you say
- "private_thought": your reasoning
"""

        response_schema = {
            "type": "object",
            "properties": {
                "sell_houses": {"type": "array", "items": {"type": "integer"}},
                "sell_hotels": {"type": "array", "items": {"type": "integer"}},
                "mortgage": {"type": "array", "items": {"type": "integer"}},
                "declare_bankruptcy": {"type": "boolean"},
                "public_speech": {"type": "string"},
                "private_thought": {"type": "string"},
            },
            "required": [
                "sell_houses",
                "sell_hotels",
                "mortgage",
                "declare_bankruptcy",
                "public_speech",
                "private_thought",
            ],
        }

        prompt = await self._build_base_prompt(game_view, decision_context)

        try:
            result = await self._call_llm(prompt, response_schema)

            self.context.add_public_message(
                ChatMessage(
                    player_id=self.player_id,
                    player_name=self.personality.name,
                    message=result["public_speech"],
                    turn_number=game_view.turn_number,
                    context="reaction",
                )
            )
            self.context.add_private_thought(
                PrivateThought(
                    thought=result["private_thought"],
                    turn_number=game_view.turn_number,
                    category="risk_assessment",
                )
            )

            # Emit events to event bus
            await self._emit_thought(result["private_thought"], game_view.turn_number)
            if result.get("public_speech"):
                await self._emit_speech(result["public_speech"], game_view.turn_number)

            return BankruptcyAction(
                sell_houses=result.get("sell_houses", []),
                sell_hotels=result.get("sell_hotels", []),
                mortgage=result.get("mortgage", []),
                declare_bankruptcy=result.get("declare_bankruptcy", True),
            )

        except Exception as e:
            logger.error(f"Agent {self.player_id} bankruptcy_decision failed: {e}")
            return BankruptcyAction(declare_bankruptcy=True)
