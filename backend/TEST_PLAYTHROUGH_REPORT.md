# Full Game Playthrough Test Report

## Test Overview
- **Test Date**: 2026-02-11 19:14:57
- **Game ID**: f385842b-c2c8-4f1a-90a8-632b45ad224e
- **Duration**: 410.5 seconds (6.8 minutes)
- **Turns Completed**: 101
- **Final Status**: in_progress

## Test Results

### Game Completion
- ⚠ **Game did not complete** (status: in_progress)

### Final Player Standings

| Rank | Player | Money | Properties | Status |
|------|--------|-------|------------|--------|
| 1 | Player1 | $0 | 5 | active |
| 2 | Player2 | $0 | 6 | active |
| 3 | Player3 | $0 | 6 | active |
| 4 | Player4 | $0 | 7 | active |

### Event Types Captured

_No events captured_

### Errors (0)

✓ No errors detected

### Warnings (3)

- ⚠ Reached maximum turn limit (100)
- ⚠ Failed to get events: 404 Client Error: Not Found for url: http://localhost:8000/api/game/f385842b-c2c8-4f1a-90a8-632b45ad224e/events
- ⚠ No events retrieved

## Performance Observations

- **Turns per minute**: 14.8
- **Average time per turn**: 4.06s
- **Total state checks**: 42

## Recommendations

- ⚠ **Game did not complete naturally** - investigate why game ended prematurely or didn't finish within time limit
- ⚠ **3 warnings** - investigate potential issues
- ⚠ **No events captured** - verify event logging is working

## Test Configuration

- **Base URL**: http://localhost:8000
- **Poll Interval**: 10s
- **Max Duration**: 15 minutes
- **Max Turns**: 100
- **Game Seed**: 12345
