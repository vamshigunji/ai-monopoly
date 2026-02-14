# CRITICAL BUG REPORT: Game State 404 Error

## Summary
**Severity**: CRITICAL
**Component**: Backend API - Game Storage
**Impact**: Games become inaccessible (404) shortly after creation, making gameplay monitoring impossible

## Issue Description
When a game is created via `POST /api/game/start`, it successfully returns a `game_id` and initial game state. However, subsequent requests to `GET /api/game/{game_id}/state` consistently return `404 Not Found`, even though:
- The game was successfully created
- The backend confirms it's healthy
- The game appears to be progressing (turns incrementing from 0 to 35 in testing)

## Reproduction Steps
1. Start backend server (confirmed running at `http://localhost:8000`)
2. Create a new game:
   ```bash
   POST http://localhost:8000/api/game/start
   Body: {"seed": 12345}
   ```
3. Note the returned `game_id` (e.g., `446ea3b0-545a-4bac-b30f-099903bcf182`)
4. Immediately attempt to fetch game state:
   ```bash
   GET http://localhost:8000/api/game/{game_id}/state
   ```
5. Observe 404 error response

## Test Results

### Test Run #1
- **Game ID**: `446ea3b0-545a-4bac-b30f-099903bcf182`
- **Duration**: 15 minutes (900 seconds)
- **Turns Completed**: 0
- **Errors**: 89 consecutive 404 errors on state endpoint
- **Outcome**: Test timed out, game never accessible

### Test Run #2
- **Game ID**: `6314cf8f-4d90-47cf-a73e-8844779a669e`
- **Duration**: 15 minutes (901 seconds)
- **Turns Completed**: 35 (!)
- **Errors**: 75 consecutive 404 errors on state endpoint
- **Observation**: Despite 404 errors, turn counter incremented, suggesting game IS running but storage access is failing

### Diagnostic Test
- Created game: `2257b146-2639-4674-8a9f-15c9d0152450`
- **Immediate state check**: SUCCESS (200 OK)
- **After 1s**: SUCCESS (200 OK)
- **Conclusion**: Issue is intermittent or timing-related

## Root Cause Analysis

### Likely Causes (In Order of Probability):

1. **Race Condition in Game Storage**
   - Game is added to storage in `routes.py:185`
   - Background task starts immediately at `routes.py:199`
   - If background task crashes or completes extremely fast, game may be lost
   - No error handling wraps the `asyncio.create_task()` call

2. **Uncaught Exception in Background Task**
   - `game_runner.run_game()` re-raises exceptions at `game_runner.py:257`
   - Uncaught exceptions in background tasks fail silently
   - Game object may be garbage collected when task fails

3. **Game Runner State Issue**
   - `game_storage` is a global singleton (`storage.py:171`)
   - No thread-safety mechanisms
   - Possible corruption during concurrent access

4. **Missing Error Logging**
   - No try/except wrapper around `asyncio.create_task(game_runner.run_game())`
   - Errors in background task are not logged or reported
   - Silent failures prevent diagnosis

## Code References

### /Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend/src/monopoly/api/routes.py:184-199
```python
# Store game runner
game_storage.add_game(game_id, game_runner, event_bus)

# Set up event history listener
event_history = game_storage.get_event_history(game_id)

async def history_listener(event: Any) -> None:
    """Add events to history."""
    if event_history:
        event_history.add_event(event, game_runner.game.turn_number)

await event_bus.subscribe("*", history_listener)

# Start game loop in background
import asyncio
asyncio.create_task(game_runner.run_game())  # ← NO ERROR HANDLING
```

### /Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend/src/monopoly/orchestrator/game_runner.py:254-257
```python
except Exception as e:
    logger.error(f"Game loop error: {e}", exc_info=True)
    self._emit_event(EventType.GAME_OVER, data={"reason": "error", "error": str(e)})
    raise  # ← Re-raises exception, killing background task
```

## Impact Assessment

### User Impact: CRITICAL
- Users cannot monitor game progression
- No way to observe game state, events, or outcomes
- Frontend cannot display live game updates
- Completely breaks the core user experience

### Testing Impact: CRITICAL
- Full game playthrough testing impossible
- Cannot verify game logic correctness
- Cannot observe event generation
- Blocks all integration testing

### Development Impact: HIGH
- Debugging gameplay issues is impossible
- Cannot validate AI agent behavior
- Event bus effectiveness cannot be measured

## Recommended Fixes

### Immediate Fix (Priority 1)
Add error handling to background task in `routes.py`:

```python
async def run_game_with_error_handling():
    try:
        await game_runner.run_game()
    except Exception as e:
        logger.error(f"Game {game_id} failed: {e}", exc_info=True)
        # Keep game in storage for post-mortem analysis
        # Could add a "failed" status flag

asyncio.create_task(run_game_with_error_handling())
```

### Secondary Fix (Priority 2)
Add game state validation and logging in `get_game_state` endpoint:

```python
@router.get("/game/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: str) -> Any:
    logger.info(f"State request for game {game_id}")
    logger.debug(f"Active games: {game_storage.list_games()}")

    game_runner = game_storage.get_game(game_id)
    if not game_runner:
        logger.warning(f"Game {game_id} not found in storage")
        # ... existing 404 response
```

### Long-term Fix (Priority 3)
1. Add game status field (`running`, `completed`, `failed`, `abandoned`)
2. Implement proper cleanup/archival for completed games
3. Add thread-safe access to game storage
4. Store game results even after completion
5. Implement game recovery from checkpoints

## Next Steps

1. Add comprehensive logging to diagnose where games disappear
2. Implement fix #1 to prevent silent background task failures
3. Re-run full playthrough test to verify fix
4. Add backend integration test for game state persistence
5. Monitor logs for any remaining storage issues

## Test Artifacts

- Full test script: `/Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend/test_full_playthrough.py`
- Test report: `/Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend/TEST_PLAYTHROUGH_REPORT.md`
- Diagnostic script: `/Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend/test_game_creation.py`

## Additional Notes

- Issue does NOT affect health endpoint (`/health` always returns 200 OK)
- Backend process remains stable (no crashes)
- Individual game creation succeeds (returns valid `game_id`)
- Events endpoint (`/api/game/{game_id}/events`) also returns 404
- No `/api/games` list endpoint exists to enumerate active games

---

**Discovered by**: QA Tester (Task #3 - Full Game Playthrough Test)
**Date**: 2026-02-11
**Test Duration**: 2 failed attempts over 30 minutes
