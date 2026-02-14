"""Chance and Community Chest card decks with all 16 cards each."""

from __future__ import annotations

import random

from monopoly.engine.types import Card, CardEffect, CardEffectType, CardType


def _build_chance_cards() -> list[Card]:
    """Build all 16 Chance cards."""
    return [
        Card(CardType.CHANCE, CardEffect(
            "Advance to Boardwalk",
            CardEffectType.ADVANCE_TO, destination=39)),
        Card(CardType.CHANCE, CardEffect(
            "Advance to GO (Collect $200)",
            CardEffectType.ADVANCE_TO, destination=0)),
        Card(CardType.CHANCE, CardEffect(
            "Advance to Illinois Avenue. If you pass GO, collect $200",
            CardEffectType.ADVANCE_TO, destination=24)),
        Card(CardType.CHANCE, CardEffect(
            "Advance to St. Charles Place. If you pass GO, collect $200",
            CardEffectType.ADVANCE_TO, destination=11)),
        Card(CardType.CHANCE, CardEffect(
            "Advance to the nearest Railroad. Pay owner twice the rental",
            CardEffectType.ADVANCE_TO_NEAREST, target_type="railroad")),
        Card(CardType.CHANCE, CardEffect(
            "Advance to the nearest Railroad. Pay owner twice the rental",
            CardEffectType.ADVANCE_TO_NEAREST, target_type="railroad")),
        Card(CardType.CHANCE, CardEffect(
            "Advance to the nearest Utility. If unowned, buy it. If owned, roll dice and pay 10x",
            CardEffectType.ADVANCE_TO_NEAREST, target_type="utility")),
        Card(CardType.CHANCE, CardEffect(
            "Bank pays you dividend of $50",
            CardEffectType.COLLECT, value=50)),
        Card(CardType.CHANCE, CardEffect(
            "Get Out of Jail Free",
            CardEffectType.GET_OUT_OF_JAIL)),
        Card(CardType.CHANCE, CardEffect(
            "Go Back 3 Spaces",
            CardEffectType.GO_BACK, value=3)),
        Card(CardType.CHANCE, CardEffect(
            "Go to Jail. Do not pass GO, do not collect $200",
            CardEffectType.GO_TO_JAIL)),
        Card(CardType.CHANCE, CardEffect(
            "Make general repairs on all your property: $25 per house, $100 per hotel",
            CardEffectType.REPAIRS, per_house=25, per_hotel=100)),
        Card(CardType.CHANCE, CardEffect(
            "Speeding fine $15",
            CardEffectType.PAY, value=15)),
        Card(CardType.CHANCE, CardEffect(
            "Take a trip to Reading Railroad. If you pass GO, collect $200",
            CardEffectType.ADVANCE_TO, destination=5)),
        Card(CardType.CHANCE, CardEffect(
            "You have been elected Chairman of the Board. Pay each player $50",
            CardEffectType.PAY_EACH_PLAYER, value=50)),
        Card(CardType.CHANCE, CardEffect(
            "Your building loan matures. Collect $150",
            CardEffectType.COLLECT, value=150)),
    ]


def _build_community_chest_cards() -> list[Card]:
    """Build all 16 Community Chest cards."""
    return [
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Advance to GO (Collect $200)",
            CardEffectType.ADVANCE_TO, destination=0)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Bank error in your favor. Collect $200",
            CardEffectType.COLLECT, value=200)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Doctor's fee. Pay $50",
            CardEffectType.PAY, value=50)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "From sale of stock you get $50",
            CardEffectType.COLLECT, value=50)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Get Out of Jail Free",
            CardEffectType.GET_OUT_OF_JAIL)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Go to Jail. Do not pass GO, do not collect $200",
            CardEffectType.GO_TO_JAIL)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Grand Opera Night. Collect $50 from every player",
            CardEffectType.COLLECT_FROM_EACH, value=50)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Income tax refund. Collect $20",
            CardEffectType.COLLECT, value=20)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "It is your birthday. Collect $10 from every player",
            CardEffectType.COLLECT_FROM_EACH, value=10)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Life insurance matures. Collect $100",
            CardEffectType.COLLECT, value=100)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Hospital fees. Pay $100",
            CardEffectType.PAY, value=100)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "School fees. Pay $50",
            CardEffectType.PAY, value=50)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "Receive $25 consultancy fee",
            CardEffectType.COLLECT, value=25)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "You are assessed for street repairs: $40 per house, $115 per hotel",
            CardEffectType.REPAIRS, per_house=40, per_hotel=115)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "You have won second prize in a beauty contest. Collect $10",
            CardEffectType.COLLECT, value=10)),
        Card(CardType.COMMUNITY_CHEST, CardEffect(
            "You inherit $100",
            CardEffectType.COLLECT, value=100)),
    ]


class Deck:
    """A shuffleable card deck."""

    def __init__(self, cards: list[Card], seed: int | None = None) -> None:
        self._cards = list(cards)
        self._draw_pile: list[Card] = []
        self._rng = random.Random(seed)
        self._jail_card_held = False
        self.shuffle()

    def shuffle(self) -> None:
        """Shuffle all cards back into the draw pile."""
        self._draw_pile = list(self._cards)
        self._rng.shuffle(self._draw_pile)

    def draw(self) -> Card:
        """Draw the top card. If empty, reshuffle (minus held jail cards)."""
        if not self._draw_pile:
            # Reshuffle, excluding Get Out of Jail Free cards that are held
            available = [
                c for c in self._cards
                if not (c.effect.effect_type == CardEffectType.GET_OUT_OF_JAIL
                        and self._jail_card_held)
            ]
            self._draw_pile = list(available)
            self._rng.shuffle(self._draw_pile)

        return self._draw_pile.pop(0)

    def return_jail_card(self) -> None:
        """Return a Get Out of Jail Free card to the deck."""
        self._jail_card_held = False

    def remove_jail_card(self) -> None:
        """Mark that a Get Out of Jail Free card is held by a player."""
        self._jail_card_held = True

    @property
    def cards_remaining(self) -> int:
        return len(self._draw_pile)


def create_chance_deck(seed: int | None = None) -> Deck:
    """Create a shuffled Chance deck."""
    return Deck(_build_chance_cards(), seed=seed)


def create_community_chest_deck(seed: int | None = None) -> Deck:
    """Create a shuffled Community Chest deck."""
    return Deck(_build_community_chest_cards(), seed=seed)
