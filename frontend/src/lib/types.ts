/**
 * TypeScript type definitions matching backend models
 * Based on backend/src/monopoly/engine/types.py
 */

export type SpaceType =
  | "PROPERTY"
  | "RAILROAD"
  | "UTILITY"
  | "TAX"
  | "CHANCE"
  | "COMMUNITY_CHEST"
  | "GO"
  | "JAIL"
  | "FREE_PARKING"
  | "GO_TO_JAIL";

export type ColorGroup =
  | "BROWN"
  | "LIGHT_BLUE"
  | "PINK"
  | "ORANGE"
  | "RED"
  | "YELLOW"
  | "GREEN"
  | "DARK_BLUE";

export type EventType =
  | "GAME_STARTED"
  | "TURN_STARTED"
  | "DICE_ROLLED"
  | "PLAYER_MOVED"
  | "PASSED_GO"
  | "PROPERTY_PURCHASED"
  | "RENT_PAID"
  | "TAX_PAID"
  | "CARD_DRAWN"
  | "CARD_EFFECT"
  | "HOUSE_BUILT"
  | "HOTEL_BUILT"
  | "BUILDING_SOLD"
  | "PROPERTY_MORTGAGED"
  | "PROPERTY_UNMORTGAGED"
  | "TRADE_PROPOSED"
  | "TRADE_ACCEPTED"
  | "TRADE_REJECTED"
  | "PLAYER_JAILED"
  | "PLAYER_FREED"
  | "PLAYER_BANKRUPT"
  | "AUCTION_STARTED"
  | "AUCTION_BID"
  | "AUCTION_WON"
  | "AGENT_SPOKE"
  | "AGENT_THOUGHT"
  | "GAME_OVER";

export interface PropertyData {
  name: string;
  position: number;
  price: number;
  mortgage_value: number;
  color_group: ColorGroup;
  rent: number[];
  house_cost: number;
}

export interface Space {
  position: number;
  name: string;
  space_type: SpaceType;
  color_group?: ColorGroup;
  price?: number;
}

export interface Player {
  id: number;
  name: string;
  position: number;
  cash: number;
  properties: number[];
  houses: { [position: number]: number };
  mortgaged: number[]; // Changed from mortgaged_properties: Set<number>
  in_jail: boolean;
  jail_turns: number;
  get_out_of_jail_cards: number;
  is_bankrupt: boolean;
  net_worth?: number; // Optional, from backend
  color: string; // Agent color for UI
  avatar?: string; // Agent avatar emoji
  personality: string; // Agent personality name
  model?: string; // LLM model name
}

export interface GameEvent {
  event_type: EventType;
  player_id: number;
  data: Record<string, any>;
  turn_number: number;
  timestamp?: string;
}

export interface GameState {
  game_id: string;
  players: Player[];
  current_player_index: number;
  turn_number: number;
  phase: string;
  status: "waiting" | "in_progress" | "paused" | "finished";
  winner_id: number | null;
}

export interface AgentMessage {
  player_id: number;
  message: string;
  timestamp: string;
  type: "public" | "private";
}

export interface TradeProposal {
  proposer_id: number;
  receiver_id: number;
  offered_properties: number[];
  requested_properties: number[];
  offered_cash: number;
  requested_cash: number;
}

// WebSocket message types
export interface WSGameEvent {
  event: EventType;
  data: Record<string, any>;
  turn_number?: number;
  timestamp: string;
}

// API response types
export interface StartGameResponse {
  game_id: string;
  message: string;
}

export interface GameStateResponse {
  game_id: string;
  state: GameState;
  events: GameEvent[];
}
