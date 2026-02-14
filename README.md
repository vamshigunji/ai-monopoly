# 🎲 Monopoly AI Agents

Watch 4 AI agents with distinct personalities play Monopoly against each other! Each agent uses different LLM models and exhibits unique strategies, negotiation styles, and decision-making patterns.

## 🎮 Features

- **4 Unique AI Personalities:**
  - 🦈 **The Shark** (GPT-3.5-turbo) - Aggressive negotiator who buys everything
  - 🎓 **The Professor** (GPT-3.5-turbo) - Analytical strategist who calculates probabilities
  - 🎭 **The Hustler** (GPT-3.5-turbo) - Charismatic bluffer who makes lopsided deals
  - 🐢 **The Turtle** (GPT-3.5-turbo) - Conservative builder who hoards cash

- **Real-time Gameplay:**
  - Live WebSocket updates
  - Animated dice rolls
  - Moving player tokens
  - Rich event logs

- **Dual Context System:**
  - **Public Chat** - Agent negotiations visible to all
  - **Private Thoughts** - Internal strategy reasoning

- **Full Monopoly Rules:**
  - Complete board with all 40 spaces
  - Properties, railroads, utilities
  - Chance & Community Chest cards
  - Auctions, trading, mortgaging
  - Houses, hotels, and bankruptcies

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd monopoly-agents
```

2. **Backend Setup:**
```bash
cd backend

# Create virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Create .env file with your API key
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key-here
EOF

# Run backend
python -m uvicorn src.monopoly.api.main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Frontend Setup (in a new terminal):**
```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

4. **Open the game:**
```
http://localhost:3000
```

## 🎯 How to Play

1. Click **"Start New Game"**
2. Watch the AI agents play automatically
3. Use the controls:
   - ⏸️ **Pause/Resume** - Control game flow
   - 🎚️ **Speed** - Adjust game speed (0.5x to 5x)
   - 🔄 **New Game** - Start fresh

4. Explore the UI:
   - **Game Board** - See token positions and property ownership
   - **Agent Cards** - View each player's cash and properties
   - **Public Chat** - Read agent negotiations
   - **Private Thoughts** - Select an agent to see their strategy
   - **Asset Panel** - View detailed property information per player
   - **Game Log** - Filter and review all game events

## 🧪 Testing

### Run Backend Tests (899 tests)
```bash
cd backend
pytest tests/ -v
```

### Run End-to-End Test
```bash
cd backend
python test_game.py
```

This will verify:
- ✅ Backend is running
- ✅ Game creation works
- ✅ AI agents make decisions
- ✅ Tokens move on the board
- ✅ Financial transactions occur
- ✅ Events are generated

## 📊 Architecture

```
monopoly-agents/
├── backend/                 # Python FastAPI backend
│   ├── src/monopoly/
│   │   ├── engine/         # Pure game logic (no I/O)
│   │   ├── agents/         # AI agent implementations
│   │   ├── orchestrator/   # Game loop coordination
│   │   └── api/            # REST + WebSocket endpoints
│   └── tests/              # 899 unit & integration tests
│
└── frontend/               # Next.js 16 + React 18
    └── src/
        ├── components/     # Game UI components
        ├── hooks/          # WebSocket & state hooks
        └── stores/         # Zustand state management
```

## 🔧 Configuration

### Change AI Models

Edit `backend/src/monopoly/agents/personalities.py`:

```python
SHARK = PersonalityConfig(
    model="gpt-4o",  # Change to gpt-4o, gpt-3.5-turbo, etc.
    temperature=0.7,
    ...
)
```

### Adjust Personalities

Modify the prompt templates in `personalities.py` to change:
- Decision-making style
- Risk tolerance
- Negotiation tactics
- Speech patterns

## 📡 API Endpoints

### REST API
- `POST /api/game/start` - Start new game
- `GET /api/game/{id}/state` - Get current state
- `GET /api/game/{id}/history` - Get event history
- `POST /api/game/{id}/pause` - Pause game
- `POST /api/game/{id}/resume` - Resume game
- `POST /api/game/{id}/speed` - Set game speed

### WebSocket
- `WS /ws/game/{id}` - Real-time event stream

## 🎓 Sprint Status

- ✅ **Sprint 1**: Game Engine (899 tests passing)
- ✅ **Sprint 2**: AI Agents (4 personalities implemented)
- ✅ **Sprint 3**: Orchestrator + API (WebSocket streaming)
- ✅ **Sprint 4**: Frontend (All components built)
- ✅ **Sprint 5**: Integration & Polish (Complete)

## 💰 Cost Estimates

Using GPT-3.5-turbo for all agents:
- **~$0.02-0.05 per full game**
- Average game: 50-200 turns
- Each turn: 2-4 LLM calls

Using GPT-4o:
- **~$0.20-0.50 per game**

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (needs 3.11+)
- Verify API key is set in `.env`
- Check port 8000 isn't in use: `lsof -ti:8000`

### Frontend shows "Disconnected"
- Ensure backend is running on port 8000
- Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Check browser console for WebSocket errors

### Agents not making decisions
- Verify `OPENAI_API_KEY` is valid
- Check backend logs for API errors
- Run `test_game.py` to verify end-to-end functionality

## 📝 License

MIT

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [OpenAI API](https://platform.openai.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Zustand](https://github.com/pmndrs/zustand)
