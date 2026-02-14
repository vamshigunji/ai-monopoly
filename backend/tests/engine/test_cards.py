"""Comprehensive tests for the Chance and Community Chest card decks."""

import pytest

from monopoly.engine.cards import (
    Deck,
    _build_chance_cards,
    _build_community_chest_cards,
    create_chance_deck,
    create_community_chest_deck,
)
from monopoly.engine.types import CardEffectType, CardType


# ── Deck composition tests ───────────────────────────────────────────────────


class TestChanceDeckComposition:
    """Tests for the Chance deck's card composition."""

    def test_chance_deck_has_exactly_16_cards(self):
        """The Chance deck must contain exactly 16 cards."""
        cards = _build_chance_cards()
        assert len(cards) == 16

    def test_all_chance_cards_are_chance_type(self):
        """Every card in the Chance deck must be of type CHANCE."""
        cards = _build_chance_cards()
        for card in cards:
            assert card.deck == CardType.CHANCE

    def test_chance_card_effect_types_are_valid(self):
        """All card effect types in the Chance deck must be valid CardEffectType values."""
        cards = _build_chance_cards()
        valid_types = set(CardEffectType)
        for card in cards:
            assert card.effect.effect_type in valid_types, (
                f"Invalid effect type on card: {card.effect.description}"
            )

    def test_chance_advance_to_boardwalk(self):
        """Chance deck contains 'Advance to Boardwalk' targeting position 39."""
        cards = _build_chance_cards()
        boardwalk_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
            and c.effect.destination == 39
        ]
        assert len(boardwalk_cards) == 1
        assert "Boardwalk" in boardwalk_cards[0].effect.description

    def test_chance_advance_to_go(self):
        """Chance deck contains 'Advance to GO' targeting position 0."""
        cards = _build_chance_cards()
        go_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
            and c.effect.destination == 0
        ]
        assert len(go_cards) == 1
        assert "GO" in go_cards[0].effect.description

    def test_chance_advance_to_illinois_avenue(self):
        """Chance deck contains 'Advance to Illinois Avenue' targeting position 24."""
        cards = _build_chance_cards()
        illinois_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
            and c.effect.destination == 24
        ]
        assert len(illinois_cards) == 1
        assert "Illinois" in illinois_cards[0].effect.description

    def test_chance_advance_to_st_charles_place(self):
        """Chance deck contains 'Advance to St. Charles Place' targeting position 11."""
        cards = _build_chance_cards()
        st_charles_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
            and c.effect.destination == 11
        ]
        assert len(st_charles_cards) == 1
        assert "St. Charles" in st_charles_cards[0].effect.description

    def test_chance_advance_to_reading_railroad(self):
        """Chance deck contains 'Take a trip to Reading Railroad' targeting position 5."""
        cards = _build_chance_cards()
        reading_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
            and c.effect.destination == 5
        ]
        assert len(reading_cards) == 1
        assert "Reading Railroad" in reading_cards[0].effect.description

    def test_chance_two_advance_to_nearest_railroad_cards(self):
        """Chance deck has exactly 2 'Advance to nearest Railroad' cards."""
        cards = _build_chance_cards()
        rr_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO_NEAREST
            and c.effect.target_type == "railroad"
        ]
        assert len(rr_cards) == 2

    def test_chance_advance_to_nearest_utility(self):
        """Chance deck has exactly 1 'Advance to nearest Utility' card."""
        cards = _build_chance_cards()
        util_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO_NEAREST
            and c.effect.target_type == "utility"
        ]
        assert len(util_cards) == 1

    def test_chance_go_to_jail(self):
        """Chance deck contains exactly 1 'Go to Jail' card."""
        cards = _build_chance_cards()
        jail_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.GO_TO_JAIL
        ]
        assert len(jail_cards) == 1

    def test_chance_get_out_of_jail_free(self):
        """Chance deck contains exactly 1 'Get Out of Jail Free' card."""
        cards = _build_chance_cards()
        jail_free_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.GET_OUT_OF_JAIL
        ]
        assert len(jail_free_cards) == 1

    def test_chance_go_back_3_spaces(self):
        """Chance deck has a 'Go Back 3 Spaces' card with value 3."""
        cards = _build_chance_cards()
        go_back = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.GO_BACK
        ]
        assert len(go_back) == 1
        assert go_back[0].effect.value == 3

    def test_chance_repairs_card_values(self):
        """Chance repair card charges $25 per house and $100 per hotel."""
        cards = _build_chance_cards()
        repair_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.REPAIRS
        ]
        assert len(repair_cards) == 1
        assert repair_cards[0].effect.per_house == 25
        assert repair_cards[0].effect.per_hotel == 100

    def test_chance_pay_each_player_card(self):
        """Chance 'Chairman of the Board' card pays $50 to each player."""
        cards = _build_chance_cards()
        pay_each = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.PAY_EACH_PLAYER
        ]
        assert len(pay_each) == 1
        assert pay_each[0].effect.value == 50

    def test_chance_collect_cards(self):
        """Chance deck has 2 COLLECT cards: $50 dividend and $150 building loan."""
        cards = _build_chance_cards()
        collect_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.COLLECT
        ]
        assert len(collect_cards) == 2
        values = sorted(c.effect.value for c in collect_cards)
        assert values == [50, 150]

    def test_chance_pay_card_speeding_fine(self):
        """Chance deck has a PAY card: $15 speeding fine."""
        cards = _build_chance_cards()
        pay_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.PAY
        ]
        assert len(pay_cards) == 1
        assert pay_cards[0].effect.value == 15


class TestCommunityChestDeckComposition:
    """Tests for the Community Chest deck's card composition."""

    def test_community_chest_deck_has_exactly_16_cards(self):
        """The Community Chest deck must contain exactly 16 cards."""
        cards = _build_community_chest_cards()
        assert len(cards) == 16

    def test_all_community_chest_cards_are_community_chest_type(self):
        """Every card must be of type COMMUNITY_CHEST."""
        cards = _build_community_chest_cards()
        for card in cards:
            assert card.deck == CardType.COMMUNITY_CHEST

    def test_community_chest_card_effect_types_are_valid(self):
        """All effect types must be valid CardEffectType values."""
        cards = _build_community_chest_cards()
        valid_types = set(CardEffectType)
        for card in cards:
            assert card.effect.effect_type in valid_types, (
                f"Invalid effect type on card: {card.effect.description}"
            )

    def test_community_chest_advance_to_go(self):
        """Community Chest has 'Advance to GO' targeting position 0."""
        cards = _build_community_chest_cards()
        go_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
            and c.effect.destination == 0
        ]
        assert len(go_cards) == 1

    def test_community_chest_go_to_jail(self):
        """Community Chest has exactly 1 'Go to Jail' card."""
        cards = _build_community_chest_cards()
        jail_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.GO_TO_JAIL
        ]
        assert len(jail_cards) == 1

    def test_community_chest_get_out_of_jail_free(self):
        """Community Chest has exactly 1 'Get Out of Jail Free' card."""
        cards = _build_community_chest_cards()
        jail_free_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.GET_OUT_OF_JAIL
        ]
        assert len(jail_free_cards) == 1

    def test_community_chest_repairs_card_values(self):
        """Community Chest repair card charges $40 per house and $115 per hotel."""
        cards = _build_community_chest_cards()
        repair_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.REPAIRS
        ]
        assert len(repair_cards) == 1
        assert repair_cards[0].effect.per_house == 40
        assert repair_cards[0].effect.per_hotel == 115

    def test_community_chest_collect_from_each_player_cards(self):
        """Community Chest has 2 COLLECT_FROM_EACH cards: $50 and $10."""
        cards = _build_community_chest_cards()
        collect_each = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.COLLECT_FROM_EACH
        ]
        assert len(collect_each) == 2
        values = sorted(c.effect.value for c in collect_each)
        assert values == [10, 50]

    def test_community_chest_collect_cards(self):
        """Community Chest has COLLECT cards with known values."""
        cards = _build_community_chest_cards()
        collect_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.COLLECT
        ]
        values = sorted(c.effect.value for c in collect_cards)
        # $10 (beauty contest), $20 (tax refund), $25 (consultancy),
        # $50 (stock sale), $100 (life insurance, inherit x2 => two separate $100 cards)
        assert values == [10, 20, 25, 50, 100, 100, 200]

    def test_community_chest_pay_cards(self):
        """Community Chest has PAY cards: $50 doctor, $100 hospital, $50 school."""
        cards = _build_community_chest_cards()
        pay_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.PAY
        ]
        values = sorted(c.effect.value for c in pay_cards)
        assert values == [50, 50, 100]


# ── Deck behavior tests ─────────────────────────────────────────────────────


class TestDeckShuffleAndDraw:
    """Tests for deck shuffling and drawing mechanics."""

    def test_deterministic_shuffle_with_seed(self):
        """Two decks with the same seed produce the same card order."""
        deck_a = create_chance_deck(seed=42)
        deck_b = create_chance_deck(seed=42)

        for _ in range(16):
            card_a = deck_a.draw()
            card_b = deck_b.draw()
            assert card_a.effect.description == card_b.effect.description

    def test_different_seeds_produce_different_order(self):
        """Two decks with different seeds produce different card orders."""
        deck_a = create_chance_deck(seed=42)
        deck_b = create_chance_deck(seed=99)

        # Draw all 16; at least one pair should differ
        descriptions_a = [deck_a.draw().effect.description for _ in range(16)]
        descriptions_b = [deck_b.draw().effect.description for _ in range(16)]
        assert descriptions_a != descriptions_b

    def test_draw_all_cards_and_reshuffle(self):
        """After drawing all 16 cards the deck reshuffles and cards are available again."""
        deck = create_chance_deck(seed=7)
        assert deck.cards_remaining == 16

        # Draw all 16 cards
        for _ in range(16):
            deck.draw()
        assert deck.cards_remaining == 0

        # Drawing again triggers a reshuffle
        card = deck.draw()
        assert card is not None
        # After reshuffle + drawing one, we should have 15 remaining
        assert deck.cards_remaining == 15

    def test_cards_remaining_decrements(self):
        """cards_remaining decreases by 1 after each draw."""
        deck = create_community_chest_deck(seed=1)
        assert deck.cards_remaining == 16

        deck.draw()
        assert deck.cards_remaining == 15

        deck.draw()
        assert deck.cards_remaining == 14

    def test_reshuffle_preserves_all_cards_when_no_jail_card_held(self):
        """After a reshuffle with no jail card held, all 16 cards are back."""
        deck = create_chance_deck(seed=5)

        # Draw all 16
        for _ in range(16):
            deck.draw()

        # Trigger reshuffle by drawing one more
        deck.draw()
        # 16 reshuffled, then 1 drawn => 15 remain
        assert deck.cards_remaining == 15


class TestGetOutOfJailFreeCardMechanics:
    """Tests for the Get Out of Jail Free card hold/return mechanics."""

    def test_jail_card_removed_from_deck_when_held(self):
        """When a jail card is marked as held, reshuffle omits it from the draw pile."""
        deck = create_chance_deck(seed=10)
        deck.remove_jail_card()

        # Draw all remaining cards to trigger reshuffle
        for _ in range(deck.cards_remaining):
            deck.draw()

        # Trigger reshuffle
        deck.draw()
        # After reshuffle, deck should have 15 cards (minus jail card) then draw 1 => 14
        assert deck.cards_remaining == 14

    def test_jail_card_returns_to_deck_when_returned(self):
        """After returning the jail card, it is included in the next reshuffle."""
        deck = create_chance_deck(seed=10)
        deck.remove_jail_card()
        deck.return_jail_card()

        # Exhaust and reshuffle
        for _ in range(deck.cards_remaining):
            deck.draw()

        deck.draw()
        # All 16 cards should be back (16 - 1 drawn = 15)
        assert deck.cards_remaining == 15

    def test_remove_and_return_jail_card_cycle(self):
        """Can remove and return the jail card multiple times."""
        deck = create_community_chest_deck(seed=20)

        # First cycle: remove
        deck.remove_jail_card()
        for _ in range(deck.cards_remaining):
            deck.draw()
        deck.draw()
        assert deck.cards_remaining == 14  # 15 reshuffled - 1 drawn

        # Return
        deck.return_jail_card()
        for _ in range(deck.cards_remaining):
            deck.draw()
        deck.draw()
        assert deck.cards_remaining == 15  # 16 reshuffled - 1 drawn

    def test_initial_deck_not_missing_jail_card(self):
        """The initial deck (before any removal) includes the jail card."""
        deck = create_chance_deck(seed=3)
        drawn_cards = [deck.draw() for _ in range(16)]
        jail_cards = [
            c for c in drawn_cards
            if c.effect.effect_type == CardEffectType.GET_OUT_OF_JAIL
        ]
        assert len(jail_cards) == 1

    def test_held_jail_card_excluded_across_multiple_reshuffles(self):
        """The jail card stays excluded across consecutive reshuffles while held."""
        deck = create_chance_deck(seed=55)
        deck.remove_jail_card()

        for _cycle in range(3):
            # Draw until empty then trigger reshuffle
            while deck.cards_remaining > 0:
                deck.draw()
            # Trigger reshuffle
            deck.draw()
            # Should always be 14 remaining after reshuffle + 1 draw
            assert deck.cards_remaining == 14


class TestDeckFactoryFunctions:
    """Tests for the create_chance_deck and create_community_chest_deck helpers."""

    def test_create_chance_deck_returns_deck(self):
        """create_chance_deck returns a Deck instance."""
        deck = create_chance_deck()
        assert isinstance(deck, Deck)

    def test_create_community_chest_deck_returns_deck(self):
        """create_community_chest_deck returns a Deck instance."""
        deck = create_community_chest_deck()
        assert isinstance(deck, Deck)

    def test_create_chance_deck_with_seed(self):
        """create_chance_deck accepts a seed parameter."""
        deck = create_chance_deck(seed=123)
        assert deck.cards_remaining == 16

    def test_create_community_chest_deck_with_seed(self):
        """create_community_chest_deck accepts a seed parameter."""
        deck = create_community_chest_deck(seed=456)
        assert deck.cards_remaining == 16

    def test_create_chance_deck_without_seed(self):
        """create_chance_deck works without a seed (random shuffling)."""
        deck = create_chance_deck()
        assert deck.cards_remaining == 16

    def test_deck_draw_returns_card_instances(self):
        """Each draw returns a proper Card object with deck and effect attributes."""
        deck = create_chance_deck(seed=1)
        card = deck.draw()
        assert hasattr(card, "deck")
        assert hasattr(card, "effect")
        assert card.deck == CardType.CHANCE
        assert hasattr(card.effect, "description")
        assert hasattr(card.effect, "effect_type")


class TestCardEffectDefaults:
    """Tests for default values on CardEffect fields."""

    def test_advance_to_card_has_destination(self):
        """ADVANCE_TO cards must have a non-negative destination."""
        cards = _build_chance_cards()
        advance_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO
        ]
        for card in advance_cards:
            assert card.effect.destination >= 0, (
                f"Card '{card.effect.description}' has invalid destination: {card.effect.destination}"
            )

    def test_advance_to_nearest_card_has_target_type(self):
        """ADVANCE_TO_NEAREST cards must have a non-empty target_type."""
        cards = _build_chance_cards()
        nearest_cards = [
            c for c in cards
            if c.effect.effect_type == CardEffectType.ADVANCE_TO_NEAREST
        ]
        for card in nearest_cards:
            assert card.effect.target_type in ("railroad", "utility"), (
                f"Card '{card.effect.description}' has invalid target_type: {card.effect.target_type}"
            )

    def test_collect_cards_have_positive_values(self):
        """COLLECT cards must have a positive value."""
        for builder in (_build_chance_cards, _build_community_chest_cards):
            cards = builder()
            collect_cards = [
                c for c in cards
                if c.effect.effect_type == CardEffectType.COLLECT
            ]
            for card in collect_cards:
                assert card.effect.value > 0, (
                    f"Card '{card.effect.description}' has non-positive value: {card.effect.value}"
                )

    def test_pay_cards_have_positive_values(self):
        """PAY cards must have a positive value."""
        for builder in (_build_chance_cards, _build_community_chest_cards):
            cards = builder()
            pay_cards = [
                c for c in cards
                if c.effect.effect_type == CardEffectType.PAY
            ]
            for card in pay_cards:
                assert card.effect.value > 0, (
                    f"Card '{card.effect.description}' has non-positive value: {card.effect.value}"
                )

    def test_repairs_cards_have_positive_per_house_and_per_hotel(self):
        """REPAIRS cards must have positive per_house and per_hotel amounts."""
        for builder in (_build_chance_cards, _build_community_chest_cards):
            cards = builder()
            repair_cards = [
                c for c in cards
                if c.effect.effect_type == CardEffectType.REPAIRS
            ]
            for card in repair_cards:
                assert card.effect.per_house > 0
                assert card.effect.per_hotel > 0
                assert card.effect.per_hotel > card.effect.per_house, (
                    "Hotel repair cost should exceed house repair cost"
                )
