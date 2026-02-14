# Monopoly AI Agents — Implementation Plan

## Context

Build a fully functional Monopoly game where 4 AI agents (powered by different LLMs with distinct personalities) play against each other. The goal is to observe how different AI personalities negotiate, strategize, and make decisions. Each agent has public context (table-talk negotiations visible to all) and private context (internal reasoning and personality-driven strategy).

**Tech Stack**: Python FastAPI backend + Next.js frontend + WebSockets
**LLM Providers**: OpenAI (GPT-4o, GPT-4o-mini) + Google Gemini (Pro, Flash)
**Players**: 4 AI agents only (no human players)
**UI Focus**: Simplified board + rich agent conversation/thought logs
**Methodology**: Test-Driven Development (TDD)

---

## Phase 0: Project Scaffolding & Game Rules Reference

### 0.1 — Repository Structure
```
monopoly-agents/
├── backend/
│   ├── pyproject.toml              # Python project config (poetry/uv)
│   ├── .env.example                # Template for API keys
│   ├── src/
│   │   └── monopoly/
│   │       ├── __init__.py
│   │       ├── engine/             # Pure game engine (no I/O)
│   │       │   ├── __init__.py
│   │       │   ├── board.py        # Board layout, 40 spaces
│   │       │   ├── property.py     # Property, Railroad, Utility models
│   │       │   ├── cards.py        # Chance & Community Chest decks
│   │       │   ├── bank.py         # Bank: money, houses, hotels
│   │       │   ├── player.py       # Player state
│   │       │   ├── dice.py         # Dice with injectable RNG
│   │       │   ├── rules.py        # Rule enforcement (even-build, housing shortage, etc.)
│   │       │   ├── game.py         # Game state machine & turn logic
│   │       │   ├── trade.py        # Trade proposal/acceptance logic
│   │       │   └── types.py        # Enums, dataclasses, type definitions
│   │       ├── agents/             # AI agent layer
│   │       │   ├── __init__.py
│   │       │   ├── base.py         # Abstract agent interface
│   │       │   ├── openai_agent.py # OpenAI GPT adapter
│   │       │   ├── gemini_agent.py # Google Gemini adapter
│   │       │   ├── personalities.py# Personality prompt templates
│   │       │   └── context.py      # Public/private context manager
│   │       ├── orchestrator/       # Game flow coordination
│   │       │   ├── __init__.py
│   │       │   ├── game_runner.py  # Main game loop
│   │       │   ├── turn_manager.py # Turn sequencing, phase management
│   │       │   └── event_bus.py    # Event system for broadcasting
│   │       └── api/                # FastAPI layer
│   │           ├── __init__.py
│   │           ├── main.py         # FastAPI app, CORS, lifespan
│   │           ├── routes.py       # REST endpoints (start game, get state)
│   │           └── websocket.py    # WebSocket handler for real-time updates
│   └── tests/
│       ├── conftest.py
│       ├── engine/                 # ~100+ unit tests for game rules
│       │   ├── test_board.py
│       │   ├── test_property.py
│       │   ├── test_cards.py
│       │   ├── test_bank.py
│       │   ├── test_player.py
│       │   ├── test_dice.py
│       │   ├── test_rules.py
│       │   ├── test_game.py
│       │   └── test_trade.py
│       ├── agents/
│       │   ├── test_context.py
│       │   └── test_agent_interface.py
│       ├── orchestrator/
│       │   └── test_game_runner.py
│       └── integration/
│           └── test_full_game.py
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Main game page
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── board/
│   │   │   │   ├── GameBoard.tsx       # Simplified Monopoly board
│   │   │   │   ├── BoardSpace.tsx      # Individual space rendering
│   │   │   │   └── PlayerToken.tsx     # Token on board
│   │   │   ├── agents/
│   │   │   │   ├── ConversationPanel.tsx  # Public agent chat
│   │   │   │   ├── ThoughtPanel.tsx       # Private agent reasoning
│   │   │   │   └── AgentCard.tsx          # Agent info (name, money, properties)
│   │   │   ├── game/
│   │   │   │   ├── GameLog.tsx         # Event stream
│   │   │   │   ├── GameControls.tsx    # Start, pause, speed
│   │   │   │   ├── DiceDisplay.tsx     # Dice roll visualization
│   │   │   │   └── TradeModal.tsx      # Trade visualization
│   │   │   └── ui/                     # Shared UI primitives
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts         # WebSocket connection
│   │   │   └── useGameState.ts         # Game state management
│   │   ├── lib/
│   │   │   └── types.ts               # Shared TypeScript types
│   │   └── stores/
│   │       └── gameStore.ts            # Zustand store for game state
│   └── __tests__/
│       └── components/
├── docs/
│   └── game-rules-reference.md     # Complete Monopoly rules reference
├── .gitignore
├── .env.example
└── README.md
```

### 0.2 — Environment Setup
- `.env` file (gitignored) with `OPENAI_API_KEY` and `GOOGLE_API_KEY`
- `.env.example` with placeholder values
- Python deps: `fastapi`, `uvicorn`, `websockets`, `openai`, `google-generativeai`, `pydantic`, `pytest`, `pytest-asyncio`
- Node deps: `next`, `react`, `tailwindcss`, `zustand`, `lucide-react`

### 0.3 — Game Rules Reference Document
Create `docs/game-rules-reference.md` containing the complete Monopoly ruleset that the engine must implement. This serves as the "spec" for TDD:

**Board (40 spaces in order):**
| # | Space | Type | Color | Price |
|---|-------|------|-------|-------|
| 0 | GO | Corner | - | - |
| 1 | Mediterranean Avenue | Property | Brown | $60 |
| 2 | Community Chest | Card | - | - |
| 3 | Baltic Avenue | Property | Brown | $60 |
| 4 | Income Tax | Tax | - | $200 |
| 5 | Reading Railroad | Railroad | - | $200 |
| 6 | Oriental Avenue | Property | Light Blue | $100 |
| 7 | Chance | Card | - | - |
| 8 | Vermont Avenue | Property | Light Blue | $100 |
| 9 | Connecticut Avenue | Property | Light Blue | $120 |
| 10 | Jail / Just Visiting | Corner | - | - |
| 11 | St. Charles Place | Property | Pink | $140 |
| 12 | Electric Company | Utility | - | $150 |
| 13 | States Avenue | Property | Pink | $140 |
| 14 | Virginia Avenue | Property | Pink | $160 |
| 15 | Pennsylvania Railroad | Railroad | - | $200 |
| 16 | St. James Place | Property | Orange | $180 |
| 17 | Community Chest | Card | - | - |
| 18 | Tennessee Avenue | Property | Orange | $180 |
| 19 | New York Avenue | Property | Orange | $200 |
| 20 | Free Parking | Corner | - | - |
| 21 | Kentucky Avenue | Property | Red | $220 |
| 22 | Chance | Card | - | - |
| 23 | Indiana Avenue | Property | Red | $220 |
| 24 | Illinois Avenue | Property | Red | $240 |
| 25 | B&O Railroad | Railroad | - | $200 |
| 26 | Atlantic Avenue | Property | Yellow | $260 |
| 27 | Ventnor Avenue | Property | Yellow | $260 |
| 28 | Water Works | Utility | - | $150 |
| 29 | Marvin Gardens | Property | Yellow | $280 |
| 30 | Go To Jail | Corner | - | - |
| 31 | Pacific Avenue | Property | Green | $300 |
| 32 | North Carolina Avenue | Property | Green | $300 |
| 33 | Community Chest | Card | - | - |
| 34 | Pennsylvania Avenue | Property | Green | $320 |
| 35 | Short Line Railroad | Railroad | - | $200 |
| 36 | Chance | Card | - | - |
| 37 | Park Place | Property | Dark Blue | $350 |
| 38 | Luxury Tax | Tax | - | $100 |
| 39 | Boardwalk | Property | Dark Blue | $400 |

**Complete property rent tables, all 16 Chance cards, all 16 Community Chest cards, and all edge-case rules** will be encoded in the reference doc (too large for plan, will be authored in Phase 0).

---

## Phase 1: Game Engine — Pure Logic (TDD)

> **Approach**: Write tests FIRST, then implement. The engine is a pure Python module with ZERO I/O, ZERO async, ZERO LLM calls. All randomness is injectable via seed.

### 1.1 — Data Models (`engine/types.py`)
- `SpaceType` enum: PROPERTY, RAILROAD, UTILITY, TAX, CHANCE, COMMUNITY_CHEST, GO, JAIL, FREE_PARKING, GO_TO_JAIL
- `ColorGroup` enum: BROWN, LIGHT_BLUE, PINK, ORANGE, RED, YELLOW, GREEN, DARK_BLUE
- `PropertyData` dataclass: name, price, mortgage_value, color_group, rent[0-5], house_cost
- `CardEffect` dataclass: description, effect_type, value, destination
- `PlayerState` dataclass: id, name, position, cash, properties, in_jail, jail_turns, get_out_of_jail_cards, is_bankrupt
- `GameState` dataclass: players, current_player_index, board, chance_deck, community_chest_deck, houses_available(32), hotels_available(12), turn_number

### 1.2 — Board (`engine/board.py`)
- `Board` class with all 40 spaces
- `get_space(position)` → space info
- `get_color_group(color)` → list of property positions
- `distance_to(from, to)` → spaces to travel (for "advance to" cards)

### 1.3 — Dice (`engine/dice.py`)
- `Dice(seed=None)` — injectable RNG for deterministic testing
- `roll()` → (die1, die2, is_doubles)

### 1.4 — Property System (`engine/property.py`)
- Calculate rent based on: unimproved, monopoly (2x), 1-4 houses, hotel
- Railroad rent: $25, $50, $100, $200 (based on count owned)
- Utility rent: 4x dice roll (1 owned), 10x dice roll (2 owned)
- Mortgage/unmortgage logic (unmortgage = mortgage_value + 10%)
- Even-build rule enforcement
- Housing shortage tracking

### 1.5 — Cards (`engine/cards.py`)
- All 16 Chance cards with effects
- All 16 Community Chest cards with effects
- Deck shuffling (with seed)
- "Get Out of Jail Free" card retention logic

### 1.6 — Bank (`engine/bank.py`)
- Starting money: $1500 per player (2x$500, 2x$100, 2x$50, 6x$20, 5x$10, 5x$5, 5x$1)
- House/hotel inventory (32 houses, 12 hotels)
- Property auction logic

### 1.7 — Rules Engine (`engine/rules.py`)
- `can_buy_property(player, space)` → bool
- `can_build_house(player, property)` → bool (even-build check)
- `can_build_hotel(player, property)` → bool
- `can_mortgage(player, property)` → bool
- `calculate_rent(property, dice_roll, owner)` → int
- `is_bankrupt(player)` → bool
- `validate_trade(trade_proposal)` → bool

### 1.8 — Game State Machine (`engine/game.py`)
Turn phases:
1. **PRE_ROLL**: Player may trade, mortgage, build before rolling
2. **ROLL**: Roll dice, move token
3. **LANDED**: Process landing (buy/auction, pay rent, draw card, go to jail, tax)
4. **POST_ROLL**: Player may trade, mortgage, build after landing
5. **END_TURN**: Check doubles (roll again or jail if 3rd), advance to next player

Key methods:
- `execute_turn(player_decisions)` → list of events
- `process_landing(player, space)` → required actions
- `execute_trade(proposal)` → success/failure
- `check_game_over()` → winner or None

### 1.9 — Trade System (`engine/trade.py`)
- `TradeProposal`: offering_player, receiving_player, offered_properties, requested_properties, offered_cash, requested_cash
- Validation: players own what they're offering, mortgaged property transfer rules (new owner pays 10% immediately, may unmortgage or keep mortgaged)

### Tests for Phase 1 (~100+ tests)
```
tests/engine/test_board.py       — Board layout correctness, all 40 spaces
tests/engine/test_dice.py        — Deterministic rolls, doubles detection
tests/engine/test_property.py    — All rent calculations, mortgage math
tests/engine/test_cards.py       — All card effects execute correctly
tests/engine/test_bank.py        — Money distribution, house inventory
tests/engine/test_rules.py       — Even-build, housing shortage, auction
tests/engine/test_game.py        — Turn flow, jail logic, bankruptcy, GO salary
tests/engine/test_trade.py       — Trade validation, mortgaged property transfers
```

---

## Phase 2: AI Agent System

### 2.1 — Agent Interface (`agents/base.py`)
```python
class AgentInterface(ABC):
    """Clean interface between game engine and LLM agents."""

    @abstractmethod
    async def decide_pre_roll(self, game_view: GameView) -> PreRollAction:
        """Buy houses, propose trades, mortgage — before rolling."""

    @abstractmethod
    async def decide_buy_or_auction(self, game_view: GameView, property: PropertyData) -> bool:
        """Buy the property you landed on, or let it go to auction?"""

    @abstractmethod
    async def decide_auction_bid(self, game_view: GameView, property: PropertyData, current_bid: int) -> int:
        """How much to bid in an auction (0 = pass)."""

    @abstractmethod
    async def decide_trade(self, game_view: GameView) -> Optional[TradeProposal]:
        """Propose a trade to another player."""

    @abstractmethod
    async def respond_to_trade(self, game_view: GameView, proposal: TradeProposal) -> bool:
        """Accept or reject a trade proposal."""

    @abstractmethod
    async def decide_jail_action(self, game_view: GameView) -> JailAction:
        """Pay $50, use card, or try to roll doubles."""

    @abstractmethod
    async def decide_post_roll(self, game_view: GameView) -> PostRollAction:
        """Actions after landing — build, mortgage, trade."""
```

`GameView` is a filtered view of `GameState` — shows only what the player can see (their own full state + public info about others).

### 2.2 — Context Manager (`agents/context.py`)
- **Public Context**: Append-only log of all agent "speech" — negotiations, reactions, taunts. Visible to all agents and the frontend.
- **Private Context**: Per-agent reasoning chain. Only visible in the UI when that agent's thought panel is selected. Includes: strategy assessment, property valuation, opponent modeling.
- Context window management: summarize older context to stay within LLM token limits.

### 2.3 — LLM Adapters
**`agents/openai_agent.py`**:
- Uses `openai` Python SDK
- System prompt: personality + Monopoly rules summary + current context
- Structured output via function calling for decisions
- Models: GPT-4o (for "smart" agents), GPT-4o-mini (for "impulsive" agents)

**`agents/gemini_agent.py`**:
- Uses `google-generativeai` SDK
- Same interface, different LLM backend
- Models: Gemini 1.5 Pro, Gemini 1.5 Flash

### 2.4 — Personalities (`agents/personalities.py`)
Four distinct agent personalities:

| Agent | Name | Model | Personality | Style |
|-------|------|-------|-------------|-------|
| 1 | "The Shark" | GPT-4o | Aggressive negotiator | Buys everything, trades ruthlessly, intimidates |
| 2 | "The Professor" | Gemini Pro | Analytical strategist | Calculates expected values, methodical building |
| 3 | "The Hustler" | GPT-4o-mini | Charismatic bluffer | Makes lopsided trade offers sound great, unpredictable |
| 4 | "The Turtle" | Gemini Flash | Conservative builder | Hoards cash, avoids risk, builds only with full monopolies |

Each personality is a system prompt template with:
- Character description and motivation
- Decision-making style
- Negotiation tactics
- Speech patterns (how they talk in public context)
- Risk tolerance parameters

### Tests for Phase 2
```
tests/agents/test_context.py           — Public/private context separation
tests/agents/test_agent_interface.py   — Mock agent makes valid decisions
```

---

## Phase 3: Game Orchestrator

### 3.1 — Event Bus (`orchestrator/event_bus.py`)
All game state changes emit events for the frontend:
- `GameStarted`, `TurnStarted`, `DiceRolled`, `PlayerMoved`
- `PropertyPurchased`, `RentPaid`, `CardDrawn`, `CardEffect`
- `TradeProposed`, `TradeAccepted`, `TradeRejected`
- `HouseBuilt`, `HotelBuilt`, `PropertyMortgaged`
- `PlayerJailed`, `PlayerFreed`, `PlayerBankrupt`
- `AgentSpoke` (public), `AgentThought` (private)
- `AuctionStarted`, `AuctionBid`, `AuctionWon`
- `GameOver`

### 3.2 — Game Runner (`orchestrator/game_runner.py`)
```python
class GameRunner:
    """Orchestrates a full Monopoly game."""

    def __init__(self, agents: list[AgentInterface], seed: int = None):
        self.game = Game(num_players=4, seed=seed)
        self.agents = agents
        self.event_bus = EventBus()

    async def run_game(self, max_turns: int = 1000):
        """Main game loop."""
        while not self.game.is_over() and self.game.turn_number < max_turns:
            await self.run_turn()

    async def run_turn(self):
        """Execute one player's complete turn."""
        player = self.game.current_player
        agent = self.agents[player.id]

        # Pre-roll phase (build, trade, mortgage)
        pre_roll = await agent.decide_pre_roll(self.game.get_view(player.id))
        self.game.execute_pre_roll(pre_roll)

        # Roll and move
        roll = self.game.roll_dice()
        self.event_bus.emit(DiceRolled(player.id, roll))
        self.game.move_player(player.id, roll.total)

        # Process landing
        landing_action = self.game.process_landing(player.id)
        if landing_action.requires_decision:
            decision = await agent.decide(landing_action)
            self.game.apply_decision(player.id, decision)

        # Post-roll phase
        post_roll = await agent.decide_post_roll(self.game.get_view(player.id))
        self.game.execute_post_roll(post_roll)

        # Advance turn (handle doubles)
        self.game.end_turn()
```

### 3.3 — Turn Manager (`orchestrator/turn_manager.py`)
- Handles doubles (roll again, max 3 before jail)
- Manages negotiation rounds between agents during trade proposals
- Enforces time limits on agent decisions (prevent infinite LLM loops)
- Handles bankruptcy resolution (selling assets, mortgaging, giving up)

### Tests for Phase 3
```
tests/orchestrator/test_game_runner.py  — Full game with mock agents
tests/integration/test_full_game.py    — End-to-end with real LLM calls (optional, slow)
```

---

## Phase 4: API Layer

### 4.1 — REST Endpoints (`api/routes.py`)
```
POST /api/game/start          — Start a new game (returns game_id)
GET  /api/game/{id}/state     — Get current game state
GET  /api/game/{id}/history   — Get event history
POST /api/game/{id}/pause     — Pause game
POST /api/game/{id}/resume    — Resume game
POST /api/game/{id}/speed     — Set game speed (delay between turns)
GET  /api/game/{id}/agents    — Get agent info (names, personalities)
```

### 4.2 — WebSocket (`api/websocket.py`)
```
WS /ws/game/{id}
```
Streams events in real-time:
```json
{
  "event": "dice_rolled",
  "data": {"player_id": 0, "die1": 4, "die2": 3, "doubles": false},
  "timestamp": "2026-02-11T12:00:00Z"
}
{
  "event": "agent_spoke",
  "data": {"player_id": 1, "message": "I'll give you Baltic for Oriental + $50. Deal?"},
  "timestamp": "2026-02-11T12:00:01Z"
}
{
  "event": "agent_thought",
  "data": {"player_id": 1, "thought": "Baltic is worth less, but I need the brown monopoly..."},
  "timestamp": "2026-02-11T12:00:01Z"
}
```

---

## Phase 5: Frontend

### 5.1 — Layout
```
┌─────────────────────────────────────────────────────────┐
│  Monopoly AI Agents                    [Speed ▾] [⏸]    │
├──────────────────────┬──────────────────────────────────┤
│                      │  Agent Panels (4 cards)          │
│   Simplified Board   │  ┌──────┐┌──────┐┌──────┐┌────┐│
│   (visual grid)      │  │Shark ││Prof  ││Hustlr││Trtl││
│   with tokens        │  │$1200 ││$1500 ││$800  ││$2k ││
│                      │  │4 prop││3 prop││6 prop││2 pr││
│                      │  └──────┘└──────┘└──────┘└────┘│
│                      ├──────────────────────────────────┤
│                      │  Public Chat (negotiations)      │
│   [Dice: 4+3=7]     │  🦈 "Give me Park Place or else" │
│                      │  🐢 "No deal. Too risky."        │
│                      │  🎭 "I'll sweeten the deal..."   │
│                      ├──────────────────────────────────┤
│                      │  Private Thoughts [Agent ▾]      │
│                      │  "Park Place + Boardwalk = win.  │
│                      │   I need to trade aggressively." │
├──────────────────────┴──────────────────────────────────┤
│  Game Log: Turn 42 | Shark rolled 7, landed on         │
│  Virginia Ave (owned by Professor), paid $18 rent       │
└─────────────────────────────────────────────────────────┘
```

### 5.2 — Key Components
- **GameBoard.tsx**: CSS Grid based board, color-coded properties, token positions
- **ConversationPanel.tsx**: Scrollable chat-style feed of agent public speech
- **ThoughtPanel.tsx**: Dropdown to select agent, shows their private reasoning
- **AgentCard.tsx**: Money, property count, personality badge, status
- **GameLog.tsx**: Chronological event stream with filtering
- **GameControls.tsx**: Start new game, pause/resume, speed slider (0.5x to 5x)

### 5.3 — State Management
- **Zustand store** (`gameStore.ts`): holds full game state received via WebSocket
- **useWebSocket hook**: connects to backend, dispatches events to store
- All state flows one-way: Backend → WebSocket → Store → Components

---

## Phase 6: Integration & Polish

- End-to-end testing with 4 real LLM agents
- Game speed tuning (configurable delay between turns)
- Error handling for LLM failures (retry with backoff, fallback to random valid move)
- Game replay from event history
- Conversation quality tuning (better personality prompts)

---

## Implementation Order (Sprint Plan)

### Sprint 1: Foundation (Engine + Tests) ← START HERE
1. Scaffold repo (backend + frontend directories, configs, .env)
2. Write `docs/game-rules-reference.md` (complete Monopoly rules)
3. Write ALL engine tests first (TDD red phase)
4. Implement `engine/types.py`, `engine/board.py`, `engine/dice.py`
5. Implement `engine/property.py`, `engine/cards.py`, `engine/bank.py`
6. Implement `engine/rules.py`, `engine/trade.py`
7. Implement `engine/game.py` (all tests green)

### Sprint 2: Agents
8. Implement `agents/base.py` (interface)
9. Implement `agents/context.py` (public/private separation)
10. Implement `agents/openai_agent.py` + `agents/gemini_agent.py`
11. Implement `agents/personalities.py` (4 personalities)
12. Write agent tests with mock LLM responses

### Sprint 3: Orchestrator + API
13. Implement `orchestrator/event_bus.py`
14. Implement `orchestrator/turn_manager.py`
15. Implement `orchestrator/game_runner.py`
16. Implement `api/main.py`, `api/routes.py`, `api/websocket.py`
17. Integration test: run a full game with real agents via API

### Sprint 4: Frontend
18. Scaffold Next.js app with Tailwind
19. Implement WebSocket hook + Zustand store
20. Build GameBoard component
21. Build AgentCard, ConversationPanel, ThoughtPanel
22. Build GameLog, GameControls, DiceDisplay
23. Wire everything together

### Sprint 5: Integration & Polish
24. End-to-end testing with real LLM agents
25. Personality prompt tuning
26. Speed controls and game replay
27. Error handling and edge cases
28. Final testing and documentation

---

## Verification Plan

### How to test the game engine:
```bash
cd backend && pytest tests/engine/ -v
```
All ~100+ unit tests must pass covering every Monopoly rule.

### How to test agents:
```bash
cd backend && pytest tests/agents/ -v
```
Mock-based tests verify agents return valid decisions.

### How to test integration:
```bash
cd backend && pytest tests/integration/ -v
```
Full game simulation with mock agents.

### How to run the full system:
```bash
# Terminal 1: Backend
cd backend && uvicorn src.monopoly.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```
Open `http://localhost:3000`, click "Start Game", watch agents play.

### What to verify visually:
1. Agents take turns, dice roll correctly
2. Properties are bought/auctioned
3. Rent is collected correctly
4. Agent conversations appear in chat panel
5. Private thoughts show strategy reasoning
6. Trades happen between agents with negotiation
7. Game ends when one player remains
