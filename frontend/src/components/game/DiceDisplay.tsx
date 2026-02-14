/**
 * Dice roll display with animation
 * Shows current dice values
 */

"use client";

import { useEffect, useState } from "react";
import { useGameStore } from "@/stores/gameStore";

export function DiceDisplay() {
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

  if (!dice) {
    return null;
  }

  const renderDie = (value: number) => {
    const dots = [];

    // Dot positions for each die value
    const positions: Record<number, number[][]> = {
      1: [[1, 1]],
      2: [[0, 0], [2, 2]],
      3: [[0, 0], [1, 1], [2, 2]],
      4: [[0, 0], [0, 2], [2, 0], [2, 2]],
      5: [[0, 0], [0, 2], [1, 1], [2, 0], [2, 2]],
      6: [[0, 0], [0, 1], [0, 2], [2, 0], [2, 1], [2, 2]],
    };

    return (
      <div className="w-12 h-12 bg-white border-2 border-gray-800 rounded-lg p-1.5 grid grid-cols-3 grid-rows-3 gap-0.5">
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
    <div className="bg-white rounded-lg border border-gray-300 p-4">
      <div className="text-center">
        <div className="text-xs text-black mb-2 font-bold">Current Roll</div>
        <div className={`flex gap-3 justify-center ${rolling ? "animate-bounce" : ""}`}>
          {renderDie(dice.die1)}
          {renderDie(dice.die2)}
        </div>
        <div className="mt-2 text-sm font-bold text-black">
          Total: {dice.die1 + dice.die2}
          {dice.doubles && (
            <span className="ml-2 text-orange-600 text-xs font-black">DOUBLES!</span>
          )}
        </div>
      </div>
    </div>
  );
}
