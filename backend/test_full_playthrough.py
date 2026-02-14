#!/usr/bin/env python3
"""
Full Game Playthrough Test
Tests a complete Monopoly game from start to finish
"""
import requests
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 10  # seconds
MAX_DURATION = 15 * 60  # 15 minutes
MAX_TURNS = 100  # Safety limit

class GamePlaythroughTest:
    def __init__(self):
        self.game_id = None
        self.start_time = None
        self.end_time = None
        self.turns_completed = 0
        self.errors = []
        self.warnings = []
        self.event_types = defaultdict(int)
        self.game_states = []
        self.final_state = None

    def start_game(self):
        """Create a new game with a seed for reproducibility"""
        print("Creating new game...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/game/start",
                json={"seed": 12345},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.game_id = data.get("game_id")
            print(f"✓ Game created: {self.game_id}")
            return True
        except Exception as e:
            self.errors.append(f"Failed to start game: {e}")
            print(f"✗ Failed to start game: {e}")
            return False

    def get_game_state(self):
        """Fetch current game state"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/game/{self.game_id}/state",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.errors.append(f"Failed to get game state: {e}")
            return None

    def get_game_events(self):
        """Fetch game events from history endpoint"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/game/{self.game_id}/history",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            # History endpoint returns {"events": [...], "total_events": N, "has_more": bool}
            return data.get("events", [])
        except Exception as e:
            self.warnings.append(f"Failed to get event history: {e}")
            return []

    def monitor_game(self):
        """Monitor game until completion or timeout"""
        print(f"\nMonitoring game for up to {MAX_DURATION/60:.0f} minutes or {MAX_TURNS} turns...")
        print("=" * 60)

        self.start_time = datetime.now()
        last_turn = -1
        consecutive_same_turns = 0

        while True:
            # Check timeout
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > MAX_DURATION:
                self.warnings.append(f"Test timed out after {MAX_DURATION/60:.0f} minutes")
                print(f"\n⚠ Test timed out after {elapsed:.0f} seconds")
                break

            # Get game state
            state = self.get_game_state()
            if not state:
                print("✗ Failed to get game state, retrying...")
                time.sleep(POLL_INTERVAL)
                continue

            # Store state snapshot
            self.game_states.append({
                "timestamp": datetime.now().isoformat(),
                "turn": state.get("turn_number", 0),
                "status": state.get("status", "unknown")
            })

            current_turn = state.get("turn_number", 0)
            status = state.get("status", "unknown")

            # Check for turn progression
            if current_turn == last_turn:
                consecutive_same_turns += 1
                if consecutive_same_turns > 10:
                    self.errors.append(f"Game stuck at turn {current_turn} for {consecutive_same_turns * POLL_INTERVAL} seconds")
                    print(f"\n✗ Game appears stuck at turn {current_turn}")
                    break
            else:
                consecutive_same_turns = 0
                last_turn = current_turn
                self.turns_completed = current_turn

            # Print progress
            print(f"[{elapsed:6.0f}s] Turn {current_turn:3d} | Status: {status:12s} | Players: {len(state.get('players', []))}", end="\r")

            # Check if game completed
            if status in ["completed", "finished"]:
                self.final_state = state
                print(f"\n✓ Game completed at turn {current_turn}")
                break

            # Check turn limit
            if current_turn >= MAX_TURNS:
                self.warnings.append(f"Reached maximum turn limit ({MAX_TURNS})")
                self.final_state = state
                print(f"\n⚠ Reached turn limit ({MAX_TURNS})")
                break

            # Wait before next check
            time.sleep(POLL_INTERVAL)

        self.end_time = datetime.now()

    def analyze_events(self):
        """Analyze game events"""
        print("\n\nAnalyzing game events...")
        events = self.get_game_events()

        if events:
            for event in events:
                event_type = event.get("type", "unknown")
                self.event_types[event_type] += 1

            print(f"✓ Collected {len(events)} events")
        else:
            self.warnings.append("No events retrieved")

    def generate_report(self):
        """Generate comprehensive test report"""
        duration = (self.end_time - self.start_time).total_seconds()

        report = f"""# Full Game Playthrough Test Report

## Test Overview
- **Test Date**: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
- **Game ID**: {self.game_id}
- **Duration**: {duration:.1f} seconds ({duration/60:.1f} minutes)
- **Turns Completed**: {self.turns_completed}
- **Final Status**: {self.final_state.get('status', 'N/A') if self.final_state else 'N/A'}

## Test Results

### Game Completion
"""

        if self.final_state:
            status = self.final_state.get("status", "unknown")
            if status in ["completed", "finished"]:
                winner = self.final_state.get("winner")
                report += f"- ✓ **Game completed successfully**\n"
                report += f"- **Winner**: {winner if winner else 'Not declared'}\n"
            else:
                report += f"- ⚠ **Game did not complete** (status: {status})\n"
        else:
            report += "- ✗ **No final state captured**\n"

        # Player standings
        if self.final_state and "players" in self.final_state:
            report += f"\n### Final Player Standings\n\n"
            players = self.final_state["players"]
            # Sort by money if available
            sorted_players = sorted(
                players,
                key=lambda p: p.get("money", 0),
                reverse=True
            )

            report += "| Rank | Player | Money | Properties | Status |\n"
            report += "|------|--------|-------|------------|--------|\n"
            for i, player in enumerate(sorted_players, 1):
                name = player.get("name", "Unknown")
                money = player.get("money", 0)
                props = len(player.get("properties", []))
                status = player.get("status", "active")
                report += f"| {i} | {name} | ${money} | {props} | {status} |\n"

        # Event types
        report += f"\n### Event Types Captured\n\n"
        if self.event_types:
            report += "| Event Type | Count |\n"
            report += "|------------|-------|\n"
            for event_type, count in sorted(self.event_types.items(), key=lambda x: x[1], reverse=True):
                report += f"| {event_type} | {count} |\n"
        else:
            report += "_No events captured_\n"

        # Errors
        report += f"\n### Errors ({len(self.errors)})\n\n"
        if self.errors:
            for error in self.errors:
                report += f"- ✗ {error}\n"
        else:
            report += "✓ No errors detected\n"

        # Warnings
        report += f"\n### Warnings ({len(self.warnings)})\n\n"
        if self.warnings:
            for warning in self.warnings:
                report += f"- ⚠ {warning}\n"
        else:
            report += "✓ No warnings\n"

        # Performance
        report += "\n## Performance Observations\n\n"
        turns_per_minute = (self.turns_completed / duration) * 60 if duration > 0 else 0
        report += f"- **Turns per minute**: {turns_per_minute:.1f}\n"
        report += f"- **Average time per turn**: {duration/self.turns_completed:.2f}s\n" if self.turns_completed > 0 else ""
        report += f"- **Total state checks**: {len(self.game_states)}\n"

        # Recommendations
        report += "\n## Recommendations\n\n"

        if not self.final_state or self.final_state.get("status") not in ["completed", "finished"]:
            report += "- ⚠ **Game did not complete naturally** - investigate why game ended prematurely or didn't finish within time limit\n"

        if self.errors:
            report += f"- ✗ **{len(self.errors)} errors detected** - review and fix critical issues\n"

        if self.warnings:
            report += f"- ⚠ **{len(self.warnings)} warnings** - investigate potential issues\n"

        if not self.event_types:
            report += "- ⚠ **No events captured** - verify event logging is working\n"

        if turns_per_minute < 1:
            report += f"- ⚠ **Slow game progression** ({turns_per_minute:.1f} turns/min) - consider optimizing game loop\n"
        elif turns_per_minute > 30:
            report += f"- ⚠ **Very fast game progression** ({turns_per_minute:.1f} turns/min) - verify game logic is executing correctly\n"

        if len(self.errors) == 0 and len(self.warnings) == 0 and self.final_state and self.final_state.get("status") in ["completed", "finished"]:
            report += "- ✓ **All checks passed** - game playthrough completed successfully\n"

        report += "\n## Test Configuration\n\n"
        report += f"- **Base URL**: {BASE_URL}\n"
        report += f"- **Poll Interval**: {POLL_INTERVAL}s\n"
        report += f"- **Max Duration**: {MAX_DURATION/60:.0f} minutes\n"
        report += f"- **Max Turns**: {MAX_TURNS}\n"
        report += f"- **Game Seed**: 12345\n"

        return report

    def run(self):
        """Run the full test"""
        print("=" * 60)
        print("MONOPOLY FULL GAME PLAYTHROUGH TEST")
        print("=" * 60)

        # Start game
        if not self.start_game():
            return False

        # Monitor game
        self.monitor_game()

        # Analyze events
        self.analyze_events()

        # Generate and save report
        print("\nGenerating test report...")
        report = self.generate_report()

        report_path = "/Users/venkatavamshigunji/Documents/Workspace/monopoly-agents/backend/TEST_PLAYTHROUGH_REPORT.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"✓ Report saved to {report_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Duration: {(self.end_time - self.start_time).total_seconds():.1f}s")
        print(f"Turns: {self.turns_completed}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Status: {'✓ PASSED' if len(self.errors) == 0 else '✗ FAILED'}")
        print("=" * 60)

        return len(self.errors) == 0

if __name__ == "__main__":
    test = GamePlaythroughTest()
    success = test.run()
    exit(0 if success else 1)
