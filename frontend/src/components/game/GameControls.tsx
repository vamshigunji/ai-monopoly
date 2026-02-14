/**
 * Game control buttons
 * Start, pause, resume, speed controls
 */

"use client";

import { useState } from "react";
import { Play, Pause, RotateCcw } from "lucide-react";
import { useGameStore } from "@/stores/gameStore";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function GameControls() {
  const [starting, setStarting] = useState(false);
  const [speed, setSpeed] = useState(1);
  const gameId = useGameStore((state) => state.gameId);
  const gameState = useGameStore((state) => state.gameState);
  const setGameId = useGameStore((state) => state.setGameId);
  const setGameState = useGameStore((state) => state.setGameState);
  const resetGame = useGameStore((state) => state.resetGame);

  const handleStartGame = async () => {
    setStarting(true);
    try {
      // Generate random seed between 1 and 1000000
      const randomSeed = Math.floor(Math.random() * 1000000) + 1;

      const response = await fetch(`${API_URL}/game/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed: randomSeed }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("API Error:", errorData);
        throw new Error(errorData.detail?.error || "Failed to start game");
      }

      const data = await response.json();
      setGameId(data.game_id);
      console.log("Game started:", data);
    } catch (error) {
      console.error("Failed to start game:", error);
      alert(`Failed to start game: ${error instanceof Error ? error.message : 'Unknown error'}\n\nMake sure the backend is running on port 8000.`);
    } finally {
      setStarting(false);
    }
  };

  const handlePauseResume = async () => {
    if (!gameId) return;

    const endpoint = gameState?.status === "paused" ? "resume" : "pause";
    try {
      const response = await fetch(`${API_URL}/game/${gameId}/${endpoint}`, {
        method: "POST",
      });

      if (!response.ok) {
        // 409 = game already in that state (already paused/finished)
        if (response.status === 409) {
          const errData = await response.json().catch(() => null);
          const detail = errData?.detail?.details?.status;
          if (detail && gameState) {
            setGameState({
              ...gameState,
              status: detail as "waiting" | "in_progress" | "paused" | "finished",
            });
          }
          return;
        }
        // 404 = game not found (probably finished and cleaned up)
        if (response.status === 404 && gameState) {
          setGameState({ ...gameState, status: "finished" });
          return;
        }
        console.warn(`Failed to ${endpoint} game: ${response.status}`);
        return;
      }

      const data = await response.json();
      console.log(`Game ${endpoint}d:`, data);

      // Update game state with new status
      if (gameState) {
        setGameState({
          ...gameState,
          status: data.status as "waiting" | "in_progress" | "paused" | "finished",
        });
      }
    } catch (error) {
      console.error(`Failed to ${endpoint} game:`, error);
    }
  };

  const handleSpeedChange = async (newSpeed: number) => {
    if (!gameId) return;

    setSpeed(newSpeed);
    try {
      const response = await fetch(`${API_URL}/game/${gameId}/speed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed: newSpeed }),
      });

      if (!response.ok) {
        throw new Error("Failed to change speed");
      }

      console.log("Speed changed to", newSpeed);
    } catch (error) {
      console.error("Failed to change speed:", error);
    }
  };

  const handleReset = () => {
    if (confirm("Reset the game? This will disconnect from the current game.")) {
      resetGame();
    }
  };

  const isPaused = gameState?.status === "paused";
  const isRunning = gameState?.status === "in_progress";
  const isFinished = gameState?.status === "finished";

  return (
    <div className="bg-white rounded-lg border border-gray-300 p-4">
      <h2 className="font-bold text-sm mb-3 text-black">Game Controls</h2>

      <div className="space-y-3">
        {/* Start/Pause/Resume buttons */}
        <div className="flex gap-2">
          {!gameId ? (
            <button
              onClick={handleStartGame}
              disabled={starting}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              <Play size={16} />
              {starting ? "Starting..." : "Start New Game"}
            </button>
          ) : isFinished ? (
            <button
              onClick={handleReset}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              <RotateCcw size={16} />
              New Game
            </button>
          ) : (
            <>
              <button
                onClick={handlePauseResume}
                className="flex-1 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded font-semibold flex items-center justify-center gap-2 transition-colors"
              >
                {isPaused ? (
                  <>
                    <Play size={16} />
                    Resume
                  </>
                ) : (
                  <>
                    <Pause size={16} />
                    Pause
                  </>
                )}
              </button>
              <button
                onClick={handleReset}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-semibold flex items-center justify-center gap-2 transition-colors"
              >
                <RotateCcw size={16} />
              </button>
            </>
          )}
        </div>

        {/* Speed control */}
        {gameId && !isFinished && (
          <div>
            <label className="block text-xs text-black font-medium mb-1">
              Game Speed: {speed}x
            </label>
            <input
              type="range"
              min="0.5"
              max="5"
              step="0.5"
              value={speed}
              onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-black font-medium mt-1">
              <span>0.5x</span>
              <span>5x</span>
            </div>
          </div>
        )}

        {/* Status indicator */}
        {gameId && (
          <div className="text-xs">
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isRunning
                    ? "bg-green-500 animate-pulse"
                    : isPaused
                    ? "bg-amber-500"
                    : isFinished
                    ? "bg-gray-500"
                    : "bg-red-500"
                }`}
              />
              <span className="text-black font-medium">
                Status: <span className="font-bold">{gameState?.status || "unknown"}</span>
              </span>
            </div>
            <div className="text-black font-medium mt-1">
              Game ID: <span className="font-mono text-xs font-bold">{gameId.slice(0, 8)}...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
