/**
 * Individual Monopoly board space component
 */

import type { Space } from "@/lib/types";

interface BoardSpaceProps {
  space: Space;
  players: number[]; // Player IDs on this space
  owner: number | null; // Player ID who owns this property
  houses: number; // Number of houses (0-5, 5=hotel)
}

const COLOR_MAP: Record<string, string> = {
  BROWN: "bg-amber-900",
  LIGHT_BLUE: "bg-sky-300",
  PINK: "bg-pink-400",
  ORANGE: "bg-orange-500",
  RED: "bg-red-600",
  YELLOW: "bg-yellow-400",
  GREEN: "bg-green-600",
  DARK_BLUE: "bg-blue-800",
};

const PLAYER_COLORS = ["bg-red-500", "bg-blue-500", "bg-amber-500", "bg-green-500"];

export function BoardSpace({ space, players, owner, houses }: BoardSpaceProps) {
  const isProperty = space.space_type === "PROPERTY";
  const isCorner = ["GO", "JAIL", "FREE_PARKING", "GO_TO_JAIL"].includes(
    space.space_type
  );

  return (
    <div
      className={`
        relative border-2 border-gray-900 bg-white flex flex-col justify-between p-1.5
        ${isCorner ? "text-xs font-bold" : "text-[11px]"}
        ${isProperty && space.color_group ? "pt-4" : ""}
        h-full
      `}
    >
      {/* Property color bar */}
      {isProperty && space.color_group && (
        <div
          className={`absolute top-0 left-0 right-0 h-3 ${
            COLOR_MAP[space.color_group] || "bg-gray-400"
          }`}
        />
      )}

      {/* Space name */}
      <div className="font-bold truncate text-gray-900 leading-tight" title={space.name}>
        {space.name}
      </div>

      {/* Price */}
      {space.price && (
        <div className="text-[10px] font-semibold text-gray-800 mt-0.5">${space.price}</div>
      )}

      {/* Owner indicator */}
      {owner !== null && (
        <div
          className={`absolute top-0 right-0 w-2 h-2 ${PLAYER_COLORS[owner]}`}
          title={`Owned by Player ${owner}`}
        />
      )}

      {/* Houses/Hotel */}
      {houses > 0 && (
        <div className="absolute bottom-0 right-0 flex gap-px">
          {houses === 5 ? (
            <div className="w-3 h-3 bg-red-600 text-white text-[8px] flex items-center justify-center font-bold">
              H
            </div>
          ) : (
            Array.from({ length: houses }).map((_, i) => (
              <div key={i} className="w-1.5 h-1.5 bg-green-600" />
            ))
          )}
        </div>
      )}

      {/* Player tokens on this space */}
      {players.length > 0 && (
        <div className="absolute bottom-1 left-1 flex gap-1 flex-wrap max-w-full z-10">
          {players.map((playerId) => (
            <div
              key={playerId}
              className={`w-6 h-6 rounded-full border-2 border-white shadow-2xl ${PLAYER_COLORS[playerId]} flex items-center justify-center text-white font-black text-xs`}
              title={`Player ${playerId + 1}`}
            >
              {playerId + 1}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
