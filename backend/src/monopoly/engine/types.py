"""Core type definitions for the Monopoly game engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SpaceType(Enum):
    """Types of spaces on the Monopoly board."""
    PROPERTY = auto()
    RAILROAD = auto()
    UTILITY = auto()
    TAX = auto()
    CHANCE = auto()
    COMMUNITY_CHEST = auto()
    GO = auto()
    JAIL = auto()
    FREE_PARKING = auto()
    GO_TO_JAIL = auto()


class ColorGroup(Enum):
    """Property color groups."""
    BROWN = "brown"
    LIGHT_BLUE = "light_blue"
    PINK = "pink"
    ORANGE = "orange"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    DARK_BLUE = "dark_blue"


class CardType(Enum):
    """Types of card decks."""
    CHANCE = auto()
    COMMUNITY_CHEST = auto()


class CardEffectType(Enum):
    """Types of card effects."""
    ADVANCE_TO = auto()          # Move to a specific space
    ADVANCE_TO_NEAREST = auto()  # Move to nearest railroad/utility
    GO_BACK = auto()             # Move backwards N spaces
    COLLECT = auto()             # Collect money from bank
    PAY = auto()                 # Pay money to bank
    PAY_EACH_PLAYER = auto()     # Pay each player N dollars
    COLLECT_FROM_EACH = auto()   # Collect N from each player
    REPAIRS = auto()             # Pay per house/hotel
    GO_TO_JAIL = auto()          # Go directly to jail
    GET_OUT_OF_JAIL = auto()     # Get out of jail free card


class JailAction(Enum):
    """Actions a player can take to get out of jail."""
    PAY_FINE = auto()       # Pay $50
    USE_CARD = auto()       # Use Get Out of Jail Free card
    ROLL_DOUBLES = auto()   # Try to roll doubles


class TurnPhase(Enum):
    """Phases within a player's turn."""
    PRE_ROLL = auto()
    ROLL = auto()
    LANDED = auto()
    POST_ROLL = auto()
    END_TURN = auto()


class GamePhase(Enum):
    """High-level game phases."""
    SETUP = auto()
    IN_PROGRESS = auto()
    FINISHED = auto()


@dataclass(frozen=True)
class PropertyData:
    """Static data for a property space."""
    name: str
    position: int
    color_group: ColorGroup
    price: int
    mortgage_value: int
    rent: tuple[int, ...]  # (base, 1_house, 2_houses, 3_houses, 4_houses, hotel)
    house_cost: int


@dataclass(frozen=True)
class RailroadData:
    """Static data for a railroad space."""
    name: str
    position: int
    price: int = 200
    mortgage_value: int = 100


@dataclass(frozen=True)
class UtilityData:
    """Static data for a utility space."""
    name: str
    position: int
    price: int = 150
    mortgage_value: int = 75


@dataclass(frozen=True)
class TaxData:
    """Static data for a tax space."""
    name: str
    position: int
    amount: int


@dataclass(frozen=True)
class Space:
    """A space on the Monopoly board."""
    position: int
    name: str
    space_type: SpaceType
    property_data: Optional[PropertyData] = None
    railroad_data: Optional[RailroadData] = None
    utility_data: Optional[UtilityData] = None
    tax_data: Optional[TaxData] = None


@dataclass(frozen=True)
class CardEffect:
    """Effect of a Chance or Community Chest card."""
    description: str
    effect_type: CardEffectType
    value: int = 0               # Dollar amount or number of spaces
    destination: int = -1        # Target position for ADVANCE_TO
    target_type: str = ""        # "railroad" or "utility" for ADVANCE_TO_NEAREST
    per_house: int = 0           # For REPAIRS
    per_hotel: int = 0           # For REPAIRS


@dataclass
class Card:
    """A Chance or Community Chest card."""
    deck: CardType
    effect: CardEffect


@dataclass(frozen=True)
class DiceRoll:
    """Result of rolling two dice."""
    die1: int
    die2: int

    @property
    def total(self) -> int:
        return self.die1 + self.die2

    @property
    def is_doubles(self) -> bool:
        return self.die1 == self.die2


@dataclass
class TradeProposal:
    """A trade proposal between two players."""
    proposer_id: int
    receiver_id: int
    offered_properties: list[int] = field(default_factory=list)   # positions
    requested_properties: list[int] = field(default_factory=list)  # positions
    offered_cash: int = 0
    requested_cash: int = 0
    offered_jail_cards: int = 0
    requested_jail_cards: int = 0


# Game event types for the event bus
class EventType(Enum):
    """Types of events emitted during gameplay."""
    GAME_STARTED = auto()
    TURN_STARTED = auto()
    DICE_ROLLED = auto()
    PLAYER_MOVED = auto()
    PASSED_GO = auto()
    PROPERTY_PURCHASED = auto()
    AUCTION_STARTED = auto()
    AUCTION_BID = auto()
    AUCTION_WON = auto()
    RENT_PAID = auto()
    CARD_DRAWN = auto()
    CARD_EFFECT = auto()
    TAX_PAID = auto()
    HOUSE_BUILT = auto()
    HOTEL_BUILT = auto()
    BUILDING_SOLD = auto()
    PROPERTY_MORTGAGED = auto()
    PROPERTY_UNMORTGAGED = auto()
    TRADE_PROPOSED = auto()
    TRADE_ACCEPTED = auto()
    TRADE_REJECTED = auto()
    PLAYER_JAILED = auto()
    PLAYER_FREED = auto()
    PLAYER_BANKRUPT = auto()
    AGENT_SPOKE = auto()
    AGENT_THOUGHT = auto()
    GAME_OVER = auto()


@dataclass
class GameEvent:
    """An event that occurred during the game."""
    event_type: EventType
    player_id: int = -1
    data: dict = field(default_factory=dict)
    turn_number: int = 0
