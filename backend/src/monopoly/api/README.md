# Monopoly AI Agents API

FastAPI application for the Monopoly AI Agents backend.

## Overview

This API provides:
- REST endpoints for game management (start, pause, resume, speed control)
- WebSocket endpoint for real-time game event streaming
- Complete game state and history access

## Running the Server

### Development Mode

```bash
# From the backend directory
uvicorn monopoly.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn monopoly.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### REST API

All REST endpoints are prefixed with `/api`.

- `POST /api/game/start` - Start a new game with 4 AI agents
- `GET /api/game/{game_id}/state` - Get complete current game state
- `GET /api/game/{game_id}/history` - Get event history with filtering
- `POST /api/game/{game_id}/pause` - Pause a running game
- `POST /api/game/{game_id}/resume` - Resume a paused game
- `POST /api/game/{game_id}/speed` - Change game speed
- `GET /api/game/{game_id}/agents` - Get agent information

### WebSocket

- `WS /ws/game/{game_id}` - Real-time event stream

## Example Usage

### Start a New Game

```bash
curl -X POST http://localhost:8000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{
    "num_players": 4,
    "seed": 42,
    "speed": 1.0
  }'
```

Response:
```json
{
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "players": [...],
  "status": "in_progress",
  "seed": 42,
  "created_at": "2026-02-11T14:30:00Z"
}
```

### Get Game State

```bash
curl http://localhost:8000/api/game/{game_id}/state
```

### Connect WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/game/{game_id}');

ws.onmessage = (event) => {
  const gameEvent = JSON.parse(event.data);
  console.log('Event:', gameEvent.event, gameEvent.data);
};

// Send control messages
ws.send(JSON.stringify({ action: 'pause' }));
ws.send(JSON.stringify({ action: 'set_speed', data: { speed: 2.0 } }));
```

## Architecture

```
monopoly/api/
├── __init__.py          # Package initialization
├── main.py              # FastAPI app, CORS, lifespan
├── routes.py            # REST endpoints
├── websocket.py         # WebSocket endpoint
├── models.py            # Pydantic request/response models
└── storage.py           # In-memory game storage
```

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://127.0.0.1:3000`

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Human-readable error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

Common error codes:
- `GAME_NOT_FOUND` (404)
- `INVALID_PLAYER_COUNT` (400)
- `INVALID_AGENT_CONFIG` (400)
- `INVALID_SPEED` (400)
- `GAME_NOT_RUNNING` (409)
- `GAME_NOT_PAUSED` (409)
- `GAME_CREATION_FAILED` (500)

## Dependencies

Required packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `websockets` - WebSocket support (included with FastAPI)

## Notes

- Games are stored in memory (not persisted to disk)
- Multiple WebSocket clients can connect to the same game
- Event history is maintained per game with sequence numbers
- Game loop runs in background asyncio tasks
