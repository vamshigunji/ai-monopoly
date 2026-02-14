/**
 * Main game page
 * Monopoly AI Agents - Watch 4 AI agents play Monopoly
 */

"use client";

import { useEffect } from "react";
import { useGameStore } from "@/stores/gameStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { GameBoard } from "@/components/board/GameBoard";
import { ConversationPanel } from "@/components/agents/ConversationPanel";
import { ThoughtPanel } from "@/components/agents/ThoughtPanel";
import { AssetPanel } from "@/components/agents/AssetPanel";
import { GameControls } from "@/components/game/GameControls";
import { GameLog } from "@/components/game/GameLog";
import { TrendGraph } from "@/components/game/TrendGraph";
import { PlayerLegend } from "@/components/game/PlayerLegend";
import { TokenUsageGraph } from "@/components/game/TokenUsageGraph";

export default function Home() {
  const gameId = useGameStore((state) => state.gameId);
  const gameState = useGameStore((state) => state.gameState);
  const { connected, error } = useWebSocket(gameId);

  // Poll for game state periodically
  useEffect(() => {
    if (!gameId) return;

    const fetchGameState = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/game/${gameId}/state`
        );
        if (response.ok) {
          const data = await response.json();
          useGameStore.getState().setGameState(data);
        }
      } catch (error) {
        console.error("Failed to fetch game state:", error);
      }
    };

    // Initial fetch
    fetchGameState();

    // Poll every 2 seconds
    const interval = setInterval(fetchGameState, 2000);

    return () => clearInterval(interval);
  }, [gameId]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      {/* Header - compact */}
      <div className="max-w-[1800px] mx-auto mb-3">
        <div className="bg-white/95 backdrop-blur-sm rounded-lg px-4 py-2 border-2 border-gray-800 shadow-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-black">🎲 Monopoly AI Agents</h1>
            <p className="text-xs text-gray-600 font-medium hidden sm:block">
              4 AI agents with different personalities
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-medium">
            <div className="flex items-center gap-1.5">
              <div
                className={`w-2 h-2 rounded-full ${
                  connected ? "bg-green-500 animate-pulse" : "bg-red-500"
                }`}
              />
              <span className="text-black font-bold">{connected ? "Connected" : "Disconnected"}</span>
            </div>
            {error && (
              <div className="text-red-600 font-bold">Error: {error}</div>
            )}
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className="max-w-[1800px] mx-auto space-y-4">
        {/* Top Section: Board + Right Panels */}
        <div className="grid grid-cols-12 gap-4">
          {/* Left Column - Board + Controls */}
          <div className="col-span-7 space-y-4">
            {/* Game Board */}
            <div className="aspect-square">
              <GameBoard />
            </div>

            {/* Controls Row */}
            <div>
              <GameControls />
            </div>
          </div>

          {/* Right Column - Players + Chat + Thoughts + Assets */}
          <div className="col-span-5 space-y-4">
            {/* Player Legend with full stats */}
            <div>
              <PlayerLegend />
            </div>

            {/* Conversation Panel */}
            <div className="h-72">
              <ConversationPanel />
            </div>

            {/* Split View: Thoughts + Assets */}
            <div className="grid grid-cols-2 gap-4 h-[480px]">
              {/* Private Thoughts Panel */}
              <div className="min-h-0 overflow-hidden">
                <ThoughtPanel />
              </div>

              {/* Asset Panel */}
              <div className="min-h-0 overflow-hidden">
                <AssetPanel />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row: Net Worth + Game Log + Token Usage - equal height, full width */}
        <div className="grid grid-cols-3 gap-4">
          <div className="h-80">
            <TrendGraph />
          </div>
          <div className="h-80">
            <GameLog />
          </div>
          <div className="h-80">
            <TokenUsageGraph />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-[1800px] mx-auto mt-4 text-center text-xs text-white font-medium">
        <p>
          Built with Next.js + FastAPI + OpenAI GPT-4o + Google Gemini |{" "}
          <a
            href="https://github.com/anthropics/claude-code"
            className="text-blue-300 hover:text-blue-200 underline"
          >
            GitHub
          </a>
        </p>
      </div>
    </div>
  );
}
