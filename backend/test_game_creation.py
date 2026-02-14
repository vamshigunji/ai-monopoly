#!/usr/bin/env python3
"""
Test script to diagnose game creation issue.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_game_creation():
    """Test game creation and immediate state retrieval."""
    print("=" * 60)
    print("GAME CREATION DIAGNOSTIC TEST")
    print("=" * 60)

    # 1. Start a game
    print("\n1. Creating game...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/game/start",
            json={"seed": 99999},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        game_id = data.get("game_id")
        print(f"   ✓ Game created: {game_id}")
        print(f"   Status: {data.get('status')}")
        print(f"   Players: {len(data.get('players', []))}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # 2. Immediately check state
    print(f"\n2. Checking state immediately...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/game/{game_id}/state",
            timeout=10
        )
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            state = response.json()
            print(f"   ✓ State retrieved")
            print(f"   Turn: {state.get('turn_number', 'N/A')}")
            print(f"   Status: {state.get('status', 'N/A')}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    # 3. Wait and try again
    for delay in [1, 2, 5]:
        print(f"\n3. Checking state after {delay}s...")
        time.sleep(delay)
        try:
            response = requests.get(
                f"{BASE_URL}/api/game/{game_id}/state",
                timeout=10
            )
            print(f"   Status code: {response.status_code}")
            if response.status_code == 200:
                state = response.json()
                print(f"   ✓ State retrieved")
                print(f"   Turn: {state.get('turn_number', 'N/A')}")
                print(f"   Status: {state.get('status', 'N/A')}")
                break
            else:
                print(f"   ✗ Error: {response.text}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    # 4. Try to list games (if endpoint exists)
    print(f"\n4. Checking available games...")
    for endpoint in ["/api/games", "/api/game"]:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   {endpoint}: Failed - {e}")

    # 5. Check health
    print(f"\n5. Backend health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status: {response.json()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_game_creation()
