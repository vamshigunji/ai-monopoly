/**
 * Private thoughts panel
 * Shows selected agent's internal reasoning
 */

"use client";

import { useEffect, useRef } from "react";
import { useGameStore } from "@/stores/gameStore";

const AGENT_INFO = [
  { name: "The Shark", emoji: "🦈", color: "text-red-600", bgColor: "bg-red-50", personality: "Aggressive Negotiator" },
  { name: "The Professor", emoji: "🎓", color: "text-blue-600", bgColor: "bg-blue-50", personality: "Analytical Strategist" },
  { name: "The Hustler", emoji: "🎭", color: "text-amber-600", bgColor: "bg-amber-50", personality: "Charismatic Bluffer" },
  { name: "The Turtle", emoji: "🐢", color: "text-green-600", bgColor: "bg-green-50", personality: "Conservative Builder" },
];

export function ThoughtPanel() {
  const selectedThoughtAgent = useGameStore((state) => state.selectedThoughtAgent);
  const setSelectedThoughtAgent = useGameStore((state) => state.setSelectedThoughtAgent);
  const privateThoughts = useGameStore((state) => state.privateThoughts);
  const gameState = useGameStore((state) => state.gameState);
  const scrollRef = useRef<HTMLDivElement>(null);

  const thoughts = privateThoughts[selectedThoughtAgent] || [];
  const agent = AGENT_INFO[selectedThoughtAgent];
  const player = gameState?.players?.[selectedThoughtAgent];

  // Auto-scroll to bottom when new thoughts arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [thoughts]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-300">
      {/* Header with agent selector dropdown */}
      <div className="px-4 py-2 border-b border-gray-300 bg-gray-50">
        <h2 className="font-bold text-sm mb-2 text-black">Private Thoughts</h2>
        <select
          value={selectedThoughtAgent}
          onChange={(e) => setSelectedThoughtAgent(Number(e.target.value))}
          className="w-full px-3 py-2 text-sm font-medium text-black bg-white border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
        >
          {AGENT_INFO.map((a, idx) => (
            <option key={idx} value={idx}>
              {a.emoji} {a.name}
            </option>
          ))}
        </select>
        {player && (
          <div className="mt-2 text-xs text-gray-600 font-medium">
            {agent.personality} · ${player.cash} · {player.properties.length} properties
          </div>
        )}
      </div>

      {/* Thoughts */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {thoughts.length === 0 ? (
          <div className="text-center text-black text-sm mt-8 font-medium">
            <span className="text-3xl block mb-2">{agent.emoji}</span>
            No thoughts from {agent.name} yet
            <div className="text-xs text-gray-600 mt-2">
              Strategic reasoning will appear here
            </div>
          </div>
        ) : (
          thoughts.map((thought, idx) => {
            const time = new Date(thought.timestamp).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });

            // Extract turn number from timestamp or use index
            const thoughtText = thought.message || "...";

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg ${agent.bgColor} border-l-4 ${agent.color.replace("text", "border")}`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-2xl flex-shrink-0">{agent.emoji}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <div className={`text-xs font-black ${agent.color}`}>
                        {agent.name}
                      </div>
                      <div className="text-xs text-gray-500 font-medium">{time}</div>
                    </div>
                    <div className="text-sm text-black font-medium italic leading-relaxed">
                      💭 "{thoughtText}"
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-300 bg-gray-50 text-xs text-black font-medium">
        {thoughts.length} thought{thoughts.length !== 1 ? "s" : ""} from {agent.name}
      </div>
    </div>
  );
}
