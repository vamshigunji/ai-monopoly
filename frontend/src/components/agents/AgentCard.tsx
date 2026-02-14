/**
 * Agent info card component
 * Displays agent name, personality, cash, properties, status
 */

"use client";

import type { Player } from "@/lib/types";

interface AgentCardProps {
  player: Player;
  isCurrentTurn: boolean;
}

const AGENT_INFO = [
  {
    name: "The Shark",
    personality: "Aggressive Negotiator",
    color: "bg-red-500",
    textColor: "text-red-500",
    borderColor: "border-red-500",
  },
  {
    name: "The Professor",
    personality: "Analytical Strategist",
    color: "bg-blue-500",
    textColor: "text-blue-500",
    borderColor: "border-blue-500",
  },
  {
    name: "The Hustler",
    personality: "Charismatic Bluffer",
    color: "bg-amber-500",
    textColor: "text-amber-500",
    borderColor: "border-amber-500",
  },
  {
    name: "The Turtle",
    personality: "Conservative Builder",
    color: "bg-green-500",
    textColor: "text-green-500",
    borderColor: "border-green-500",
  },
];

export function AgentCard({ player, isCurrentTurn }: AgentCardProps) {
  const agent = AGENT_INFO[player.id];

  if (!agent) return null;

  const totalHouses = Object.values(player.houses).reduce((sum, h) => sum + (h < 5 ? h : 0), 0);
  const totalHotels = Object.values(player.houses).filter((h) => h === 5).length;

  return (
    <div
      className={`
        rounded-lg border-2 p-3 transition-all
        ${isCurrentTurn ? `${agent.borderColor} shadow-md` : "border-gray-300"}
        ${player.is_bankrupt ? "opacity-50 grayscale" : ""}
        bg-white
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${agent.color}`} />
            <h3 className="font-bold text-sm text-black">{agent.name}</h3>
          </div>
          <p className="text-xs text-black font-medium">{agent.personality}</p>
        </div>
        {isCurrentTurn && (
          <div className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
            Turn
          </div>
        )}
        {player.is_bankrupt && (
          <div className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
            Bankrupt
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="space-y-1">
        {/* Cash */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-black font-medium">Cash:</span>
          <span className="font-bold text-sm text-black">
            ${player.cash.toLocaleString()}
          </span>
        </div>

        {/* Properties */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-black font-medium">Properties:</span>
          <span className="text-sm font-bold text-black">{player.properties.length}</span>
        </div>

        {/* Houses & Hotels */}
        {(totalHouses > 0 || totalHotels > 0) && (
          <div className="flex justify-between items-center">
            <span className="text-xs text-black font-medium">Buildings:</span>
            <span className="text-sm font-bold text-black">
              {totalHouses > 0 && <span>{totalHouses}🏠</span>}
              {totalHouses > 0 && totalHotels > 0 && " "}
              {totalHotels > 0 && <span>{totalHotels}🏨</span>}
            </span>
          </div>
        )}

        {/* Jail status */}
        {player.in_jail && (
          <div className="text-xs text-black font-bold bg-orange-100 px-2 py-1 rounded mt-1 border-2 border-orange-400">
            🔒 In Jail ({player.jail_turns} turns)
          </div>
        )}

        {/* Get Out of Jail cards */}
        {player.get_out_of_jail_cards > 0 && (
          <div className="text-xs text-black font-bold">
            🎫 {player.get_out_of_jail_cards} GOOJF card{player.get_out_of_jail_cards > 1 ? "s" : ""}
          </div>
        )}
      </div>
    </div>
  );
}
