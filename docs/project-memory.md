# Monopoly AI Agents — Project Memory & Context

This file preserves full project context so any Claude Code session can pick up where the last one left off.

---

## 1. Project Vision

Build a fully functional Monopoly game where 4 AI agents (powered by different LLMs with distinct personalities) play against each other. The primary goal is to observe how different AI personalities negotiate, strategize, and make decisions. Each agent has:
- **Public context**: Table-talk negotiations visible to all agents and the audience
- **Private context**: Internal reasoning and personality-driven strategy (visible only in debug UI)

No human players — AI agents only.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / FastAPI / Uvicorn / Pydantic / WebSockets |
| Frontend | Next.js / React / TypeScript / Tailwind CSS / Zustand |
| LLM (OpenAI) | GPT-4o (Shark), GPT-4o-mini (Hustler) |
| LLM (Google) | Gemini 1.5 Pro (Professor), Gemini 1.5 Flash (Turtle) |
| Testing | pytest / pytest-asyncio / pytest-cov (899 tests passing) |
| Linting | ruff (100 char line length, Python 3.11 target) |

---

## 3. Project Structure

```
monopoly-agents/
├── backend/
│   ├── pyproject.toml
│   ├── src/monopoly/
│   │   ├── engine/          # COMPLETE (Sprint 1)
│   │   │   ├── types.py     # 15+ classes: enums, dataclasses, events
│   │   │   ├── board.py     # 40 spaces, property data, color groups
│   │   │   ├── dice.py      # Injectable RNG via seed
│   │   │   ├── player.py    # Mutable player state
│   │   │   ├── cards.py     # 16 Chance + 16 CC cards, deck logic
│   │   │   ├── bank.py      # 32 houses, 12 hotels, shortage tracking
│   │   │   ├── rules.py     # Rent, even-build, mortgage, trade validation
│   │   │   ├── trade.py     # Trade execution with mortgaged property fees
│   │   │   └── game.py      # ~590 line state machine, all turn phases
│   │   ├── agents/          # COMPLETE (Sprint 2)
│   │   │   ├── base.py      # AgentInterface ABC, GameView, action types
│   │   │   ├── openai_agent.py  # OpenAI GPT adapter (all 8 decisions)
│   │   │   ├── gemini_agent.py  # Gemini adapter (all 8 decisions)
│   │   │   ├── personalities.py # 4 personality configs + prompts
│   │   │   ├── random_agent.py  # Fallback agent for LLM failures
│   │   │   └── context.py   # Public/private context with sliding window
│   │   ├── orchestrator/    # NOT STARTED (Sprint 3)
│   │   │   ├── event_bus.py
│   │   │   ├── turn_manager.py
│   │   │   └── game_runner.py
│   │   └── api/             # NOT STARTED (Sprint 3)
│   │       ├── main.py
│   │       ├── routes.py
│   │       └── websocket.py
│   └── tests/
│       ├── conftest.py      # Shared fixtures
│       ├── engine/          # 808 tests, all passing
│       │   ├── test_board.py
│       │   ├── test_dice.py
│       │   ├── test_player.py
│       │   ├── test_cards.py
│       │   ├── test_bank.py
│       │   ├── test_rules.py
│       │   ├── test_trade.py
│       │   └── test_game.py
│       └── agents/          # 72 tests, all passing (Sprint 2)
│           ├── test_context.py
│           ├── test_random_agent.py
│           ├── test_openai_agent.py   # Mock LLM tests
│           └── test_gemini_agent.py   # Mock LLM tests
├── frontend/                # NOT STARTED (Sprint 4)
├── docs/
│   ├── game-rules-reference.md   # Complete Monopoly rules (863 lines)
│   ├── sprint-plan.md            # 5-sprint implementation plan (573 lines)
│   ├── architecture.md           # System architecture (1,056 lines)
│   ├── api-specification.md      # REST + WebSocket API (1,799 lines)
│   ├── agent-design.md           # Agent system design (1,789 lines)
│   ├── data-models.md            # All data types reference (1,192 lines)
│   └── project-memory.md         # THIS FILE
├── .env                          # API keys (gitignored)
├── .env.example
└── .gitignore
```

---

## 4. Sprint Plan & Status

### Sprint 1: Foundation (COMPLETE)
- [x] Repository scaffolding
- [x] `docs/game-rules-reference.md`
- [x] All engine tests written first (TDD)
- [x] `engine/types.py`, `board.py`, `dice.py`
- [x] `engine/player.py`, `cards.py`, `bank.py`
- [x] `engine/rules.py`, `trade.py`
- [x] `engine/game.py`
- [x] All 808 engine tests passing
- [x] All 6 documentation files

### Sprint 2: AI Agent System (COMPLETE)
- [x] `agents/base.py` — AgentInterface ABC + GameView + action dataclasses
- [x] `agents/context.py` — Public/private context manager with sliding window
- [x] `agents/personalities.py` — 4 personality configs + system prompt templates
- [x] `agents/openai_agent.py` — OpenAI GPT adapter with function calling (all 8 decisions)
- [x] `agents/gemini_agent.py` — Gemini adapter with structured output (all 8 decisions)
- [x] `agents/random_agent.py` — Fallback agent for LLM failures
- [x] Agent tests with mock LLM responses (72 tests)
- [x] All 899 tests passing (808 engine + 72 agents + 19 other)

### Sprint 3: Orchestrator + API (NEXT)
- [ ] `orchestrator/event_bus.py`
- [ ] `orchestrator/turn_manager.py`
- [ ] `orchestrator/game_runner.py`
- [ ] `api/main.py`, `api/routes.py`, `api/websocket.py`
- [ ] Integration test: full game with mock agents via API

### Sprint 4: Frontend
- [ ] Next.js scaffold with Tailwind
- [ ] WebSocket hook + Zustand store
- [ ] GameBoard component (simplified CSS grid)
- [ ] AgentCard, ConversationPanel, ThoughtPanel
- [ ] GameLog, GameControls, DiceDisplay
- [ ] **Line graph: dual-axis (cash dashed + net worth solid) per player over turns** (Recharts)

### Sprint 5: Integration & Polish
- [ ] End-to-end testing with real LLM agents
- [ ] Personality prompt tuning
- [ ] Speed controls and game replay
- [ ] Error handling and edge cases

---

## 5. Four Agent Personalities

| Slot | Name | Model | Temp | Personality | Color |
|------|------|-------|------|-------------|-------|
| 0 | The Shark | GPT-4o | 0.7 | Aggressive negotiator, buys everything, builds fast | #EF4444 |
| 1 | The Professor | Gemini Pro | 0.3 | Analytical strategist, calculates expected values | #3B82F6 |
| 2 | The Hustler | GPT-4o-mini | 1.0 | Charismatic bluffer, high trade volume, unpredictable | #F59E0B |
| 3 | The Turtle | Gemini Flash | 0.2 | Conservative hoarder, rarely trades, outlasts opponents | #10B981 |

---

## 6. Key Design Decisions

1. **Pure game engine with zero I/O** — engine/ has no network, no async, no LLM calls. All randomness injectable via seed.
2. **Event-sourced architecture** — All state mutations emit GameEvent to append-only list. Enables replay, debugging, frontend sync.
3. **Injectable RNG** — `Dice(seed=42)` and `Deck(seed=42)` for deterministic testing.
4. **Separate agent interface** — AgentInterface ABC is the async boundary. Game engine is sync; agents are async.
5. **WebSocket for real-time** — Events stream from backend to frontend. REST for control (start/pause/speed).
6. **Frozen dataclasses for static data** — PropertyData, Space, DiceRoll etc. are immutable. Player, Bank, Game are mutable.

---

## 7. Additional Requirements (Not Yet Implemented)

### Line Graph (Sprint 4)
- **Dual-axis chart** for each player showing:
  - **Solid line**: Net worth (cash + property values + building values)
  - **Dashed line**: Cash only
- All 4 players on the same chart, color-coded by agent color
- X-axis: turn number, Y-axis: dollars
- Toggle to show/hide individual players or metrics
- **Backend**: Needs `TURN_ENDED` events with per-player financial snapshots
- **Frontend**: Recharts library

---

## 8. Known Issues & Fixes (from Sprint 1)

| Issue | Fix |
|-------|-----|
| `pyproject.toml` build-backend error | Changed to `"setuptools.build_meta"` |
| `board.py` imported non-existent `Board as BoardBase` from types.py | Removed the import |
| `test_bank.py` expected `MAX_HOTELS + 1` but `return_hotel()` caps at max | Changed assertion to `== MAX_HOTELS` |

---

## 9. How to Run

```bash
# Run all tests
cd /Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend
python3 -m pytest tests/ -v

# Expected: 899 passed in ~0.82s

# Run just engine tests
python3 -m pytest tests/engine/ -v   # 808 tests

# Run just agent tests
python3 -m pytest tests/agents/ -v   # 72 tests
```

---

## 10. API Keys

Stored in `/Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/.env` (gitignored):
- `OPENAI_API_KEY` — configured
- `GOOGLE_API_KEY` — configured

---

## 11. Plan File Location

Full implementation plan: `/Users/venkatavamshigunji/.claude/plans/greedy-riding-narwhal.md`
Copy in project: `/Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/docs/sprint-plan.md`
