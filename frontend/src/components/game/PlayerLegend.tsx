/**
 * PlayerLegend - Complete player dashboard with stats, model, and status
 */

"use client";

import { useGameStore } from "@/stores/gameStore";

const AGENT_INFO = [
  {
    name: "The Shark",
    emoji: "🦈",
    personality: "Aggressive Negotiator",
    traits: "High risk · Ruthless trader · Buys everything · Intimidates opponents",
  },
  {
    name: "The Professor",
    emoji: "🎓",
    personality: "Analytical Strategist",
    traits: "Calculated risk · Methodical builder · Data-driven · Quotes probabilities",
  },
  {
    name: "The Hustler",
    emoji: "🎭",
    personality: "Charismatic Bluffer",
    traits: "High risk · Unpredictable · Charm & persuasion · Lopsided deals",
  },
  {
    name: "The Turtle",
    emoji: "🐢",
    personality: "Conservative Builder",
    traits: "Low risk · Patient builder · Hoards cash · Avoids risky trades",
  },
];

export function PlayerLegend() {
  const gameState = useGameStore((state) => state.gameState);

  if (!gameState?.players) {
    return (
      <div className="bg-white border-2 border-gray-800 rounded-lg p-4 shadow-lg">
        <h3 className="text-sm font-bold mb-2 text-black">Players</h3>
        <p className="text-gray-500 text-sm font-medium">No game data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-gray-800 rounded-lg p-3 shadow-lg">
      <h3 className="text-sm font-bold mb-2 text-black">Players</h3>
      <div className="grid grid-cols-4 gap-2">
        {gameState.players.map((player) => {
          const agent = AGENT_INFO[player.id];
          const isCurrentTurn = player.id === gameState.current_player_index;
          const totalHouses = Object.values(player.houses).reduce(
            (sum, h) => sum + (h < 5 ? h : 0),
            0
          );
          const totalHotels = Object.values(player.houses).filter(
            (h) => h === 5
          ).length;

          return (
            <div
              key={player.id}
              className={`p-2 rounded-lg border-2 transition-all ${
                player.is_bankrupt ? "opacity-50 grayscale" : ""
              }`}
              style={{
                borderColor: isCurrentTurn ? player.color : "#e5e7eb",
                backgroundColor: isCurrentTurn
                  ? `${player.color}15`
                  : `${player.color}08`,
              }}
            >
              {/* Name row */}
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="text-lg">{agent.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div
                    className="font-black text-xs truncate"
                    style={{ color: player.color }}
                  >
                    {agent.name}
                  </div>
                  <div className="text-[10px] text-gray-500 font-medium truncate">
                    {agent.personality}
                  </div>
                </div>
                {isCurrentTurn && (
                  <span className="text-[9px] font-bold bg-green-100 text-green-700 px-1 py-0.5 rounded shrink-0">
                    TURN
                  </span>
                )}
                {player.is_bankrupt && (
                  <span className="text-[9px] font-bold bg-red-100 text-red-700 px-1 py-0.5 rounded shrink-0">
                    OUT
                  </span>
                )}
              </div>

              {/* Stats grid */}
              <div className="space-y-0.5 text-[11px] border-t border-gray-200 pt-1.5">
                <div className="flex justify-between">
                  <span className="text-gray-600 font-medium">Net Worth</span>
                  <span className="font-black text-black">
                    ${(player.net_worth ?? player.cash).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 font-medium">Cash</span>
                  <span className="font-bold text-black">
                    ${player.cash.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 font-medium">Props</span>
                  <span className="font-bold text-black">
                    {player.properties.length}
                  </span>
                </div>
                {(totalHouses > 0 || totalHotels > 0) && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 font-medium">Bldgs</span>
                    <span className="font-bold text-black">
                      {totalHouses > 0 && `${totalHouses}🏠`}
                      {totalHouses > 0 && totalHotels > 0 && " "}
                      {totalHotels > 0 && `${totalHotels}🏨`}
                    </span>
                  </div>
                )}
                {player.in_jail && (
                  <div className="text-[10px] font-bold text-orange-700 bg-orange-50 px-1 py-0.5 rounded text-center">
                    🔒 Jail ({player.jail_turns})
                  </div>
                )}
                {player.get_out_of_jail_cards > 0 && (
                  <div className="text-[10px] font-bold text-black">
                    🎫 {player.get_out_of_jail_cards} GOOJF
                  </div>
                )}
              </div>

              {/* Persona traits */}
              <div className="text-[10px] text-gray-500 font-medium mt-1.5 pt-1 border-t border-gray-200 leading-relaxed">
                {agent.traits}
              </div>

              {/* Model */}
              <div className="text-[10px] text-gray-500 font-semibold mt-1 truncate">
                🤖 {player.model || "Unknown"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
