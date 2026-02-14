"""Trade execution logic for Monopoly."""

from __future__ import annotations

from monopoly.engine.player import Player
from monopoly.engine.rules import Rules
from monopoly.engine.types import TradeProposal, GameEvent, EventType


def execute_trade(
    proposal: TradeProposal,
    proposer: Player,
    receiver: Player,
    rules: Rules,
) -> list[GameEvent]:
    """Execute a validated trade between two players.

    Returns a list of game events describing what happened.
    Assumes the trade has already been validated via rules.validate_trade().
    """
    events: list[GameEvent] = []

    # Transfer properties from proposer to receiver
    for pos in proposal.offered_properties:
        is_mortgaged = proposer.is_mortgaged(pos)
        proposer.remove_property(pos)
        receiver.add_property(pos)
        if is_mortgaged:
            receiver.mortgage_property(pos)
            # Receiver pays 10% transfer fee immediately
            fee = rules.mortgage_transfer_fee(pos)
            receiver.remove_cash(fee)

    # Transfer properties from receiver to proposer
    for pos in proposal.requested_properties:
        is_mortgaged = receiver.is_mortgaged(pos)
        receiver.remove_property(pos)
        proposer.add_property(pos)
        if is_mortgaged:
            proposer.mortgage_property(pos)
            fee = rules.mortgage_transfer_fee(pos)
            proposer.remove_cash(fee)

    # Transfer cash
    if proposal.offered_cash > 0:
        proposer.remove_cash(proposal.offered_cash)
        receiver.add_cash(proposal.offered_cash)

    if proposal.requested_cash > 0:
        receiver.remove_cash(proposal.requested_cash)
        proposer.add_cash(proposal.requested_cash)

    # Transfer Get Out of Jail Free cards
    if proposal.offered_jail_cards > 0:
        proposer.get_out_of_jail_cards -= proposal.offered_jail_cards
        receiver.get_out_of_jail_cards += proposal.offered_jail_cards

    if proposal.requested_jail_cards > 0:
        receiver.get_out_of_jail_cards -= proposal.requested_jail_cards
        proposer.get_out_of_jail_cards += proposal.requested_jail_cards

    events.append(GameEvent(
        event_type=EventType.TRADE_ACCEPTED,
        player_id=proposer.player_id,
        data={
            "proposer_id": proposer.player_id,
            "receiver_id": receiver.player_id,
            "offered_properties": proposal.offered_properties,
            "requested_properties": proposal.requested_properties,
            "offered_cash": proposal.offered_cash,
            "requested_cash": proposal.requested_cash,
        },
    ))

    return events
