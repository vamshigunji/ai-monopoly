"""Game state machine — the core Monopoly game loop and state management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from monopoly.engine.bank import Bank
from monopoly.engine.board import Board, PROPERTIES, RAILROADS, UTILITIES, COLOR_GROUP_POSITIONS
from monopoly.engine.cards import Deck, create_chance_deck, create_community_chest_deck
from monopoly.engine.dice import Dice
from monopoly.engine.player import Player
from monopoly.engine.rules import Rules
from monopoly.engine.trade import execute_trade
from monopoly.engine.types import (
    CardEffectType,
    DiceRoll,
    EventType,
    GameEvent,
    GamePhase,
    JailAction,
    SpaceType,
    TradeProposal,
    TurnPhase,
)


GO_SALARY = 200
JAIL_FINE = 50
MAX_JAIL_TURNS = 3


@dataclass
class LandingResult:
    """Result of landing on a space — what action is needed."""
    space_type: SpaceType
    position: int
    requires_buy_decision: bool = False
    rent_owed: int = 0
    rent_to_player: int = -1
    card_drawn: Optional[str] = None
    tax_amount: int = 0
    sent_to_jail: bool = False


class Game:
    """Core Monopoly game state machine."""

    def __init__(self, num_players: int = 4, seed: int | None = None) -> None:
        self.board = Board()
        self.dice = Dice(seed=seed)
        self.bank = Bank()
        self.rules = Rules(self.board)
        self.chance_deck: Deck = create_chance_deck(seed=seed)
        self.community_chest_deck: Deck = create_community_chest_deck(
            seed=(seed + 1) if seed is not None else None
        )

        self.players: list[Player] = [
            Player(player_id=i, name=f"Player{i + 1}")
            for i in range(num_players)
        ]

        self.current_player_index: int = 0
        self.turn_number: int = 0
        self.phase: GamePhase = GamePhase.IN_PROGRESS
        self.turn_phase: TurnPhase = TurnPhase.PRE_ROLL
        self.last_roll: DiceRoll | None = None
        self.events: list[GameEvent] = []

        # Property ownership tracking: position -> player_id (or -1 if unowned)
        self._property_owners: dict[int, int] = {}

    # ── Property ownership ──────────────────────────────────────────────

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def get_property_owner(self, position: int) -> Player | None:
        """Get the player who owns a property, or None."""
        owner_id = self._property_owners.get(position, -1)
        if owner_id == -1:
            return None
        return self.players[owner_id]

    def is_property_owned(self, position: int) -> bool:
        """Check if a property position is owned by any player."""
        return position in self._property_owners

    def assign_property(self, player: Player, position: int) -> None:
        """Assign a property to a player."""
        self._property_owners[position] = player.player_id
        player.add_property(position)

    def transfer_property(self, from_player: Player, to_player: Player, position: int) -> None:
        """Transfer a property from one player to another."""
        from_player.remove_property(position)
        to_player.add_property(position)
        self._property_owners[position] = to_player.player_id

    def unown_property(self, position: int) -> None:
        """Remove ownership of a property (for bankruptcy to bank)."""
        self._property_owners.pop(position, None)

    # ── Dice rolling ────────────────────────────────────────────────────

    def roll_dice(self) -> DiceRoll:
        """Roll the dice and return the result."""
        roll = self.dice.roll()
        self.last_roll = roll
        self._emit(EventType.DICE_ROLLED, data={
            "die1": roll.die1, "die2": roll.die2,
            "total": roll.total, "doubles": roll.is_doubles,
        })
        return roll

    # ── Movement ────────────────────────────────────────────────────────

    def move_player(self, player: Player, spaces: int) -> bool:
        """Move a player forward. Returns True if passed GO."""
        passed_go = player.move_forward(spaces)
        self._emit(EventType.PLAYER_MOVED, player_id=player.player_id, data={
            "new_position": player.position, "spaces_moved": spaces,
        })
        if passed_go:
            player.add_cash(GO_SALARY)
            self._emit(EventType.PASSED_GO, player_id=player.player_id, data={
                "salary": GO_SALARY,
            })
        return passed_go

    def move_player_to(self, player: Player, position: int, collect_go: bool = True) -> bool:
        """Move a player to a specific position. Returns True if passed GO."""
        passed_go = player.move_to(position)
        self._emit(EventType.PLAYER_MOVED, player_id=player.player_id, data={
            "new_position": player.position, "direct_move": True,
        })
        if passed_go and collect_go:
            player.add_cash(GO_SALARY)
            self._emit(EventType.PASSED_GO, player_id=player.player_id, data={
                "salary": GO_SALARY,
            })
        return passed_go

    # ── Landing ─────────────────────────────────────────────────────────

    def process_landing(self, player: Player) -> LandingResult:
        """Process landing on a space. Returns what action is needed."""
        space = self.board.get_space(player.position)
        result = LandingResult(space_type=space.space_type, position=player.position)

        if space.space_type == SpaceType.PROPERTY:
            self._handle_property_landing(player, result)
        elif space.space_type == SpaceType.RAILROAD:
            self._handle_railroad_landing(player, result)
        elif space.space_type == SpaceType.UTILITY:
            self._handle_utility_landing(player, result)
        elif space.space_type == SpaceType.TAX:
            self._handle_tax(player, space, result)
        elif space.space_type == SpaceType.CHANCE:
            self._handle_card(player, self.chance_deck, result)
        elif space.space_type == SpaceType.COMMUNITY_CHEST:
            self._handle_card(player, self.community_chest_deck, result)
        elif space.space_type == SpaceType.GO_TO_JAIL:
            self._send_to_jail(player)
            result.sent_to_jail = True

        return result

    def _handle_property_landing(self, player: Player, result: LandingResult) -> None:
        """Handle landing on a property space."""
        pos = player.position
        owner = self.get_property_owner(pos)

        if owner is None:
            result.requires_buy_decision = True
        elif owner.player_id != player.player_id and not owner.is_mortgaged(pos):
            rent = self.rules.calculate_rent(pos, owner, self.last_roll)
            result.rent_owed = rent
            result.rent_to_player = owner.player_id

    def _handle_railroad_landing(self, player: Player, result: LandingResult) -> None:
        """Handle landing on a railroad."""
        pos = player.position
        owner = self.get_property_owner(pos)

        if owner is None:
            result.requires_buy_decision = True
        elif owner.player_id != player.player_id and not owner.is_mortgaged(pos):
            rent = self.rules.calculate_rent(pos, owner)
            result.rent_owed = rent
            result.rent_to_player = owner.player_id

    def _handle_utility_landing(self, player: Player, result: LandingResult) -> None:
        """Handle landing on a utility."""
        pos = player.position
        owner = self.get_property_owner(pos)

        if owner is None:
            result.requires_buy_decision = True
        elif owner.player_id != player.player_id and not owner.is_mortgaged(pos):
            rent = self.rules.calculate_rent(pos, owner, self.last_roll)
            result.rent_owed = rent
            result.rent_to_player = owner.player_id

    def _handle_tax(self, player: Player, space, result: LandingResult) -> None:
        """Handle landing on a tax space."""
        tax = space.tax_data.amount
        player.remove_cash(tax)
        result.tax_amount = tax
        self._emit(EventType.TAX_PAID, player_id=player.player_id, data={
            "amount": tax, "space": space.name,
        })

    def _handle_card(self, player: Player, deck: Deck, result: LandingResult) -> None:
        """Handle drawing a Chance or Community Chest card."""
        card = deck.draw()
        effect = card.effect
        result.card_drawn = effect.description

        self._emit(EventType.CARD_DRAWN, player_id=player.player_id, data={
            "description": effect.description,
            "deck": card.deck.name,
        })

        self._apply_card_effect(player, card, deck)

    def _apply_card_effect(self, player: Player, card, deck: Deck) -> None:
        """Apply a card's effect to the player."""
        effect = card.effect

        if effect.effect_type == CardEffectType.ADVANCE_TO:
            collect_go = effect.destination != 10  # Don't collect GO if going to jail
            self.move_player_to(player, effect.destination, collect_go=collect_go)
            # Process the new landing
            new_result = self.process_landing(player)
            if new_result.rent_owed > 0:
                self.pay_rent(player, new_result.rent_to_player, new_result.rent_owed)

        elif effect.effect_type == CardEffectType.ADVANCE_TO_NEAREST:
            if effect.target_type == "railroad":
                target = self.board.get_nearest_railroad(player.position)
                self.move_player_to(player, target)
                owner = self.get_property_owner(target)
                if owner is not None and owner.player_id != player.player_id:
                    # Pay double railroad rent
                    rent = self.rules.calculate_rent(target, owner) * 2
                    self.pay_rent(player, owner.player_id, rent)
                elif owner is None:
                    pass  # Landing result will handle buy decision on next check
            elif effect.target_type == "utility":
                target = self.board.get_nearest_utility(player.position)
                self.move_player_to(player, target)
                owner = self.get_property_owner(target)
                if owner is not None and owner.player_id != player.player_id:
                    # Roll dice and pay 10x
                    roll = self.roll_dice()
                    rent = roll.total * 10
                    self.pay_rent(player, owner.player_id, rent)

        elif effect.effect_type == CardEffectType.GO_BACK:
            new_pos = (player.position - effect.value) % 40
            player.position = new_pos
            self._emit(EventType.PLAYER_MOVED, player_id=player.player_id, data={
                "new_position": new_pos, "went_back": effect.value,
            })
            # Process landing on the new space
            new_result = self.process_landing(player)
            if new_result.rent_owed > 0:
                self.pay_rent(player, new_result.rent_to_player, new_result.rent_owed)

        elif effect.effect_type == CardEffectType.COLLECT:
            player.add_cash(effect.value)

        elif effect.effect_type == CardEffectType.PAY:
            player.remove_cash(effect.value)

        elif effect.effect_type == CardEffectType.PAY_EACH_PLAYER:
            active_players = [p for p in self.players if not p.is_bankrupt]
            for other in active_players:
                if other.player_id != player.player_id:
                    player.remove_cash(effect.value)
                    other.add_cash(effect.value)

        elif effect.effect_type == CardEffectType.COLLECT_FROM_EACH:
            active_players = [p for p in self.players if not p.is_bankrupt]
            for other in active_players:
                if other.player_id != player.player_id:
                    other.remove_cash(effect.value)
                    player.add_cash(effect.value)

        elif effect.effect_type == CardEffectType.REPAIRS:
            total_cost = 0
            for pos in player.properties:
                houses = player.get_house_count(pos)
                if houses == 5:  # hotel
                    total_cost += effect.per_hotel
                elif houses > 0:
                    total_cost += effect.per_house * houses
            player.remove_cash(total_cost)

        elif effect.effect_type == CardEffectType.GO_TO_JAIL:
            self._send_to_jail(player)

        elif effect.effect_type == CardEffectType.GET_OUT_OF_JAIL:
            player.get_out_of_jail_cards += 1
            deck.remove_jail_card()

    # ── Rent payment ────────────────────────────────────────────────────

    def pay_rent(self, payer: Player, owner_id: int, amount: int) -> None:
        """Process rent payment from one player to another."""
        owner = self.players[owner_id]
        payer.remove_cash(amount)
        owner.add_cash(amount)
        self._emit(EventType.RENT_PAID, player_id=payer.player_id, data={
            "amount": amount, "to_player": owner_id,
        })

    # ── Buying and auctioning ───────────────────────────────────────────

    def buy_property(self, player: Player, position: int) -> bool:
        """Player buys a property at listed price. Returns success."""
        price = self.board.get_purchase_price(position)
        if price == 0 or player.cash < price:
            return False
        if self.is_property_owned(position):
            return False

        player.remove_cash(price)
        self.assign_property(player, position)
        self._emit(EventType.PROPERTY_PURCHASED, player_id=player.player_id, data={
            "position": position, "price": price,
            "name": self.board.get_space(position).name,
        })
        return True

    def auction_property(self, position: int, bids: dict[int, int]) -> int | None:
        """Auction a property. bids = {player_id: bid_amount}.
        Returns the winning player_id or None if no bids."""
        if not bids:
            return None

        # Filter valid bids (player must have enough cash)
        valid_bids = {
            pid: amount for pid, amount in bids.items()
            if amount > 0 and self.players[pid].cash >= amount
            and not self.players[pid].is_bankrupt
        }

        if not valid_bids:
            return None

        winner_id = max(valid_bids, key=valid_bids.get)
        winning_bid = valid_bids[winner_id]
        winner = self.players[winner_id]

        winner.remove_cash(winning_bid)
        self.assign_property(winner, position)

        self._emit(EventType.AUCTION_WON, player_id=winner_id, data={
            "position": position, "bid": winning_bid,
            "name": self.board.get_space(position).name,
        })
        return winner_id

    # ── Building ────────────────────────────────────────────────────────

    def build_house(self, player: Player, position: int) -> bool:
        """Build a house on a property. Returns success."""
        if not self.rules.can_build_house(player, position, self.bank):
            return False

        prop = PROPERTIES[position]
        player.remove_cash(prop.house_cost)
        player.set_houses(position, player.get_house_count(position) + 1)
        self.bank.buy_house()

        self._emit(EventType.HOUSE_BUILT, player_id=player.player_id, data={
            "position": position, "houses": player.get_house_count(position),
            "name": prop.name,
        })
        return True

    def build_hotel(self, player: Player, position: int) -> bool:
        """Build a hotel on a property (upgrade from 4 houses). Returns success."""
        if not self.rules.can_build_hotel(player, position, self.bank):
            return False

        prop = PROPERTIES[position]
        player.remove_cash(prop.house_cost)
        player.set_houses(position, 5)  # 5 = hotel
        self.bank.upgrade_to_hotel()

        self._emit(EventType.HOTEL_BUILT, player_id=player.player_id, data={
            "position": position, "name": prop.name,
        })
        return True

    def sell_house(self, player: Player, position: int) -> bool:
        """Sell a house back to the bank at half price."""
        if not self.rules.can_sell_house(player, position):
            return False

        prop = PROPERTIES[position]
        refund = prop.house_cost // 2
        player.add_cash(refund)
        player.set_houses(position, player.get_house_count(position) - 1)
        self.bank.return_house()

        self._emit(EventType.BUILDING_SOLD, player_id=player.player_id, data={
            "position": position, "refund": refund,
        })
        return True

    def sell_hotel(self, player: Player, position: int) -> bool:
        """Sell a hotel (downgrade to 4 houses if available, else sell all)."""
        if player.get_house_count(position) != 5:
            return False

        prop = PROPERTIES[position]
        refund = prop.house_cost // 2

        if self.bank.downgrade_from_hotel():
            # Downgrade to 4 houses
            player.set_houses(position, 4)
            player.add_cash(refund)
        else:
            # No houses available — must sell hotel entirely
            player.set_houses(position, 0)
            player.add_cash(refund * 5)  # Refund for hotel = 5 * half house cost
            self.bank.return_hotel()

        self._emit(EventType.BUILDING_SOLD, player_id=player.player_id, data={
            "position": position, "refund": refund,
        })
        return True

    # ── Mortgage ────────────────────────────────────────────────────────

    def mortgage_property(self, player: Player, position: int) -> bool:
        """Mortgage a property."""
        if not self.rules.can_mortgage(player, position):
            return False

        mortgage_value = self.rules.get_mortgage_value(position)
        player.add_cash(mortgage_value)
        player.mortgage_property(position)

        self._emit(EventType.PROPERTY_MORTGAGED, player_id=player.player_id, data={
            "position": position, "value": mortgage_value,
        })
        return True

    def unmortgage_property(self, player: Player, position: int) -> bool:
        """Unmortgage a property (pay mortgage + 10% interest)."""
        if not self.rules.can_unmortgage(player, position):
            return False

        cost = self.rules.unmortgage_cost(position)
        player.remove_cash(cost)
        player.unmortgage_property(position)

        self._emit(EventType.PROPERTY_UNMORTGAGED, player_id=player.player_id, data={
            "position": position, "cost": cost,
        })
        return True

    # ── Jail ────────────────────────────────────────────────────────────

    def _send_to_jail(self, player: Player) -> None:
        """Send a player to jail."""
        player.send_to_jail()
        self._emit(EventType.PLAYER_JAILED, player_id=player.player_id)

    def handle_jail_turn(self, player: Player, action: JailAction) -> DiceRoll | None:
        """Handle a jailed player's turn. Returns dice roll if they rolled."""
        if not player.in_jail:
            return None

        if action == JailAction.PAY_FINE:
            if player.cash >= JAIL_FINE:
                player.remove_cash(JAIL_FINE)
                player.release_from_jail()
                self._emit(EventType.PLAYER_FREED, player_id=player.player_id, data={
                    "method": "paid_fine",
                })
            return None

        elif action == JailAction.USE_CARD:
            if player.get_out_of_jail_cards > 0:
                player.get_out_of_jail_cards -= 1
                player.release_from_jail()
                # Return the card to the appropriate deck
                # (simplified: we return to both decks' pool)
                self.chance_deck.return_jail_card()
                self.community_chest_deck.return_jail_card()
                self._emit(EventType.PLAYER_FREED, player_id=player.player_id, data={
                    "method": "used_card",
                })
            return None

        elif action == JailAction.ROLL_DOUBLES:
            roll = self.roll_dice()
            player.jail_turns += 1

            if roll.is_doubles:
                player.release_from_jail()
                self._emit(EventType.PLAYER_FREED, player_id=player.player_id, data={
                    "method": "rolled_doubles", "roll": roll.total,
                })
                return roll
            elif player.jail_turns >= MAX_JAIL_TURNS:
                # Must pay fine after 3 failed attempts
                player.remove_cash(JAIL_FINE)
                player.release_from_jail()
                self._emit(EventType.PLAYER_FREED, player_id=player.player_id, data={
                    "method": "forced_payment", "roll": roll.total,
                })
                return roll
            return None

        return None

    # ── Trading ─────────────────────────────────────────────────────────

    def execute_trade(self, proposal: TradeProposal) -> tuple[bool, str]:
        """Validate and execute a trade proposal."""
        proposer = self.players[proposal.proposer_id]
        receiver = self.players[proposal.receiver_id]

        is_valid, reason = self.rules.validate_trade(proposal, proposer, receiver)
        if not is_valid:
            self._emit(EventType.TRADE_REJECTED, player_id=proposer.player_id, data={
                "reason": reason,
            })
            return False, reason

        events = execute_trade(proposal, proposer, receiver, self.rules)

        # Update property ownership tracking
        for pos in proposal.offered_properties:
            self._property_owners[pos] = receiver.player_id
        for pos in proposal.requested_properties:
            self._property_owners[pos] = proposer.player_id

        self.events.extend(events)
        return True, ""

    # ── Bankruptcy ──────────────────────────────────────────────────────

    def declare_bankruptcy(self, player: Player, creditor_id: int | None = None) -> None:
        """Handle a player going bankrupt."""
        player.is_bankrupt = True

        if creditor_id is not None:
            # Bankrupt to another player: transfer all assets
            creditor = self.players[creditor_id]
            for pos in list(player.properties):
                is_mortgaged = player.is_mortgaged(pos)
                player.remove_property(pos)
                creditor.add_property(pos)
                self._property_owners[pos] = creditor.player_id
                if is_mortgaged:
                    creditor.mortgage_property(pos)
            creditor.add_cash(player.cash)
            creditor.get_out_of_jail_cards += player.get_out_of_jail_cards
        else:
            # Bankrupt to the bank: properties go to auction
            for pos in list(player.properties):
                # Return any buildings
                houses = player.get_house_count(pos)
                if houses == 5:
                    self.bank.return_hotel()
                else:
                    for _ in range(houses):
                        self.bank.return_house()
                player.remove_property(pos)
                self.unown_property(pos)

        player.cash = 0
        player.get_out_of_jail_cards = 0
        player.properties.clear()
        player.houses.clear()
        player.mortgaged.clear()

        self._emit(EventType.PLAYER_BANKRUPT, player_id=player.player_id, data={
            "creditor_id": creditor_id,
        })

    # ── Turn management ─────────────────────────────────────────────────

    def advance_turn(self) -> None:
        """Advance to the next player's turn."""
        self.turn_number += 1
        # Find next non-bankrupt player
        for _ in range(len(self.players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if not self.current_player.is_bankrupt:
                break

        self.turn_phase = TurnPhase.PRE_ROLL
        self._emit(EventType.TURN_STARTED, player_id=self.current_player.player_id, data={
            "turn_number": self.turn_number,
        })

    def is_over(self) -> bool:
        """Check if the game is over (only 1 player remaining)."""
        active = [p for p in self.players if not p.is_bankrupt]
        return len(active) <= 1

    def get_winner(self) -> Player | None:
        """Get the winning player, or None if game isn't over."""
        if not self.is_over():
            return None
        active = [p for p in self.players if not p.is_bankrupt]
        return active[0] if active else None

    def get_active_players(self) -> list[Player]:
        """Get all non-bankrupt players."""
        return [p for p in self.players if not p.is_bankrupt]

    # ── Event system ────────────────────────────────────────────────────

    def _emit(self, event_type: EventType, player_id: int = -1, data: dict | None = None) -> None:
        """Emit a game event."""
        event = GameEvent(
            event_type=event_type,
            player_id=player_id,
            data=data or {},
            turn_number=self.turn_number,
        )
        self.events.append(event)

    def get_events_since(self, index: int) -> list[GameEvent]:
        """Get all events since a given index."""
        return self.events[index:]
