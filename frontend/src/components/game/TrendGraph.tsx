/**
 * TrendGraph - Line chart showing player net worth over time
 * Tracks net worth (cash + property values) for all 4 players across turns
 */

"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useGameStore } from "@/stores/gameStore";

export function TrendGraph() {
  const netWorthHistory = useGameStore((state) => state.netWorthHistory);
  const gameState = useGameStore((state) => state.gameState);

  if (!gameState?.players) {
    return (
      <div className="bg-white border-2 border-gray-800 rounded-lg p-4 shadow-lg h-[300px] flex items-center justify-center">
        <p className="text-gray-500 font-medium">No game data available</p>
      </div>
    );
  }

  // Convert history object to array for Recharts
  const chartData = Object.entries(netWorthHistory)
    .map(([turn, playerNetWorths]) => ({
      turn: parseInt(turn),
      ...playerNetWorths,
    }))
    .sort((a, b) => a.turn - b.turn);

  // Get player colors mapping
  const playerColors = gameState.players.reduce(
    (acc, player) => {
      acc[player.id] = player.color;
      return acc;
    },
    {} as Record<number, string>
  );

  // Agent names mapping
  const AGENT_NAMES = ["The Shark", "The Professor", "The Hustler", "The Turtle"];

  // Get player names mapping (use actual agent names)
  const playerNames = gameState.players.reduce(
    (acc, player) => {
      acc[player.id] = AGENT_NAMES[player.id] || player.name;
      return acc;
    },
    {} as Record<number, string>
  );

  if (chartData.length === 0) {
    return (
      <div className="bg-white border-2 border-gray-800 rounded-lg p-4 shadow-lg h-[300px] flex items-center justify-center">
        <p className="text-gray-500 font-medium">Waiting for game data...</p>
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-gray-800 rounded-lg p-4 shadow-lg h-[300px]">
      <h3 className="text-lg font-bold mb-2 text-black">Net Worth Trends</h3>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="turn"
            label={{ value: "Turn", position: "insideBottom", offset: -5 }}
            stroke="#374151"
            style={{ fontSize: "12px", fontWeight: 600 }}
          />
          <YAxis
            label={{ value: "Net Worth ($)", angle: -90, position: "insideLeft" }}
            stroke="#374151"
            style={{ fontSize: "12px", fontWeight: 600 }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "white",
              border: "2px solid #1f2937",
              borderRadius: "0.5rem",
              fontWeight: 600,
            }}
            formatter={(value: number | undefined, name: string | undefined) => [
              `$${value ?? 0}`,
              playerNames[parseInt(name ?? "0")] || `Player ${name ?? "Unknown"}`,
            ]}
            labelFormatter={(turn) => `Turn ${turn}`}
          />
          <Legend
            formatter={(value) => playerNames[parseInt(value)] || `Player ${value}`}
            wrapperStyle={{ fontSize: "12px", fontWeight: 600 }}
          />
          {gameState.players.map((player) => (
            <Line
              key={player.id}
              type="monotone"
              dataKey={player.id.toString()}
              stroke={player.color}
              strokeWidth={2}
              dot={{ fill: player.color, r: 3 }}
              activeDot={{ r: 5 }}
              name={player.id.toString()}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
