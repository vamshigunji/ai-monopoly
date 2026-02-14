/**
 * Public conversation panel
 * Shows agent-to-agent negotiations and table talk
 */

"use client";

import { useEffect, useRef } from "react";
import { useGameStore } from "@/stores/gameStore";

const AGENT_NAMES = ["Shark", "Professor", "Hustler", "Turtle"];
const AGENT_EMOJIS = ["🦈", "🎓", "🎭", "🐢"];
const AGENT_COLORS = ["text-red-600", "text-blue-600", "text-amber-600", "text-green-600"];
const AGENT_BG_COLORS = ["bg-red-50", "bg-blue-50", "bg-amber-50", "bg-green-50"];

export function ConversationPanel() {
  const publicChat = useGameStore((state) => state.publicChat);
  const gameState = useGameStore((state) => state.gameState);
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
  }, [publicChat]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-300">
      {/* Header */}
      <div className="px-4 py-2 border-b border-gray-300 bg-gray-50">
        <h2 className="font-bold text-sm text-black">Public Negotiations</h2>
        <p className="text-xs text-black font-medium">Agent conversations visible to all</p>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {publicChat.length === 0 ? (
          <div className="text-center text-black text-sm mt-8 font-medium">
            💬 No public conversations yet
            <div className="text-xs text-gray-600 mt-2">
              Agents will negotiate trades and talk trash here
            </div>
          </div>
        ) : (
          publicChat.map((msg, idx) => {
            // Handle undefined or invalid player_id
            const playerId = msg.player_id ?? -1;
            const isValidPlayer = playerId >= 0 && playerId < 4;

            const agentName = isValidPlayer ? AGENT_NAMES[playerId] : "Unknown";
            const agentEmoji = isValidPlayer ? AGENT_EMOJIS[playerId] : "❓";
            const agentColor = isValidPlayer ? AGENT_COLORS[playerId] : "text-gray-600";
            const agentBg = isValidPlayer ? AGENT_BG_COLORS[playerId] : "bg-gray-50";

            const time = new Date(msg.timestamp).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });

            // Get player's current cash and properties for context
            const player = isValidPlayer && gameState?.players?.[playerId];
            const cash = player ? `$${player.cash}` : "";
            const propCount = player ? player.properties.length : 0;

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg border-l-4 ${agentBg} ${agentColor.replace('text', 'border')}`}
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{agentEmoji}</span>
                    <div>
                      <div className={`font-black text-sm ${agentColor}`}>
                        {agentName}
                      </div>
                      {player && (
                        <div className="text-xs text-gray-600 font-medium">
                          {cash} · {propCount} properties
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 font-medium">{time}</div>
                </div>
                <div className="text-sm text-black font-medium pl-10">
                  "{msg.message}"
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-300 bg-gray-50 text-xs text-black font-medium">
        {publicChat.length} message{publicChat.length !== 1 ? "s" : ""}
      </div>
    </div>
  );
}
