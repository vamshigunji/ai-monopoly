/**
 * Monopoly game board component
 * CSS Grid-based layout with all 40 spaces
 */

"use client";

import { useEffect, useState } from "react";
import { useGameStore } from "@/stores/gameStore";
import { BoardSpace } from "./BoardSpace";
import { BOARD_SPACES } from "@/lib/boardData";

export function GameBoard() {
  const gameState = useGameStore((state) => state.gameState);
  const events = useGameStore((state) => state.events);
  const [dice, setDice] = useState<{ die1: number; die2: number; doubles: boolean } | null>(null);
  const [rolling, setRolling] = useState(false);

  // Watch for dice roll events
  useEffect(() => {
    const lastEvent = events[events.length - 1];
    if (lastEvent?.event_type === "DICE_ROLLED") {
      setRolling(true);

      // Simulate rolling animation
      const rollDuration = 500;
      const rollInterval = setInterval(() => {
        setDice({
          die1: Math.floor(Math.random() * 6) + 1,
          die2: Math.floor(Math.random() * 6) + 1,
          doubles: false,
        });
      }, 50);

      setTimeout(() => {
        clearInterval(rollInterval);
        setDice({
          die1: lastEvent.data.die1,
          die2: lastEvent.data.die2,
          doubles: lastEvent.data.doubles,
        });
        setRolling(false);
      }, rollDuration);

      return () => clearInterval(rollInterval);
    }
  }, [events]);

  // Group players by position
  const playersByPosition: { [pos: number]: number[] } = {};
  gameState?.players.forEach((player) => {
    if (!player.is_bankrupt) {
      if (!playersByPosition[player.position]) {
        playersByPosition[player.position] = [];
      }
      playersByPosition[player.position].push(player.id);
    }
  });

  // Map property owners
  const propertyOwners: { [pos: number]: number } = {};
  gameState?.players.forEach((player) => {
    player.properties.forEach((propPos) => {
      propertyOwners[propPos] = player.id;
    });
  });

  // Render a single die
  const renderDie = (value: number) => {
    const positions: Record<number, number[][]> = {
      1: [[1, 1]],
      2: [[0, 0], [2, 2]],
      3: [[0, 0], [1, 1], [2, 2]],
      4: [[0, 0], [0, 2], [2, 0], [2, 2]],
      5: [[0, 0], [0, 2], [1, 1], [2, 0], [2, 2]],
      6: [[0, 0], [0, 1], [0, 2], [2, 0], [2, 1], [2, 2]],
    };

    return (
      <div className="w-16 h-16 bg-white border-3 border-gray-900 rounded-lg p-2 grid grid-cols-3 grid-rows-3 gap-1 shadow-xl">
        {Array.from({ length: 9 }).map((_, idx) => {
          const row = Math.floor(idx / 3);
          const col = idx % 3;
          const hasDot = positions[value]?.some(([r, c]) => r === row && c === col);

          return (
            <div
              key={idx}
              className={`rounded-full ${
                hasDot ? "bg-gray-900" : "bg-transparent"
              }`}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="w-full aspect-square bg-gradient-to-br from-green-100 to-green-200 p-3 rounded-lg shadow-2xl">
      <div className="grid grid-cols-11 grid-rows-11 gap-0 h-full w-full">
        {/* Bottom row (positions 0-10) */}
        {BOARD_SPACES.slice(0, 11).map((space, idx) => (
          <div
            key={space.position}
            style={{
              gridColumn: idx === 0 ? 11 : 11 - idx,
              gridRow: 11
            }}
          >
            <BoardSpace
              space={space as any}
              players={playersByPosition[space.position] || []}
              owner={propertyOwners[space.position] ?? null}
              houses={gameState?.players[propertyOwners[space.position]]?.houses[space.position] || 0}
            />
          </div>
        ))}

        {/* Left side (positions 11-19) */}
        {BOARD_SPACES.slice(11, 20).map((space, idx) => (
          <div
            key={space.position}
            style={{
              gridColumn: 1,
              gridRow: 10 - idx
            }}
          >
            <BoardSpace
              space={space as any}
              players={playersByPosition[space.position] || []}
              owner={propertyOwners[space.position] ?? null}
              houses={gameState?.players[propertyOwners[space.position]]?.houses[space.position] || 0}
            />
          </div>
        ))}

        {/* Top row (positions 20-30) */}
        {BOARD_SPACES.slice(20, 31).map((space, idx) => (
          <div
            key={space.position}
            style={{
              gridColumn: idx + 1,
              gridRow: 1
            }}
          >
            <BoardSpace
              space={space as any}
              players={playersByPosition[space.position] || []}
              owner={propertyOwners[space.position] ?? null}
              houses={gameState?.players[propertyOwners[space.position]]?.houses[space.position] || 0}
            />
          </div>
        ))}

        {/* Right side (positions 31-39) */}
        {BOARD_SPACES.slice(31, 40).map((space, idx) => (
          <div
            key={space.position}
            style={{
              gridColumn: 11,
              gridRow: idx + 2
            }}
          >
            <BoardSpace
              space={space as any}
              players={playersByPosition[space.position] || []}
              owner={propertyOwners[space.position] ?? null}
              houses={gameState?.players[propertyOwners[space.position]]?.houses[space.position] || 0}
            />
          </div>
        ))}

        {/* Center area - Game title and dice */}
        <div
          style={{
            gridColumn: '2 / 11',
            gridRow: '2 / 11'
          }}
          className="flex flex-col items-center justify-center bg-gradient-to-br from-white/90 to-green-50/90 backdrop-blur-sm rounded-xl border-4 border-gray-900 shadow-inner"
        >
          <div className="text-center p-6">
            <h1 className="text-5xl font-black text-gray-900 mb-2 tracking-tight">MONOPOLY</h1>
            <p className="text-2xl text-gray-700 font-semibold">AI Agents</p>
            {gameState && (
              <div className="mt-4 text-base font-medium text-gray-800">
                <p className="mb-1">Turn: <span className="font-bold">{gameState.turn_number}</span></p>
                <p className="capitalize">Status: <span className="font-bold">{gameState.status}</span></p>
              </div>
            )}

            {/* Dice Display */}
            {dice && (
              <div className="mt-6">
                <div className="text-sm text-gray-900 mb-3 font-bold">Current Roll</div>
                <div className={`flex gap-4 justify-center ${rolling ? "animate-bounce" : ""}`}>
                  {renderDie(dice.die1)}
                  {renderDie(dice.die2)}
                </div>
                <div className="mt-3 text-lg font-black text-gray-900">
                  Total: {dice.die1 + dice.die2}
                  {dice.doubles && (
                    <span className="ml-2 text-orange-600 text-base font-black">🎊 DOUBLES!</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
