/**
 * Asset panel showing detailed property info for selected player
 * Shows what each player owns, property values, rents, etc.
 */

"use client";

import { useState } from "react";
import { useGameStore } from "@/stores/gameStore";
import { BOARD_SPACES } from "@/lib/boardData";

const AGENT_INFO = [
  { name: "The Shark", emoji: "🦈", color: "text-red-600", bgColor: "bg-red-50", borderColor: "border-red-500" },
  { name: "The Professor", emoji: "🎓", color: "text-blue-600", bgColor: "bg-blue-50", borderColor: "border-blue-500" },
  { name: "The Hustler", emoji: "🎭", color: "text-amber-600", bgColor: "bg-amber-50", borderColor: "border-amber-500" },
  { name: "The Turtle", emoji: "🐢", color: "text-green-600", bgColor: "bg-green-50", borderColor: "border-green-500" },
];

// Get actual rent from property data based on development level
const getRent = (space: any, houses: number, ownedRailroads: number = 1): number => {
  if (space.space_type === "PROPERTY" && space.rent) {
    // Rent array: [base, 1H, 2H, 3H, 4H, hotel]
    return space.rent[Math.min(houses, 5)] || 0;
  }
  if (space.space_type === "RAILROAD" && space.rent) {
    // Railroad rent based on number owned: [1RR, 2RR, 3RR, 4RR]
    return space.rent[Math.min(ownedRailroads - 1, 3)] || 0;
  }
  if (space.space_type === "UTILITY") {
    // Utilities use multiplier × dice roll (showing base multiplier for display)
    return ownedRailroads === 1 ? 4 : 10;
  }
  return 0;
};

export function AssetPanel() {
  const selectedAssetAgent = useGameStore((state) => state.selectedAssetAgent);
  const setSelectedAssetAgent = useGameStore((state) => state.setSelectedAssetAgent);
  const gameState = useGameStore((state) => state.gameState);
  const [expandedProperties, setExpandedProperties] = useState<Set<number>>(new Set());

  const player = gameState?.players[selectedAssetAgent];
  const agent = AGENT_INFO[selectedAssetAgent];

  const toggleProperty = (position: number) => {
    const newExpanded = new Set(expandedProperties);
    if (newExpanded.has(position)) {
      newExpanded.delete(position);
    } else {
      newExpanded.add(position);
    }
    setExpandedProperties(newExpanded);
  };

  if (!player || !agent) return null;

  // Calculate how many railroads player owns (for railroad rent calculation)
  const ownedRailroads = player.properties.filter(pos => {
    const space = BOARD_SPACES[pos];
    return space.space_type === "RAILROAD";
  }).length;

  // Calculate how many utilities player owns (for utility rent calculation)
  const ownedUtilities = player.properties.filter(pos => {
    const space = BOARD_SPACES[pos];
    return space.space_type === "UTILITY";
  }).length;

  // Get property details
  const properties = player.properties.map((pos) => {
    const space = BOARD_SPACES[pos];
    const houses = player.houses[pos] || 0;
    const isMortgaged = player.mortgaged?.includes(pos) || false;

    // Determine count for rent calculation
    let countForRent = 1;
    if (space.space_type === "RAILROAD") countForRent = ownedRailroads;
    if (space.space_type === "UTILITY") countForRent = ownedUtilities;

    return {
      position: pos,
      name: space.name,
      type: space.space_type,
      colorGroup: (space as any).color_group,
      price: (space as any).price || 0,
      mortgageValue: (space as any).mortgage || Math.floor(((space as any).price || 0) / 2),
      rentSchedule: (space as any).rent || [],
      houseCost: (space as any).house_cost || 0,
      houses,
      rent: getRent(space, houses, countForRent),
      mortgaged: isMortgaged,
    };
  });

  // Calculate totals
  const totalValue = properties.reduce((sum, p) => sum + p.price, 0);
  const totalRentIncome = properties.reduce((sum, p) => sum + p.rent, 0);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-300">
      {/* Header with agent selector dropdown */}
      <div className="px-4 py-2 border-b border-gray-300 bg-gray-50">
        <h2 className="font-bold text-sm mb-2 text-black">Asset Details</h2>
        <select
          value={selectedAssetAgent}
          onChange={(e) => setSelectedAssetAgent(Number(e.target.value))}
          className="w-full px-3 py-2 text-sm font-medium text-black bg-white border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        >
          {AGENT_INFO.map((a, idx) => (
            <option key={idx} value={idx}>
              {a.emoji} {a.name}
            </option>
          ))}
        </select>
      </div>

      {/* Asset summary */}
      <div className={`px-4 py-3 ${agent.bgColor} border-b border-gray-300`}>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-xs text-black font-medium">Cash</div>
            <div className="text-lg font-black text-black">${player.cash.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-black font-medium">Properties</div>
            <div className="text-lg font-black text-black">{properties.length}</div>
          </div>
          <div>
            <div className="text-xs text-black font-medium">Property Value</div>
            <div className="text-base font-bold text-black">${totalValue.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-black font-medium">Total Worth</div>
            <div className="text-base font-bold text-black">${(player.cash + totalValue).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Properties list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {properties.length === 0 ? (
          <div className="text-center text-black text-sm mt-8 font-medium">
            <span className="text-3xl block mb-2">{agent.emoji}</span>
            No properties owned yet
          </div>
        ) : (
          properties.map((prop) => {
            const isExpanded = expandedProperties.has(prop.position);

            return (
              <div
                key={prop.position}
                className={`p-3 rounded-lg border-l-4 cursor-pointer transition-all duration-300 ${
                  prop.colorGroup ? `border-${prop.colorGroup.toLowerCase()}-500` : "border-gray-500"
                } ${prop.mortgaged ? "bg-gray-200" : "bg-white"} shadow-sm hover:shadow-md`}
                onClick={() => toggleProperty(prop.position)}
              >
                {/* Header: Name & Price with Expand Indicator */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="font-black text-sm text-black">{prop.name}</div>
                      <span className={`text-xs transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                      </span>
                    </div>
                    {prop.colorGroup && (
                      <div className="text-xs text-gray-600 font-medium mt-0.5">
                        {prop.colorGroup} · Position {prop.position}
                      </div>
                    )}
                  </div>
                  <div className="text-sm font-black text-black">${prop.price}</div>
                </div>

                {/* Mortgage Status */}
                {prop.mortgaged && (
                  <div className="mb-2 text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded">
                    🔒 MORTGAGED (Value: ${prop.mortgageValue})
                  </div>
                )}

                {/* Current Status: Houses/Rent - Always Visible */}
                <div className="mb-2 text-xs bg-gray-50 p-2 rounded">
                  <div className="flex items-center justify-between">
                    <div className="text-black font-bold">
                      {prop.type === "RAILROAD" ? `🚂 Railroad (${ownedRailroads} owned)` :
                       prop.type === "UTILITY" ? `⚡ Utility (${ownedUtilities} owned)` :
                       prop.houses === 5 ? "🏨 Hotel" :
                       prop.houses > 0 ? `🏠 ${prop.houses} House${prop.houses > 1 ? "s" : ""}` :
                       "No houses"}
                    </div>
                    <div className="font-black text-green-600">
                      {prop.type === "UTILITY" ?
                        `Rent: ${prop.rent}× dice` :
                        `Current Rent: $${prop.rent}`
                      }
                    </div>
                  </div>
                </div>

                {/* Expandable Details Section */}
                <div
                  className={`overflow-hidden transition-all duration-300 ${
                    isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  {/* Rent Schedule (if available) */}
                  {prop.rentSchedule && prop.rentSchedule.length > 0 && (
                    <div className="text-xs space-y-1 mb-2">
                      <div className="font-bold text-black mb-1">
                        {prop.type === "RAILROAD" ? "Railroad Rent:" :
                         prop.type === "UTILITY" ? "Utility Rent:" : "Rent Schedule:"}
                      </div>
                      {prop.type === "RAILROAD" ? (
                        // Railroad rent display
                        <div className="grid grid-cols-2 gap-1 text-black">
                          {prop.rentSchedule.map((rent: number, idx: number) => (
                            <div
                              key={idx}
                              className={`px-1.5 py-0.5 rounded ${
                                idx + 1 === ownedRailroads ? "bg-green-100 font-bold" : "bg-gray-100"
                              }`}
                            >
                              {idx + 1} RR{idx + 1 > 1 ? 's' : ''}: ${rent}
                            </div>
                          ))}
                        </div>
                      ) : prop.type === "UTILITY" ? (
                        // Utility display
                        <div className="text-xs bg-gray-100 p-2 rounded text-black">
                          <div className={ownedUtilities === 1 ? "font-bold" : ""}>1 Utility: 4× dice roll</div>
                          <div className={ownedUtilities === 2 ? "font-bold" : ""}>2 Utilities: 10× dice roll</div>
                        </div>
                      ) : (
                        // Property rent schedule
                        <div className="grid grid-cols-3 gap-1 text-black">
                          {prop.rentSchedule.map((rent: number, idx: number) => (
                            <div
                              key={idx}
                              className={`px-1.5 py-0.5 rounded ${
                                idx === prop.houses ? "bg-green-100 font-bold" : "bg-gray-100"
                              }`}
                            >
                              {idx === 0 ? "Base" : idx === 5 ? "Hotel" : `${idx}H`}: ${rent}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Property Details */}
                  <div className="text-xs text-gray-700 space-y-1 border-t border-gray-200 pt-2">
                    {prop.houseCost > 0 && (
                      <div className="flex justify-between">
                        <span className="font-medium">House Cost:</span>
                        <span className="font-bold">${prop.houseCost}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="font-medium">Mortgage Value:</span>
                      <span className="font-bold">${prop.mortgageValue}</span>
                    </div>
                  </div>
                </div>

                {/* Click to expand hint (only when collapsed) */}
                {!isExpanded && (
                  <div className="text-xs text-gray-500 text-center mt-2 font-medium">
                    Click to see details
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-300 bg-gray-50 text-xs text-black font-medium">
        {properties.length} propert{properties.length !== 1 ? "ies" : "y"} · Total value: ${totalValue.toLocaleString()}
      </div>
    </div>
  );
}
