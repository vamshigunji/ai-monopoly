/**
 * Zustand store for Monopoly game state
 * Single source of truth for all game data
 */

import { create } from "zustand";
import type {
  GameState,
  GameEvent,
  AgentMessage,
  Player,
  WSGameEvent,
} from "@/lib/types";
import { BOARD_SPACES } from "@/lib/boardData";

interface GameStore {
  // Game state
  gameId: string | null;
  gameState: GameState | null;
  events: GameEvent[];

  // UI state
  publicChat: AgentMessage[];
  privateThoughts: { [playerId: number]: AgentMessage[] };
  selectedThoughtAgent: number;
  selectedAssetAgent: number;

  // Net worth tracking
  netWorthHistory: { [turn: number]: { [playerId: number]: number } };

  // Token usage tracking (cumulative per player from real LLM data)
  tokenHistory: { [turn: number]: { [playerId: number]: number } };
  cumulativeTokens: { [playerId: number]: number };

  // WebSocket state
  connected: boolean;
  connectionError: string | null;

  // Actions
  setGameId: (gameId: string) => void;
  setGameState: (state: GameState) => void;
  addEvent: (event: GameEvent) => void;
  addPublicMessage: (message: AgentMessage) => void;
  addPrivateThought: (playerId: number, message: AgentMessage) => void;
  setSelectedThoughtAgent: (playerId: number) => void;
  setSelectedAssetAgent: (playerId: number) => void;
  setConnected: (connected: boolean) => void;
  setConnectionError: (error: string | null) => void;
  handleWSEvent: (wsEvent: WSGameEvent) => void;
  resetGame: () => void;
  updateNetWorthHistory: () => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  gameId: null,
  gameState: null,
  events: [],
  publicChat: [],
  privateThoughts: {},
  selectedThoughtAgent: 0,
  selectedAssetAgent: 0,
  netWorthHistory: {},
  tokenHistory: {},
  cumulativeTokens: {},
  connected: false,
  connectionError: null,

  // Actions
  setGameId: (gameId) => set({ gameId }),

  setGameState: (gameState) => {
    set({ gameState });
    // Update net worth history when game state changes
    get().updateNetWorthHistory();
  },

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event],
    })),

  addPublicMessage: (message) =>
    set((state) => ({
      publicChat: [...state.publicChat, message],
    })),

  addPrivateThought: (playerId, message) =>
    set((state) => ({
      privateThoughts: {
        ...state.privateThoughts,
        [playerId]: [...(state.privateThoughts[playerId] || []), message],
      },
    })),

  setSelectedThoughtAgent: (playerId) =>
    set({ selectedThoughtAgent: playerId }),

  setSelectedAssetAgent: (playerId) =>
    set({ selectedAssetAgent: playerId }),

  setConnected: (connected) => set({ connected }),

  setConnectionError: (error) => set({ connectionError: error }),

  // Handle incoming WebSocket events
  handleWSEvent: (wsEvent) => {
    const { event, data, turn_number, timestamp } = wsEvent;

    // Handle game_state_sync event (initial state from WebSocket)
    if (event === "game_state_sync" as any) {
      console.log("📡 Received game_state_sync, updating full state");
      get().setGameState({
        game_id: data.game_id,
        players: data.players,
        current_player_index: data.current_player_id,
        turn_number: data.turn_number,
        phase: data.turn_phase || "ROLL_DICE",
        status: data.status as "waiting" | "in_progress" | "paused" | "finished",
        winner_id: null,
      });
      return;
    }

    // Create GameEvent from WSEvent
    const gameEvent: GameEvent = {
      event_type: event,
      player_id: data.player_id ?? -1,
      data,
      turn_number: turn_number ?? 0,
      timestamp,
    };

    // Add to events list
    get().addEvent(gameEvent);

    // Handle special event types
    switch (event) {
      case "AGENT_SPOKE":
        get().addPublicMessage({
          player_id: data.player_id,
          message: data.message,
          timestamp,
          type: "public",
        });
        break;

      case "AGENT_THOUGHT":
        get().addPrivateThought(data.player_id, {
          player_id: data.player_id,
          message: data.thought,
          timestamp,
          type: "private",
        });
        // Track real token usage from backend
        if (data.prompt_tokens !== undefined || data.completion_tokens !== undefined) {
          const totalTokens = (data.prompt_tokens || 0) + (data.completion_tokens || 0);
          if (totalTokens > 0) {
            set((state) => ({
              cumulativeTokens: {
                ...state.cumulativeTokens,
                [data.player_id]: totalTokens,
              },
            }));
          }
        }
        break;

      case "GAME_OVER":
        set((state) => ({
          gameState: state.gameState
            ? { ...state.gameState, status: "finished", winner_id: data.winner_id }
            : null,
        }));
        break;

      case "TURN_STARTED":
        set((state) => ({
          gameState: state.gameState
            ? {
                ...state.gameState,
                current_player_index: data.player_id,
                turn_number: turn_number ?? state.gameState.turn_number + 1,
              }
            : null,
        }));
        break;

      // Update player cash on financial events
      case "PROPERTY_PURCHASED":
      case "RENT_PAID":
      case "TAX_PAID":
      case "PASSED_GO":
        // We'll update full state via periodic polling or state updates from backend
        break;
    }
  },

  resetGame: () =>
    set({
      gameId: null,
      gameState: null,
      events: [],
      publicChat: [],
      privateThoughts: {},
      selectedThoughtAgent: 0,
      netWorthHistory: {},
      tokenHistory: {},
      cumulativeTokens: {},
      connected: false,
      connectionError: null,
    }),

  // Calculate and update net worth history
  updateNetWorthHistory: () => {
    const { gameState, netWorthHistory, tokenHistory, cumulativeTokens } = get();
    if (!gameState?.players || gameState.turn_number === 0) return;

    // Calculate net worth for each player
    const turnNetWorths: { [playerId: number]: number } = {};

    // Use real cumulative token data from AGENT_THOUGHT events
    const turnTokens: { [playerId: number]: number } = {};

    gameState.players.forEach((player) => {
      // Start with cash
      let netWorth = player.cash;

      // Add property values
      player.properties.forEach((position) => {
        const space = BOARD_SPACES[position];
        if (space?.price) {
          // Add base property price
          netWorth += space.price;

          // Add value of houses/hotels (house_cost * number of houses)
          const houses = player.houses[position] || 0;
          if (houses > 0 && space.space_type === "PROPERTY") {
            // House cost is typically 50% of property price in simplified monopoly
            const houseCost = Math.floor(space.price * 0.5);
            netWorth += houseCost * houses;
          }
        }
      });

      // Subtract mortgaged property values (they're worth 50% when mortgaged)
      player.mortgaged.forEach((position) => {
        const space = BOARD_SPACES[position];
        if (space?.price) {
          netWorth -= Math.floor(space.price * 0.5);
        }
      });

      turnNetWorths[player.id] = netWorth;

      // Use real token data from backend (cumulative totals)
      turnTokens[player.id] = cumulativeTokens[player.id] || 0;
    });

    // Update net worth history, keeping only last 30 turns
    const newNetWorthHistory = { ...netWorthHistory };
    newNetWorthHistory[gameState.turn_number] = turnNetWorths;

    // Update token history, keeping only last 30 turns
    const newTokenHistory = { ...tokenHistory };
    newTokenHistory[gameState.turn_number] = turnTokens;

    // Keep only last 30 turns for both histories
    const turns = Object.keys(newNetWorthHistory)
      .map(Number)
      .sort((a, b) => a - b);
    if (turns.length > 30) {
      const turnsToRemove = turns.slice(0, turns.length - 30);
      turnsToRemove.forEach((turn) => {
        delete newNetWorthHistory[turn];
        delete newTokenHistory[turn];
      });
    }

    set({
      netWorthHistory: newNetWorthHistory,
      tokenHistory: newTokenHistory
    });
  },
}));
