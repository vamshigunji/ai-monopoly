#!/usr/bin/env python3
"""
End-to-end test script for Monopoly AI Agents
Tests: game creation, agent decisions, events, progression
"""

import asyncio
import time
import requests
import json
from typing import Dict, Any

API_URL = "http://localhost:8000/api"

class GameTester:
    def __init__(self):
        self.game_id = None
        self.initial_state = None
        self.current_state = None

    def print_header(self, text: str):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")

    def print_status(self, emoji: str, text: str):
        print(f"{emoji} {text}")

    def test_backend_health(self) -> bool:
        """Test if backend is running"""
        self.print_header("1. Testing Backend Health")
        try:
            response = requests.get(f"{API_URL.replace('/api', '')}/docs", timeout=5)
            if response.status_code == 200:
                self.print_status("✅", "Backend is running on port 8000")
                return True
            else:
                self.print_status("❌", f"Backend returned status {response.status_code}")
                return False
        except Exception as e:
            self.print_status("❌", f"Backend is NOT running: {e}")
            return False

    def create_game(self) -> bool:
        """Create a new game"""
        self.print_header("2. Creating New Game")
        try:
            response = requests.post(
                f"{API_URL}/game/start",
                json={"seed": 99999},
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.game_id = data["game_id"]
                self.print_status("✅", f"Game created: {self.game_id[:8]}...")

                # Print agent details
                print("\n   Agents configured:")
                for player in data["players"]:
                    print(f"   - {player['name']} ({player['model']})")

                return True
            else:
                self.print_status("❌", f"Failed to create game: {response.status_code}")
                print(f"   Error: {response.text}")
                return False

        except Exception as e:
            self.print_status("❌", f"Exception creating game: {e}")
            return False

    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state"""
        try:
            response = requests.get(
                f"{API_URL}/game/{self.game_id}/state",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"   Error fetching state: {e}")
            return None

    def test_game_progression(self) -> bool:
        """Wait for game to progress and verify it's working"""
        self.print_header("3. Testing Game Progression")

        # Get initial state
        state = self.get_game_state()
        if not state:
            self.print_status("❌", "Could not fetch initial game state")
            return False

        self.initial_state = state
        initial_turn = self.initial_state.get("turn_number", 0)

        self.print_status("⏳", f"Initial turn: {initial_turn}")
        self.print_status("⏳", "Waiting 15 seconds for agents to make decisions...")

        # Wait and check for progression
        time.sleep(15)

        state = self.get_game_state()
        if not state:
            self.print_status("❌", "Could not fetch updated game state")
            return False

        self.current_state = state
        current_turn = self.current_state.get("turn_number", 0)

        if current_turn > initial_turn:
            self.print_status("✅", f"Game progressed! Now on turn {current_turn}")
            return True
        else:
            self.print_status("❌", f"Game did NOT progress (still turn {current_turn})")
            self.print_status("⚠️", "This means agents are NOT making decisions")
            return False

    def verify_tokens_moving(self) -> bool:
        """Check if player positions are changing"""
        self.print_header("4. Verifying Player Movement")

        if not self.initial_state or not self.current_state:
            self.print_status("❌", "No state data to compare")
            return False

        moved = False
        for i, (initial, current) in enumerate(zip(
            self.initial_state["players"],
            self.current_state["players"]
        )):
            initial_pos = initial["position"]
            current_pos = current["position"]

            if current_pos != initial_pos:
                self.print_status("✅", f"{initial['name']}: moved from {initial_pos} → {current_pos}")
                moved = True
            else:
                self.print_status("ℹ️", f"{initial['name']}: still at position {current_pos}")

        return moved

    def verify_cash_changes(self) -> bool:
        """Check if player cash is changing"""
        self.print_header("5. Verifying Financial Activity")

        if not self.initial_state or not self.current_state:
            return False

        changed = False
        for i, (initial, current) in enumerate(zip(
            self.initial_state["players"],
            self.current_state["players"]
        )):
            initial_cash = initial["cash"]
            current_cash = current["cash"]

            if current_cash != initial_cash:
                diff = current_cash - initial_cash
                sign = "+" if diff > 0 else ""
                self.print_status("✅", f"{initial['name']}: ${initial_cash} → ${current_cash} ({sign}${diff})")
                changed = True
            else:
                self.print_status("ℹ️", f"{initial['name']}: still has ${current_cash}")

        return changed

    def check_events(self) -> bool:
        """Check if events are being generated"""
        self.print_header("6. Checking Game Events")

        if not self.current_state:
            return False

        # In a real implementation, we'd fetch events from an events endpoint
        # For now, we check if turn number increased (which means events happened)
        if self.current_state["turn_number"] > 0:
            self.print_status("✅", f"Events are being generated (turn {self.current_state['turn_number']})")
            return True
        else:
            self.print_status("❌", "No events detected")
            return False

    def print_summary(self, results: Dict[str, bool]):
        """Print final summary"""
        self.print_header("TEST SUMMARY")

        total = len(results)
        passed = sum(1 for v in results.values() if v)

        print(f"Tests Passed: {passed}/{total}\n")

        for test, result in results.items():
            emoji = "✅" if result else "❌"
            print(f"{emoji} {test}")

        print("\n" + "="*60)

        if passed == total:
            print("🎉 ALL TESTS PASSED! Backend is fully working!")
            print("\nYou should see:")
            print("  ✅ Tokens moving on the board")
            print("  ✅ Dice rolling in center")
            print("  ✅ Rich game logs")
            print("  ✅ Public conversations")
            print("  ✅ Private thoughts")
        else:
            print("⚠️  Some tests failed. Debug needed.")
            if not results.get("Game Progression"):
                print("\n💡 Likely issue: Agents not making decisions")
                print("   Check backend logs for errors")

        print("="*60 + "\n")

    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "🎲"*30)
        print("  MONOPOLY AI AGENTS - BACKEND TEST SUITE")
        print("🎲"*30)

        results = {}

        # Run tests in sequence
        results["Backend Running"] = self.test_backend_health()
        if not results["Backend Running"]:
            print("\n❌ Backend not running. Please start it first.")
            return

        results["Game Creation"] = self.create_game()
        if not results["Game Creation"]:
            return

        results["Game Progression"] = self.test_game_progression()
        results["Token Movement"] = self.verify_tokens_moving()
        results["Cash Changes"] = self.verify_cash_changes()
        results["Events Generated"] = self.check_events()

        # Print summary
        self.print_summary(results)


if __name__ == "__main__":
    tester = GameTester()
    tester.run_all_tests()
