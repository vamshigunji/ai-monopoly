# Monopoly AI Agents -- API Specification

> Version 1.0 | Last updated: 2026-02-11
>
> This document is the single source of truth for every HTTP endpoint, WebSocket message, data model, and error code exposed by the Monopoly AI Agents backend. A frontend developer should be able to build the complete UI from this spec alone.

---

## Table of Contents

1. [Overview](#1-overview)
2. [REST Endpoints](#2-rest-endpoints)
3. [WebSocket Protocol](#3-websocket-protocol)
4. [Data Models](#4-data-models)
5. [Error Responses](#5-error-responses)
6. [Board Reference](#6-board-reference)
7. [Appendix: Enumerations](#7-appendix-enumerations)

---

## 1. Overview

### Connection Details

| Item | Value |
|------|-------|
| **Base URL** | `http://localhost:8000` |
| **WebSocket URL** | `ws://localhost:8000/ws/game/{game_id}` |
| **Content-Type** | `application/json` |
| **Authentication** | None (local development only) |
| **CORS** | Allowed from `http://localhost:3000` (Next.js dev server) |

### Architecture

```
Frontend (Next.js :3000)
   |
   |--- REST (HTTP) ---> FastAPI (:8000) /api/*       (start game, get state, controls)
   |
   |--- WebSocket -----> FastAPI (:8000) /ws/game/*   (real-time event stream)
   |
   v
Zustand Store (client-side state)
```

All game state flows **one-way** from the backend to the frontend. The frontend never directly mutates game state -- it sends control commands (start, pause, resume, speed) and receives game events via WebSocket.

### Conventions

- All timestamps are **ISO 8601** strings in UTC (e.g., `"2026-02-11T14:30:00Z"`).
- Player IDs are **0-indexed integers** (`0`, `1`, `2`, `3`).
- Board positions are **0-indexed integers** (`0` through `39`).
- Money amounts are **integers** (dollars, no cents).
- Property positions are used as unique identifiers for properties.
- Sequence numbers on events are **monotonically increasing integers** starting at `0`.

---

## 2. REST Endpoints

All REST endpoints are prefixed with `/api`.

---

### POST /api/game/start

Start a new Monopoly game with 4 AI agents.

**Request Body**

```json
{
  "num_players": 4,
  "seed": null,
  "speed": 1.0,
  "agents": [
    {
      "name": "The Shark",
      "model": "gpt-4o",
      "personality": "aggressive",
      "avatar": "shark",
      "color": "#EF4444"
    },
    {
      "name": "The Professor",
      "model": "gemini-pro",
      "personality": "analytical",
      "avatar": "professor",
      "color": "#3B82F6"
    },
    {
      "name": "The Hustler",
      "model": "gpt-4o-mini",
      "personality": "charismatic",
      "avatar": "hustler",
      "color": "#F59E0B"
    },
    {
      "name": "The Turtle",
      "model": "gemini-flash",
      "personality": "conservative",
      "avatar": "turtle",
      "color": "#10B981"
    }
  ]
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `num_players` | `integer` | No | `4` | Number of AI players (always 4). |
| `seed` | `integer \| null` | No | `null` | Random seed for deterministic replays. `null` uses a random seed. |
| `speed` | `float` | No | `1.0` | Delay multiplier between turns (1.0 = normal, 2.0 = 2x fast, 0.5 = half speed). |
| `agents` | `AgentConfig[]` | No | Default 4 agents | Array of agent configurations. Must have exactly `num_players` entries if provided. |

**AgentConfig Object**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | `string` | Yes | - | Display name for the agent. |
| `model` | `string` | Yes | - | LLM model identifier. One of: `"gpt-4o"`, `"gpt-4o-mini"`, `"gemini-pro"`, `"gemini-flash"`. |
| `personality` | `string` | Yes | - | Personality archetype. One of: `"aggressive"`, `"analytical"`, `"charismatic"`, `"conservative"`. |
| `avatar` | `string` | No | Derived from personality | Avatar identifier for the UI. |
| `color` | `string` | No | Auto-assigned | Hex color code for the player's token and UI elements. |

**Response** `201 Created`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "players": [
    {
      "id": 0,
      "name": "The Shark",
      "model": "gpt-4o",
      "personality": "aggressive",
      "avatar": "shark",
      "color": "#EF4444",
      "cash": 1500,
      "position": 0
    },
    {
      "id": 1,
      "name": "The Professor",
      "model": "gemini-pro",
      "personality": "analytical",
      "avatar": "professor",
      "color": "#3B82F6",
      "cash": 1500,
      "position": 0
    },
    {
      "id": 2,
      "name": "The Hustler",
      "model": "gpt-4o-mini",
      "personality": "charismatic",
      "avatar": "hustler",
      "color": "#F59E0B",
      "cash": 1500,
      "position": 0
    },
    {
      "id": 3,
      "name": "The Turtle",
      "model": "gemini-flash",
      "personality": "conservative",
      "avatar": "turtle",
      "color": "#10B981",
      "cash": 1500,
      "position": 0
    }
  ],
  "status": "in_progress",
  "seed": 42,
  "created_at": "2026-02-11T14:30:00Z"
}
```

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `400` | `INVALID_PLAYER_COUNT` | `num_players` is not 4. |
| `400` | `INVALID_AGENT_CONFIG` | Agent configuration is missing required fields or has invalid values. |
| `500` | `GAME_CREATION_FAILED` | Internal error during game initialization. |

---

### GET /api/game/{game_id}/state

Get the complete current game state.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `game_id` | `string (UUID)` | The game identifier returned from `/api/game/start`. |

**Response** `200 OK`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "in_progress",
  "turn_number": 42,
  "current_player_id": 2,
  "turn_phase": "ROLL",
  "speed": 1.0,
  "players": [
    {
      "id": 0,
      "name": "The Shark",
      "position": 24,
      "cash": 1120,
      "properties": [1, 3, 6, 8, 9],
      "houses": {
        "1": 2,
        "3": 2
      },
      "mortgaged": [],
      "in_jail": false,
      "jail_turns": 0,
      "get_out_of_jail_cards": 1,
      "is_bankrupt": false,
      "net_worth": 1870,
      "color": "#EF4444",
      "avatar": "shark",
      "personality": "aggressive"
    },
    {
      "id": 1,
      "name": "The Professor",
      "position": 11,
      "cash": 1680,
      "properties": [11, 13, 14, 25],
      "houses": {},
      "mortgaged": [25],
      "in_jail": false,
      "jail_turns": 0,
      "get_out_of_jail_cards": 0,
      "is_bankrupt": false,
      "net_worth": 2300,
      "color": "#3B82F6",
      "avatar": "professor",
      "personality": "analytical"
    },
    {
      "id": 2,
      "name": "The Hustler",
      "position": 19,
      "cash": 450,
      "properties": [16, 18, 19, 5, 15],
      "houses": {
        "16": 1,
        "18": 1,
        "19": 1
      },
      "mortgaged": [],
      "in_jail": false,
      "jail_turns": 0,
      "get_out_of_jail_cards": 0,
      "is_bankrupt": false,
      "net_worth": 1610,
      "color": "#F59E0B",
      "avatar": "hustler",
      "personality": "charismatic"
    },
    {
      "id": 3,
      "name": "The Turtle",
      "position": 10,
      "cash": 2100,
      "properties": [12, 28],
      "houses": {},
      "mortgaged": [],
      "in_jail": true,
      "jail_turns": 1,
      "get_out_of_jail_cards": 0,
      "is_bankrupt": false,
      "net_worth": 2400,
      "color": "#10B981",
      "avatar": "turtle",
      "personality": "conservative"
    }
  ],
  "board": [
    {
      "position": 0,
      "name": "GO",
      "type": "GO",
      "owner_id": null,
      "houses": 0,
      "is_mortgaged": false,
      "color_group": null,
      "price": null
    },
    {
      "position": 1,
      "name": "Mediterranean Avenue",
      "type": "PROPERTY",
      "owner_id": 0,
      "houses": 2,
      "is_mortgaged": false,
      "color_group": "BROWN",
      "price": 60,
      "rent_schedule": [2, 10, 30, 90, 160, 250],
      "house_cost": 50,
      "mortgage_value": 30
    }
  ],
  "bank": {
    "houses_available": 28,
    "hotels_available": 12
  },
  "last_roll": {
    "die1": 4,
    "die2": 3,
    "total": 7,
    "doubles": false
  }
}
```

The `board` array contains all 40 spaces. See [BoardSpaceState](#boardspacestate) for the full schema of each entry. The example above shows only two entries for brevity.

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `404` | `GAME_NOT_FOUND` | No game exists with the given `game_id`. |

---

### GET /api/game/{game_id}/history

Get the event history for a game.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `game_id` | `string (UUID)` | The game identifier. |

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since` | `integer` | `0` | Return only events with `sequence >= since`. Use this for incremental polling. |
| `limit` | `integer` | `1000` | Maximum number of events to return. |
| `event_type` | `string` | `null` | Filter by event type (e.g., `"dice_rolled"`, `"agent_spoke"`). Comma-separated for multiple types. |

**Response** `200 OK`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "events": [
    {
      "event": "dice_rolled",
      "data": {
        "player_id": 0,
        "die1": 4,
        "die2": 3,
        "total": 7,
        "doubles": false
      },
      "timestamp": "2026-02-11T14:30:05Z",
      "turn_number": 1,
      "sequence": 3
    },
    {
      "event": "player_moved",
      "data": {
        "player_id": 0,
        "new_position": 7,
        "spaces_moved": 7
      },
      "timestamp": "2026-02-11T14:30:05Z",
      "turn_number": 1,
      "sequence": 4
    }
  ],
  "total_events": 1234,
  "has_more": true
}
```

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `404` | `GAME_NOT_FOUND` | No game exists with the given `game_id`. |

---

### POST /api/game/{game_id}/pause

Pause a running game. The game loop stops after the current turn completes.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `game_id` | `string (UUID)` | The game identifier. |

**Request Body**: None

**Response** `200 OK`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "paused",
  "turn_number": 42
}
```

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `404` | `GAME_NOT_FOUND` | No game exists with the given `game_id`. |
| `409` | `GAME_NOT_RUNNING` | Game is not currently `in_progress` (already paused or finished). |

---

### POST /api/game/{game_id}/resume

Resume a paused game.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `game_id` | `string (UUID)` | The game identifier. |

**Request Body**: None

**Response** `200 OK`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "in_progress",
  "turn_number": 42
}
```

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `404` | `GAME_NOT_FOUND` | No game exists with the given `game_id`. |
| `409` | `GAME_NOT_PAUSED` | Game is not currently `paused`. |

---

### POST /api/game/{game_id}/speed

Change the game speed (delay between turns).

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `game_id` | `string (UUID)` | The game identifier. |

**Request Body**

```json
{
  "speed": 2.0
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `speed` | `float` | Yes | Speed multiplier. Range: `0.25` (very slow) to `5.0` (very fast). `1.0` is normal speed. |

**Response** `200 OK`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "speed": 2.0
}
```

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `404` | `GAME_NOT_FOUND` | No game exists with the given `game_id`. |
| `400` | `INVALID_SPEED` | Speed is outside the valid range `[0.25, 5.0]`. |

---

### GET /api/game/{game_id}/agents

Get detailed information about all AI agents in the game, including their personality descriptions and configuration.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `game_id` | `string (UUID)` | The game identifier. |

**Response** `200 OK`

```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "agents": [
    {
      "id": 0,
      "name": "The Shark",
      "model": "gpt-4o",
      "personality": "aggressive",
      "avatar": "shark",
      "color": "#EF4444",
      "description": "An aggressive negotiator who buys everything in sight, trades ruthlessly, and intimidates opponents into bad deals. Favors monopoly acquisition at any cost.",
      "style": {
        "risk_tolerance": "high",
        "trading_aggression": "very_high",
        "building_strategy": "opportunistic",
        "speech_pattern": "Threatening, confident, uses ultimatums"
      }
    },
    {
      "id": 1,
      "name": "The Professor",
      "model": "gemini-pro",
      "personality": "analytical",
      "avatar": "professor",
      "color": "#3B82F6",
      "description": "An analytical strategist who calculates expected values for every decision, builds methodically, and only accepts trades with clear mathematical advantage.",
      "style": {
        "risk_tolerance": "medium",
        "trading_aggression": "medium",
        "building_strategy": "methodical",
        "speech_pattern": "Precise, data-driven, quotes probabilities"
      }
    },
    {
      "id": 2,
      "name": "The Hustler",
      "model": "gpt-4o-mini",
      "personality": "charismatic",
      "avatar": "hustler",
      "color": "#F59E0B",
      "description": "A charismatic bluffer who makes lopsided trade offers sound amazing, takes unpredictable risks, and uses charm to manipulate other agents.",
      "style": {
        "risk_tolerance": "high",
        "trading_aggression": "high",
        "building_strategy": "unpredictable",
        "speech_pattern": "Persuasive, flattering, changes the subject"
      }
    },
    {
      "id": 3,
      "name": "The Turtle",
      "model": "gemini-flash",
      "personality": "conservative",
      "avatar": "turtle",
      "color": "#10B981",
      "description": "A conservative builder who hoards cash, avoids risky trades, and only develops properties when holding complete monopolies with ample reserves.",
      "style": {
        "risk_tolerance": "low",
        "trading_aggression": "low",
        "building_strategy": "patient",
        "speech_pattern": "Cautious, brief, politely declines most offers"
      }
    }
  ]
}
```

**Error Responses**

| Code | Error Code | Condition |
|------|------------|-----------|
| `404` | `GAME_NOT_FOUND` | No game exists with the given `game_id`. |

---

## 3. WebSocket Protocol

### Connection

**URL**: `ws://localhost:8000/ws/game/{game_id}`

**Behavior on connect**:
1. Server validates that `game_id` exists (sends error frame and closes if not).
2. Server immediately sends the full current game state as the first message (event type `"game_state_sync"`).
3. Server then streams all subsequent game events in real time.
4. Multiple clients can connect to the same game simultaneously.

**Behavior on disconnect**:
- The game continues running regardless of connected clients.
- Reconnecting clients receive a full state sync followed by events from the current point.

### Message Format (server to client)

Every message from the server is a JSON object with this structure:

```json
{
  "event": "event_type_string",
  "data": {},
  "timestamp": "2026-02-11T14:30:05Z",
  "turn_number": 42,
  "sequence": 1234
}
```

| Field | Type | Description |
|-------|------|-------------|
| `event` | `string` | The event type identifier (see table below). |
| `data` | `object` | Event-specific payload. |
| `timestamp` | `string` | ISO 8601 timestamp of when the event occurred. |
| `turn_number` | `integer` | The turn number during which this event occurred. |
| `sequence` | `integer` | Monotonically increasing sequence number. Use for ordering and deduplication. |

### Message Format (client to server)

The WebSocket is primarily server-push. The following client messages are supported for convenience, but the same actions are available via REST:

```json
{
  "action": "pause" | "resume" | "set_speed",
  "data": {}
}
```

| Action | Data | Description |
|--------|------|-------------|
| `"pause"` | `{}` | Pause the game. |
| `"resume"` | `{}` | Resume the game. |
| `"set_speed"` | `{ "speed": 2.0 }` | Change game speed. |

---

### Event Types Reference

Below is the complete list of every event type the server emits. Each event is documented with its full `data` schema.

---

#### game_state_sync

Sent immediately on WebSocket connection. Contains the full game state snapshot.

```json
{
  "event": "game_state_sync",
  "data": {
    "game_id": "uuid",
    "status": "in_progress",
    "turn_number": 42,
    "current_player_id": 0,
    "turn_phase": "PRE_ROLL",
    "speed": 1.0,
    "players": [ /* PlayerState[] -- see Data Models */ ],
    "board": [ /* BoardSpaceState[] -- see Data Models */ ],
    "bank": { "houses_available": 32, "hotels_available": 12 },
    "last_roll": null
  },
  "timestamp": "2026-02-11T14:30:00Z",
  "turn_number": 42,
  "sequence": 0
}
```

---

#### game_started

Emitted once when a new game begins.

```json
{
  "event": "game_started",
  "data": {
    "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "players": [
      {
        "id": 0,
        "name": "The Shark",
        "model": "gpt-4o",
        "personality": "aggressive",
        "avatar": "shark",
        "color": "#EF4444",
        "cash": 1500,
        "position": 0
      }
    ],
    "board": [ /* BoardSpaceState[] */ ],
    "seed": 42
  }
}
```

---

#### turn_started

Emitted at the beginning of each player's turn.

```json
{
  "event": "turn_started",
  "data": {
    "player_id": 0,
    "turn_number": 42
  }
}
```

---

#### dice_rolled

Emitted whenever dice are rolled (regular turns, jail attempts, utility rent calculations).

```json
{
  "event": "dice_rolled",
  "data": {
    "player_id": 0,
    "die1": 4,
    "die2": 3,
    "total": 7,
    "doubles": false
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player who rolled. |
| `die1` | `integer` | First die value (1-6). |
| `die2` | `integer` | Second die value (1-6). |
| `total` | `integer` | Sum of both dice (2-12). |
| `doubles` | `boolean` | Whether both dice show the same value. |

---

#### player_moved

Emitted when a player's token moves on the board.

```json
{
  "event": "player_moved",
  "data": {
    "player_id": 0,
    "new_position": 7,
    "spaces_moved": 7
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player who moved. |
| `new_position` | `integer` | Board position the player landed on (0-39). |
| `spaces_moved` | `integer` | Number of spaces moved forward. Absent on direct moves (card effects). |

When a player is moved directly (e.g., by a card effect), the `data` may instead contain:

```json
{
  "player_id": 0,
  "new_position": 24,
  "direct_move": true
}
```

Or when a card sends a player backwards:

```json
{
  "player_id": 0,
  "new_position": 4,
  "went_back": 3
}
```

---

#### passed_go

Emitted when a player passes or lands on GO and collects the $200 salary.

```json
{
  "event": "passed_go",
  "data": {
    "player_id": 0,
    "salary": 200
  }
}
```

---

#### property_purchased

Emitted when a player buys a property at its listed price.

```json
{
  "event": "property_purchased",
  "data": {
    "player_id": 0,
    "position": 6,
    "price": 100,
    "name": "Oriental Avenue"
  }
}
```

---

#### auction_started

Emitted when a property goes to auction (player declined to buy).

```json
{
  "event": "auction_started",
  "data": {
    "position": 6,
    "name": "Oriental Avenue",
    "starting_bid": 1
  }
}
```

---

#### auction_bid

Emitted for each bid placed during an auction.

```json
{
  "event": "auction_bid",
  "data": {
    "player_id": 1,
    "position": 6,
    "amount": 75
  }
}
```

---

#### auction_won

Emitted when an auction concludes and a player wins the property.

```json
{
  "event": "auction_won",
  "data": {
    "player_id": 1,
    "position": 6,
    "bid": 85,
    "name": "Oriental Avenue"
  }
}
```

If no player bids, the property is not sold, and only `auction_started` is emitted (no `auction_won`).

---

#### rent_paid

Emitted when a player pays rent to a property owner.

```json
{
  "event": "rent_paid",
  "data": {
    "player_id": 2,
    "amount": 150,
    "to_player": 0,
    "position": 1,
    "property_name": "Mediterranean Avenue"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player paying rent. |
| `amount` | `integer` | Rent amount in dollars. |
| `to_player` | `integer` | The property owner receiving rent. |
| `position` | `integer` | Board position of the property. |
| `property_name` | `string` | Human-readable name of the property. |

---

#### card_drawn

Emitted when a player draws a Chance or Community Chest card.

```json
{
  "event": "card_drawn",
  "data": {
    "player_id": 0,
    "description": "Advance to Boardwalk",
    "deck": "CHANCE"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player who drew the card. |
| `description` | `string` | The text on the card. |
| `deck` | `string` | Which deck: `"CHANCE"` or `"COMMUNITY_CHEST"`. |

---

#### tax_paid

Emitted when a player lands on a tax space and pays the tax.

```json
{
  "event": "tax_paid",
  "data": {
    "player_id": 0,
    "amount": 200,
    "space": "Income Tax"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player paying the tax. |
| `amount` | `integer` | Tax amount ($200 for Income Tax, $100 for Luxury Tax). |
| `space` | `string` | Name of the tax space. |

---

#### house_built

Emitted when a player builds a house on a property.

```json
{
  "event": "house_built",
  "data": {
    "player_id": 0,
    "position": 1,
    "houses": 2,
    "name": "Mediterranean Avenue",
    "cost": 50
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player building. |
| `position` | `integer` | Board position of the property. |
| `houses` | `integer` | New total house count on this property (1-4). |
| `name` | `string` | Property name. |
| `cost` | `integer` | Cost of the house. |

---

#### hotel_built

Emitted when a player upgrades from 4 houses to a hotel.

```json
{
  "event": "hotel_built",
  "data": {
    "player_id": 0,
    "position": 1,
    "name": "Mediterranean Avenue",
    "cost": 50
  }
}
```

---

#### building_sold

Emitted when a player sells a house or hotel back to the bank.

```json
{
  "event": "building_sold",
  "data": {
    "player_id": 0,
    "position": 1,
    "refund": 25,
    "remaining_houses": 1
  }
}
```

---

#### property_mortgaged

Emitted when a player mortgages a property.

```json
{
  "event": "property_mortgaged",
  "data": {
    "player_id": 0,
    "position": 6,
    "value": 50,
    "name": "Oriental Avenue"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The player mortgaging. |
| `position` | `integer` | Board position. |
| `value` | `integer` | Cash received from mortgaging. |
| `name` | `string` | Property name. |

---

#### property_unmortgaged

Emitted when a player lifts a mortgage on a property.

```json
{
  "event": "property_unmortgaged",
  "data": {
    "player_id": 0,
    "position": 6,
    "cost": 55,
    "name": "Oriental Avenue"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `cost` | `integer` | Cash paid to unmortgage (mortgage value + 10% interest, rounded down). |

---

#### trade_proposed

Emitted when an agent proposes a trade to another agent.

```json
{
  "event": "trade_proposed",
  "data": {
    "proposer_id": 0,
    "receiver_id": 1,
    "details": {
      "offered_properties": [1, 3],
      "requested_properties": [11],
      "offered_cash": 200,
      "requested_cash": 0,
      "offered_jail_cards": 0,
      "requested_jail_cards": 0
    }
  }
}
```

---

#### trade_accepted

Emitted when a trade is accepted and executed.

```json
{
  "event": "trade_accepted",
  "data": {
    "proposer_id": 0,
    "receiver_id": 1,
    "details": {
      "offered_properties": [1, 3],
      "requested_properties": [11],
      "offered_cash": 200,
      "requested_cash": 0,
      "offered_jail_cards": 0,
      "requested_jail_cards": 0
    }
  }
}
```

---

#### trade_rejected

Emitted when a trade proposal is declined.

```json
{
  "event": "trade_rejected",
  "data": {
    "proposer_id": 0,
    "receiver_id": 1,
    "reason": "Receiver declined the offer"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reason` | `string` | Human-readable reason for rejection. May come from the AI agent or from validation failure. |

---

#### player_jailed

Emitted when a player is sent to jail (via Go To Jail space, card, or rolling 3 consecutive doubles).

```json
{
  "event": "player_jailed",
  "data": {
    "player_id": 0,
    "reason": "landed_on_go_to_jail"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reason` | `string` | One of: `"landed_on_go_to_jail"`, `"card_effect"`, `"three_doubles"`. |

---

#### player_freed

Emitted when a player gets out of jail.

```json
{
  "event": "player_freed",
  "data": {
    "player_id": 0,
    "method": "paid_fine"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `method` | `string` | How they got out: `"paid_fine"` ($50), `"used_card"` (Get Out of Jail Free), `"rolled_doubles"`, `"forced_payment"` (failed to roll doubles 3 turns, forced to pay $50). |
| `roll` | `integer \| null` | The dice total, present only when `method` is `"rolled_doubles"` or `"forced_payment"`. |

---

#### player_bankrupt

Emitted when a player goes bankrupt and is eliminated from the game.

```json
{
  "event": "player_bankrupt",
  "data": {
    "player_id": 2,
    "creditor_id": 0,
    "assets_transferred": {
      "properties": [16, 18, 19, 5, 15],
      "cash": 450,
      "jail_cards": 0
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The bankrupt player. |
| `creditor_id` | `integer \| null` | The player who caused the bankruptcy (receives assets). `null` if bankrupt to the bank (properties go to auction). |
| `assets_transferred` | `object` | Summary of assets transferred to the creditor or returned to the bank. |

---

#### agent_spoke

Emitted when an AI agent says something publicly (visible to all agents and the frontend chat panel).

```json
{
  "event": "agent_spoke",
  "data": {
    "player_id": 0,
    "message": "Give me Park Place or I'll make sure you regret it.",
    "context": "negotiation"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The speaking agent. |
| `message` | `string` | The public message text. |
| `context` | `string` | Context for the message. One of: `"negotiation"`, `"reaction"`, `"taunt"`, `"general"`. |

---

#### agent_thought

Emitted when an AI agent has a private thought (internal strategy reasoning, visible only in the UI when that agent's thought panel is selected).

```json
{
  "event": "agent_thought",
  "data": {
    "player_id": 1,
    "thought": "If I acquire Illinois Avenue, I complete the red monopoly. Expected ROI with 3 houses is 340% over 15 turns. Worth paying up to $350 in a trade.",
    "category": "strategy"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | `integer` | The thinking agent. |
| `thought` | `string` | The private thought text. |
| `category` | `string` | Category of thought. One of: `"strategy"`, `"valuation"`, `"opponent_analysis"`, `"trade_evaluation"`, `"risk_assessment"`. |

---

#### game_over

Emitted when the game ends (only 1 player remaining, or max turns reached).

```json
{
  "event": "game_over",
  "data": {
    "winner_id": 1,
    "winner_name": "The Professor",
    "reason": "last_player_standing",
    "total_turns": 342,
    "duration_seconds": 1847,
    "final_standings": [
      {
        "rank": 1,
        "player_id": 1,
        "name": "The Professor",
        "net_worth": 4850,
        "properties_owned": 12,
        "is_bankrupt": false,
        "eliminated_on_turn": null
      },
      {
        "rank": 2,
        "player_id": 0,
        "name": "The Shark",
        "net_worth": 0,
        "properties_owned": 0,
        "is_bankrupt": true,
        "eliminated_on_turn": 298
      },
      {
        "rank": 3,
        "player_id": 3,
        "name": "The Turtle",
        "net_worth": 0,
        "properties_owned": 0,
        "is_bankrupt": true,
        "eliminated_on_turn": 215
      },
      {
        "rank": 4,
        "player_id": 2,
        "name": "The Hustler",
        "net_worth": 0,
        "properties_owned": 0,
        "is_bankrupt": true,
        "eliminated_on_turn": 187
      }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `winner_id` | `integer` | Player ID of the winner. |
| `winner_name` | `string` | Display name of the winner. |
| `reason` | `string` | `"last_player_standing"` or `"max_turns_reached"`. |
| `total_turns` | `integer` | Total number of turns played. |
| `duration_seconds` | `integer` | Wall-clock duration of the game in seconds. |
| `final_standings` | `FinalStanding[]` | Ordered list of all players, ranked by finish position. |

---

### Event Type Summary Table

| Event Type | Frequency | Description |
|------------|-----------|-------------|
| `game_state_sync` | Once per connection | Full state snapshot on WebSocket connect |
| `game_started` | Once per game | Game initialization |
| `turn_started` | Every turn | New turn begins |
| `dice_rolled` | 1+ per turn | Dice are rolled |
| `player_moved` | 1+ per turn | Token moves on board |
| `passed_go` | Occasional | Player passes/lands on GO |
| `property_purchased` | Occasional | Property bought at list price |
| `auction_started` | Occasional | Property auction begins |
| `auction_bid` | 0+ per auction | Bid placed during auction |
| `auction_won` | 0-1 per auction | Auction concludes with winner |
| `rent_paid` | Common | Rent payment between players |
| `card_drawn` | Occasional | Chance/Community Chest card drawn |
| `tax_paid` | Occasional | Tax space payment |
| `house_built` | Occasional | House construction |
| `hotel_built` | Rare | Hotel upgrade |
| `building_sold` | Rare | Building sold back to bank |
| `property_mortgaged` | Occasional | Property mortgaged |
| `property_unmortgaged` | Occasional | Mortgage lifted |
| `trade_proposed` | Occasional | Trade offer made |
| `trade_accepted` | Occasional | Trade completed |
| `trade_rejected` | Occasional | Trade declined |
| `player_jailed` | Occasional | Player sent to jail |
| `player_freed` | Occasional | Player leaves jail |
| `player_bankrupt` | 0-3 per game | Player eliminated |
| `agent_spoke` | Frequent | Public agent dialogue |
| `agent_thought` | Frequent | Private agent reasoning |
| `game_over` | Once per game | Game ends |

---

## 4. Data Models

These are the canonical JSON shapes used throughout the REST and WebSocket APIs.

---

### GameState

The complete state of a Monopoly game at a point in time. Returned by `GET /api/game/{game_id}/state` and the `game_state_sync` WebSocket event.

```typescript
interface GameState {
  game_id: string;               // UUID
  status: GameStatus;            // "setup" | "in_progress" | "paused" | "finished"
  turn_number: number;           // Current turn count (0-indexed, increments each player turn)
  current_player_id: number;     // Player ID of whose turn it is (0-3)
  turn_phase: TurnPhase;         // Current phase within the turn
  speed: number;                 // Game speed multiplier
  players: PlayerState[];        // Array of 4 player states
  board: BoardSpaceState[];      // Array of 40 board space states
  bank: BankState;               // Bank inventory
  last_roll: DiceRoll | null;    // Most recent dice roll, null if game just started
  created_at: string;            // ISO 8601 timestamp
}
```

---

### PlayerState

Complete state of a single player.

```typescript
interface PlayerState {
  id: number;                     // 0-3
  name: string;                   // Display name (e.g., "The Shark")
  position: number;               // Current board position (0-39)
  cash: number;                   // Current cash in dollars
  properties: number[];           // Array of owned property positions
  houses: Record<string, number>; // Position (as string key) -> house count (1-4), 5 means hotel
  mortgaged: number[];            // Array of mortgaged property positions
  in_jail: boolean;               // Whether the player is currently in jail
  jail_turns: number;             // Number of turns spent in jail (0-3)
  get_out_of_jail_cards: number;  // Number of GOOJF cards held (0-2)
  is_bankrupt: boolean;           // Whether the player has been eliminated
  net_worth: number;              // Total value: cash + property values + building values
  consecutive_doubles: number;    // Consecutive doubles rolled this turn (0-2, 3 = jail)

  // Agent metadata (included in full state, may be omitted in events)
  color: string;                  // Hex color code
  avatar: string;                 // Avatar identifier
  personality: string;            // Personality archetype
  model?: string;                 // LLM model (optional, included in /agents response)
}
```

**House Count Encoding**

The `houses` dictionary maps position numbers (as string keys in JSON) to house counts:
- `0` = no houses (key absent from dict)
- `1` = 1 house
- `2` = 2 houses
- `3` = 3 houses
- `4` = 4 houses
- `5` = hotel

---

### BoardSpaceState

State of a single board space. The `board` array always has 40 entries, one per position.

```typescript
interface BoardSpaceState {
  position: number;                // 0-39
  name: string;                    // Space name (e.g., "Mediterranean Avenue")
  type: SpaceType;                 // Space type enum value

  // Present only for purchasable spaces (PROPERTY, RAILROAD, UTILITY)
  owner_id: number | null;         // Player ID of owner, null if unowned or non-purchasable
  houses: number;                  // Number of houses (0-4) or 5 for hotel. 0 for non-property spaces
  is_mortgaged: boolean;           // Whether the property is mortgaged

  // Present only for PROPERTY type
  color_group: ColorGroup | null;  // Color group enum value, null for non-property
  price: number | null;            // Purchase price, null for non-purchasable
  rent_schedule: number[] | null;  // [base, 1h, 2h, 3h, 4h, hotel] rent values
  house_cost: number | null;       // Cost per house/hotel
  mortgage_value: number | null;   // Cash received when mortgaging

  // Present only for RAILROAD type
  // price: 200 (always)
  // mortgage_value: 100 (always)
  // Rent depends on how many railroads the owner has: $25/$50/$100/$200

  // Present only for UTILITY type
  // price: 150 (always)
  // mortgage_value: 75 (always)
  // Rent = dice_roll * multiplier (4x for 1 utility, 10x for 2)

  // Present only for TAX type
  tax_amount: number | null;       // Tax amount ($200 Income Tax, $100 Luxury Tax)
}
```

---

### PropertyInfo

Detailed static information about a purchasable property. This data is constant throughout the game.

```typescript
interface PropertyInfo {
  position: number;
  name: string;
  type: "property" | "railroad" | "utility";
  color_group: ColorGroup | null;  // null for railroad/utility
  price: number;
  mortgage_value: number;
  house_cost: number | null;       // null for railroad/utility

  // Rent schedule (varies by type)
  rent_schedule: RentSchedule;
}

// For standard properties
interface PropertyRentSchedule {
  base: number;              // Unimproved rent
  monopoly: number;          // Unimproved rent with full color group (2x base)
  one_house: number;
  two_houses: number;
  three_houses: number;
  four_houses: number;
  hotel: number;
}

// For railroads
interface RailroadRentSchedule {
  one_owned: 25;
  two_owned: 50;
  three_owned: 100;
  four_owned: 200;
}

// For utilities
interface UtilityRentSchedule {
  one_owned_multiplier: 4;    // Rent = dice_roll * 4
  two_owned_multiplier: 10;   // Rent = dice_roll * 10
}
```

---

### DiceRoll

Result of rolling two six-sided dice.

```typescript
interface DiceRoll {
  die1: number;     // 1-6
  die2: number;     // 1-6
  total: number;    // 2-12 (die1 + die2)
  doubles: boolean; // die1 === die2
}
```

---

### TradeProposal

A trade offer between two players.

```typescript
interface TradeProposal {
  proposer_id: number;             // Player proposing the trade
  receiver_id: number;             // Player receiving the offer
  offered_properties: number[];    // Positions of properties the proposer offers
  requested_properties: number[];  // Positions of properties the proposer wants
  offered_cash: number;            // Cash the proposer offers (>= 0)
  requested_cash: number;          // Cash the proposer requests (>= 0)
  offered_jail_cards: number;      // GOOJF cards the proposer offers (>= 0)
  requested_jail_cards: number;    // GOOJF cards the proposer requests (>= 0)
}
```

**Trade Validation Rules** (enforced server-side):
- The proposer must own all `offered_properties`.
- The receiver must own all `requested_properties`.
- No property involved in a trade may have buildings on it. Buildings must be sold first.
- The proposer must have at least `offered_cash` in cash.
- The receiver must have at least `requested_cash` in cash.
- Jail card counts must not exceed what each player holds.
- The trade must involve at least one item (cannot be empty).
- Mortgaged properties can be traded. The receiver pays a 10% transfer fee immediately and may choose to unmortgage or keep it mortgaged.

---

### AgentInfo

Information about an AI agent's configuration and personality.

```typescript
interface AgentInfo {
  id: number;                  // Player ID (0-3)
  name: string;                // Display name
  model: string;               // LLM model identifier
  personality: string;         // Personality archetype
  avatar: string;              // Avatar identifier for UI rendering
  color: string;               // Hex color code
  description: string;         // Human-readable personality description
  style: AgentStyle;           // Behavioral parameters
}

interface AgentStyle {
  risk_tolerance: "low" | "medium" | "high";
  trading_aggression: "low" | "medium" | "high" | "very_high";
  building_strategy: "patient" | "methodical" | "opportunistic" | "unpredictable";
  speech_pattern: string;      // Description of how the agent speaks
}
```

---

### BankState

Current state of the bank's building inventory.

```typescript
interface BankState {
  houses_available: number;    // 0-32 (starts at 32)
  hotels_available: number;    // 0-12 (starts at 12)
}
```

---

### FinalStanding

A player's final ranking at game end.

```typescript
interface FinalStanding {
  rank: number;                // 1-4 (1 = winner)
  player_id: number;           // Player ID
  name: string;                // Display name
  net_worth: number;           // Final net worth (0 if bankrupt)
  properties_owned: number;    // Count of properties at elimination/game end
  is_bankrupt: boolean;
  eliminated_on_turn: number | null; // Turn number when eliminated, null for winner
}
```

---

## 5. Error Responses

All error responses follow a consistent format:

```json
{
  "error": "Human-readable error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error` | `string` | A human-readable description of what went wrong. |
| `code` | `string` | A machine-readable error code (UPPER_SNAKE_CASE). |
| `details` | `object` | Optional additional context. May be empty `{}`. |

### Error Code Reference

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `INVALID_REQUEST` | Malformed JSON or missing required fields. |
| `400` | `INVALID_PLAYER_COUNT` | `num_players` is not exactly 4. |
| `400` | `INVALID_AGENT_CONFIG` | Agent configuration has invalid `model`, `personality`, or is incomplete. |
| `400` | `INVALID_SPEED` | Speed value is outside the range `[0.25, 5.0]`. |
| `400` | `INVALID_ACTION` | The requested action is not valid in the current game state (e.g., building on an unowned property). |
| `400` | `INVALID_TRADE` | Trade proposal fails validation (insufficient funds, missing ownership, buildings present). |
| `400` | `INVALID_EVENT_FILTER` | Unknown event type specified in the `event_type` query parameter. |
| `404` | `GAME_NOT_FOUND` | No game exists with the provided `game_id`. |
| `409` | `GAME_ALREADY_STARTED` | Attempt to start a game when one is already running with the same ID. |
| `409` | `GAME_NOT_RUNNING` | Action requires game to be `in_progress`, but game is paused or finished. |
| `409` | `GAME_NOT_PAUSED` | Attempted to resume a game that is not paused. |
| `409` | `GAME_ALREADY_FINISHED` | Attempted to perform an action on a completed game. |
| `500` | `GAME_CREATION_FAILED` | Internal error during game initialization. |
| `500` | `LLM_ERROR` | An LLM provider returned an error or timed out. The game auto-retries with backoff; if all retries fail, the agent makes a random valid move. |
| `500` | `INTERNAL_ERROR` | Unexpected server error. |

### WebSocket Error Frame

When a WebSocket connection fails, the server sends an error frame before closing:

```json
{
  "event": "error",
  "data": {
    "error": "Game not found",
    "code": "GAME_NOT_FOUND"
  },
  "timestamp": "2026-02-11T14:30:00Z",
  "turn_number": 0,
  "sequence": -1
}
```

The connection is then closed with WebSocket close code `4404` (custom application code).

| Close Code | Meaning |
|------------|---------|
| `4400` | Bad request (invalid game_id format) |
| `4404` | Game not found |
| `4500` | Internal server error |

---

## 6. Board Reference

Complete board layout with all 40 positions. This data is static and returned in the `board` array of the game state.

| Position | Name | Type | Color Group | Price | Mortgage | House Cost | Rent Schedule |
|----------|------|------|-------------|-------|----------|------------|---------------|
| 0 | GO | GO | - | - | - | - | Collect $200 salary |
| 1 | Mediterranean Avenue | PROPERTY | BROWN | $60 | $30 | $50 | 2 / 10 / 30 / 90 / 160 / 250 |
| 2 | Community Chest | COMMUNITY_CHEST | - | - | - | - | - |
| 3 | Baltic Avenue | PROPERTY | BROWN | $60 | $30 | $50 | 4 / 20 / 60 / 180 / 320 / 450 |
| 4 | Income Tax | TAX | - | - | - | - | Pay $200 |
| 5 | Reading Railroad | RAILROAD | - | $200 | $100 | - | 25 / 50 / 100 / 200 |
| 6 | Oriental Avenue | PROPERTY | LIGHT_BLUE | $100 | $50 | $50 | 6 / 30 / 90 / 270 / 400 / 550 |
| 7 | Chance | CHANCE | - | - | - | - | - |
| 8 | Vermont Avenue | PROPERTY | LIGHT_BLUE | $100 | $50 | $50 | 6 / 30 / 90 / 270 / 400 / 550 |
| 9 | Connecticut Avenue | PROPERTY | LIGHT_BLUE | $120 | $60 | $50 | 8 / 40 / 100 / 300 / 450 / 600 |
| 10 | Jail / Just Visiting | JAIL | - | - | - | - | - |
| 11 | St. Charles Place | PROPERTY | PINK | $140 | $70 | $100 | 10 / 50 / 150 / 450 / 625 / 750 |
| 12 | Electric Company | UTILITY | - | $150 | $75 | - | 4x or 10x dice roll |
| 13 | States Avenue | PROPERTY | PINK | $140 | $70 | $100 | 10 / 50 / 150 / 450 / 625 / 750 |
| 14 | Virginia Avenue | PROPERTY | PINK | $160 | $80 | $100 | 12 / 60 / 180 / 500 / 700 / 900 |
| 15 | Pennsylvania Railroad | RAILROAD | - | $200 | $100 | - | 25 / 50 / 100 / 200 |
| 16 | St. James Place | PROPERTY | ORANGE | $180 | $90 | $100 | 14 / 70 / 200 / 550 / 750 / 950 |
| 17 | Community Chest | COMMUNITY_CHEST | - | - | - | - | - |
| 18 | Tennessee Avenue | PROPERTY | ORANGE | $180 | $90 | $100 | 14 / 70 / 200 / 550 / 750 / 950 |
| 19 | New York Avenue | PROPERTY | ORANGE | $200 | $100 | $100 | 16 / 80 / 220 / 600 / 800 / 1000 |
| 20 | Free Parking | FREE_PARKING | - | - | - | - | - |
| 21 | Kentucky Avenue | PROPERTY | RED | $220 | $110 | $150 | 18 / 90 / 250 / 700 / 875 / 1050 |
| 22 | Chance | CHANCE | - | - | - | - | - |
| 23 | Indiana Avenue | PROPERTY | RED | $220 | $110 | $150 | 18 / 90 / 250 / 700 / 875 / 1050 |
| 24 | Illinois Avenue | PROPERTY | RED | $240 | $120 | $150 | 20 / 100 / 300 / 750 / 925 / 1100 |
| 25 | B&O Railroad | RAILROAD | - | $200 | $100 | - | 25 / 50 / 100 / 200 |
| 26 | Atlantic Avenue | PROPERTY | YELLOW | $260 | $130 | $150 | 22 / 110 / 330 / 800 / 975 / 1150 |
| 27 | Ventnor Avenue | PROPERTY | YELLOW | $260 | $130 | $150 | 22 / 110 / 330 / 800 / 975 / 1150 |
| 28 | Water Works | UTILITY | - | $150 | $75 | - | 4x or 10x dice roll |
| 29 | Marvin Gardens | PROPERTY | YELLOW | $280 | $140 | $150 | 24 / 120 / 360 / 850 / 1025 / 1200 |
| 30 | Go To Jail | GO_TO_JAIL | - | - | - | - | Go directly to Jail |
| 31 | Pacific Avenue | PROPERTY | GREEN | $300 | $150 | $200 | 26 / 130 / 390 / 900 / 1100 / 1275 |
| 32 | North Carolina Avenue | PROPERTY | GREEN | $300 | $150 | $200 | 26 / 130 / 390 / 900 / 1100 / 1275 |
| 33 | Community Chest | COMMUNITY_CHEST | - | - | - | - | - |
| 34 | Pennsylvania Avenue | PROPERTY | GREEN | $320 | $160 | $200 | 28 / 150 / 450 / 1000 / 1200 / 1400 |
| 35 | Short Line Railroad | RAILROAD | - | $200 | $100 | - | 25 / 50 / 100 / 200 |
| 36 | Chance | CHANCE | - | - | - | - | - |
| 37 | Park Place | PROPERTY | DARK_BLUE | $350 | $175 | $200 | 35 / 175 / 500 / 1100 / 1300 / 1500 |
| 38 | Luxury Tax | TAX | - | - | - | - | Pay $100 |
| 39 | Boardwalk | PROPERTY | DARK_BLUE | $400 | $200 | $200 | 50 / 200 / 600 / 1400 / 1700 / 2000 |

**Rent Schedule Format**: base / 1 house / 2 houses / 3 houses / 4 houses / hotel

**Railroad Rent Schedule**: $25 (1 owned) / $50 (2 owned) / $100 (3 owned) / $200 (4 owned)

**Utility Rent**: 4x dice total (1 owned) or 10x dice total (2 owned)

**Monopoly Bonus**: Unimproved properties in a complete color group charge **2x base rent**.

---

## 7. Appendix: Enumerations

### SpaceType

```
GO, PROPERTY, COMMUNITY_CHEST, TAX, RAILROAD, CHANCE,
JAIL, UTILITY, FREE_PARKING, GO_TO_JAIL
```

### ColorGroup

```
BROWN, LIGHT_BLUE, PINK, ORANGE, RED, YELLOW, GREEN, DARK_BLUE
```

### GameStatus

```
setup, in_progress, paused, finished
```

### TurnPhase

```
PRE_ROLL, ROLL, LANDED, POST_ROLL, END_TURN
```

**Phase Flow**:
1. `PRE_ROLL` -- Agent may build houses, propose trades, or mortgage properties before rolling.
2. `ROLL` -- Dice are rolled and the player's token moves.
3. `LANDED` -- The landing space is processed (buy/auction, pay rent, draw card, go to jail, pay tax).
4. `POST_ROLL` -- Agent may build, trade, or mortgage after landing.
5. `END_TURN` -- Check for doubles (roll again) or third-doubles (jail). Advance to next player.

### JailAction

```
PAY_FINE      -- Pay $50 to the bank
USE_CARD      -- Use a Get Out of Jail Free card
ROLL_DOUBLES  -- Attempt to roll doubles (up to 3 tries across turns)
```

### CardEffectType

```
ADVANCE_TO, ADVANCE_TO_NEAREST, GO_BACK, COLLECT, PAY,
PAY_EACH_PLAYER, COLLECT_FROM_EACH, REPAIRS, GO_TO_JAIL, GET_OUT_OF_JAIL
```

### EventType

```
GAME_STARTED, TURN_STARTED, DICE_ROLLED, PLAYER_MOVED, PASSED_GO,
PROPERTY_PURCHASED, AUCTION_STARTED, AUCTION_BID, AUCTION_WON,
RENT_PAID, CARD_DRAWN, CARD_EFFECT, TAX_PAID,
HOUSE_BUILT, HOTEL_BUILT, BUILDING_SOLD,
PROPERTY_MORTGAGED, PROPERTY_UNMORTGAGED,
TRADE_PROPOSED, TRADE_ACCEPTED, TRADE_REJECTED,
PLAYER_JAILED, PLAYER_FREED, PLAYER_BANKRUPT,
AGENT_SPOKE, AGENT_THOUGHT,
GAME_OVER
```

### Default Agent Configurations

| Slot | Name | Model | Personality | Avatar | Color |
|------|------|-------|-------------|--------|-------|
| 0 | The Shark | gpt-4o | aggressive | shark | #EF4444 |
| 1 | The Professor | gemini-pro | analytical | professor | #3B82F6 |
| 2 | The Hustler | gpt-4o-mini | charismatic | hustler | #F59E0B |
| 3 | The Turtle | gemini-flash | conservative | turtle | #10B981 |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial API specification covering all REST endpoints, WebSocket protocol, data models, and error codes. |
