/**
 * Game event log
 * Chronological stream of all game events with filtering
 */

"use client";

import { useState, useEffect, useRef } from "react";
import { useGameStore } from "@/stores/gameStore";
import { Filter } from "lucide-react";
import type { EventType } from "@/lib/types";
import { getSpaceName } from "@/lib/boardData";

const AGENT_NAMES = ["Shark", "Professor", "Hustler", "Turtle"];
const AGENT_COLORS = ["text-red-600", "text-blue-600", "text-amber-600", "text-green-600"];

// Event type categories for filtering
const EVENT_CATEGORIES = {
  movement: ["DICE_ROLLED", "PLAYER_MOVED", "PASSED_GO"],
  property: ["PROPERTY_PURCHASED", "HOUSE_BUILT", "HOTEL_BUILT", "PROPERTY_MORTGAGED", "PROPERTY_UNMORTGAGED"],
  finance: ["RENT_PAID", "TAX_PAID"],
  trading: ["TRADE_PROPOSED", "TRADE_ACCEPTED", "TRADE_REJECTED"],
  cards: ["CARD_DRAWN", "CARD_EFFECT"],
  jail: ["PLAYER_JAILED", "PLAYER_FREED"],
  other: ["GAME_STARTED", "TURN_STARTED", "PLAYER_BANKRUPT", "GAME_OVER", "AUCTION_STARTED", "AUCTION_BID", "AUCTION_WON"],
};

export function GameLog() {
  const events = useGameStore((state) => state.events);
  const [filter, setFilter] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);

  // Track whether user is scrolled near the bottom
  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      isNearBottomRef.current = scrollHeight - scrollTop - clientHeight < 60;
    }
  };

  // Auto-scroll only if user is near the bottom
  useEffect(() => {
    if (scrollRef.current && isNearBottomRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const filteredEvents = filter
    ? events.filter((e) => {
        const category = Object.entries(EVENT_CATEGORIES).find(([_, types]) =>
          types.includes(e.event_type as EventType)
        );
        return category?.[0] === filter;
      })
    : events;

  const formatEvent = (event: any) => {
    const playerName =
      event.player_id >= 0 && event.player_id < 4
        ? AGENT_NAMES[event.player_id]
        : "Game";
    const playerColor =
      event.player_id >= 0 && event.player_id < 4
        ? AGENT_COLORS[event.player_id]
        : "text-gray-800";

    let description = "";

    switch (event.event_type) {
      case "GAME_STARTED":
        description = `🎮 New game started!`;
        break;
      case "TURN_STARTED":
        description = `🎯 ${playerName}'s turn begins`;
        break;
      case "DICE_ROLLED":
        description = `🎲 Rolled ${event.data.die1} + ${event.data.die2} = ${event.data.total}${event.data.is_doubles ? " 🎊 DOUBLES!" : ""}`;
        break;
      case "PLAYER_MOVED": {
        const spaceName = event.data.space_name || getSpaceName(event.data.position);
        description = `🚶 Moved to ${spaceName}`;
        break;
      }
      case "PASSED_GO":
        description = `💰 Passed GO! Collected $${event.data.salary || 200} 🎉`;
        break;
      case "PROPERTY_PURCHASED":
        description = `🏘️ Purchased ${event.data.name} for $${event.data.price} 💰`;
        break;
      case "RENT_PAID": {
        const toPlayer = event.data.to_player !== undefined ? AGENT_NAMES[event.data.to_player] : "the bank";
        description = `💸 Paid $${event.data.amount} rent to ${toPlayer}`;
        break;
      }
      case "TAX_PAID":
        description = `💰 Paid $${event.data.amount} ${event.data.space || "tax"}`;
        break;
      case "HOUSE_BUILT":
        description = `🏠 Built house #${event.data.houses} on ${event.data.name}`;
        break;
      case "HOTEL_BUILT":
        description = `🏨 Built HOTEL on ${event.data.name}! 🎊`;
        break;
      case "PROPERTY_MORTGAGED":
        description = `🏦 Mortgaged ${event.data.name || "property"} for $${event.data.value}`;
        break;
      case "PROPERTY_UNMORTGAGED":
        description = `🏦 Unmortgaged ${event.data.name || "property"} for $${event.data.cost}`;
        break;
      case "TRADE_PROPOSED":
        description = `🤝 Proposed trade with ${AGENT_NAMES[event.data.to_player] || "opponent"}`;
        break;
      case "TRADE_ACCEPTED":
        description = `✅ Accepted trade with ${AGENT_NAMES[event.data.receiver_id ?? event.data.from_player] || "opponent"}`;
        break;
      case "TRADE_REJECTED":
        description = `❌ Rejected trade from ${AGENT_NAMES[event.data.from_player ?? event.player_id] || "opponent"}`;
        break;
      case "PLAYER_JAILED":
        description = `⛓️ Sent to Jail!`;
        break;
      case "PLAYER_FREED": {
        const method = event.data.method === "CARD" || event.data.method === "card" ? "using Get Out of Jail card" :
                      event.data.method === "PAY" || event.data.method === "payment" ? "paying $50" :
                      "rolling doubles";
        description = `🔓 Left jail by ${method}`;
        break;
      }
      case "CARD_DRAWN":
        description = `🎴 Drew ${event.data.card_type || "card"}: "${event.data.description || "..."}"`;
        break;
      case "AUCTION_STARTED": {
        const auctionProp = event.data.name || getSpaceName(event.data.position) || "property";
        description = `⚖️ Auction started for ${auctionProp}`;
        break;
      }
      case "AUCTION_BID":
        description = `💰 Bid $${event.data.bid || event.data.amount} in auction`;
        break;
      case "AUCTION_WON":
        description = `🎉 Won auction for ${event.data.name || "property"} at $${event.data.bid || event.data.amount}`;
        break;
      case "PLAYER_BANKRUPT":
        description = `💀 Went BANKRUPT!`;
        break;
      case "GAME_OVER": {
        const winnerId = event.data.winner?.player_id ?? event.data.winner_id;
        const winnerName = winnerId !== undefined ? AGENT_NAMES[winnerId] : null;
        const netWorth = event.data.winner?.net_worth;
        if (event.data.reason === "max_turns_reached") {
          description = winnerName
            ? `🏆 GAME OVER! ${winnerName} wins by highest net worth ($${netWorth?.toLocaleString() || "?"}) after ${event.data.turns} turns`
            : `🏆 GAME OVER! Max turns reached - no winner`;
        } else if (event.data.reason === "error") {
          description = `🏆 GAME OVER! Game ended due to error`;
        } else {
          description = winnerName
            ? `🏆 GAME OVER! ${winnerName} wins! 🎉`
            : `🏆 GAME OVER!`;
        }
        break;
      }
      case "AGENT_SPOKE":
        description = `💬 "${event.data.message || event.data.speech}"`;
        break;
      case "AGENT_THOUGHT":
        description = `💭 Thinking: "${event.data.thought}"`;
        break;
      default:
        description = event.event_type.toLowerCase().replace(/_/g, " ");
    }

    return { playerName, playerColor, description };
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-300">
      {/* Header */}
      <div className="px-4 py-2 border-b border-gray-300 bg-gray-50">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-sm text-black">Game Log</h2>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="text-xs text-black font-medium hover:text-gray-700 flex items-center gap-1"
          >
            <Filter size={12} />
            Filter
          </button>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-2 flex flex-wrap gap-1">
            <button
              onClick={() => setFilter(null)}
              className={`text-xs px-2 py-1 rounded ${
                filter === null
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              All
            </button>
            {Object.keys(EVENT_CATEGORIES).map((category) => (
              <button
                key={category}
                onClick={() => setFilter(category)}
                className={`text-xs px-2 py-1 rounded capitalize ${
                  filter === category
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Events */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-2 space-y-1 text-xs"
      >
        {filteredEvents.length === 0 ? (
          <div className="text-center text-black font-medium mt-8">
            No events yet. Start a game to see the log.
          </div>
        ) : (
          filteredEvents.map((event, idx) => {
            const { playerName, playerColor, description } = formatEvent(event);
            return (
              <div
                key={idx}
                className="flex gap-2 hover:bg-gray-50 p-1 rounded"
              >
                <span className="text-gray-600 font-bold w-12 flex-shrink-0">
                  T{event.turn_number}
                </span>
                <span className={`font-black w-20 flex-shrink-0 ${playerColor}`}>
                  {playerName}
                </span>
                <span className={`flex-1 font-semibold ${playerColor}`}>{description}</span>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-300 bg-gray-50 text-xs text-black font-medium">
        {filteredEvents.length} event{filteredEvents.length !== 1 ? "s" : ""}
        {filter && ` (filtered: ${filter})`}
      </div>
    </div>
  );
}
