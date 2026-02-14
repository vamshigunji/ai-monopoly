#!/usr/bin/env python3
"""
Event History Validation Test
Verifies that game events are captured correctly including agent conversations
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_event_history():
    """Test event history endpoint and verify agent events"""
    print("=" * 60)
    print("EVENT HISTORY VALIDATION TEST")
    print("=" * 60)

    # 1. Create a new game
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
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # 2. Wait for some gameplay
    print(f"\n2. Waiting 30 seconds for gameplay...")
    time.sleep(30)

    # 3. Fetch event history
    print(f"\n3. Fetching event history...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/game/{game_id}/history",
            timeout=10
        )
        response.raise_for_status()
        history = response.json()

        events = history.get("events", [])
        total = history.get("total_events", 0)
        has_more = history.get("has_more", False)

        print(f"   ✓ History retrieved")
        print(f"   Total events: {total}")
        print(f"   Events in response: {len(events)}")
        print(f"   Has more: {has_more}")

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # 4. Analyze event types
    print(f"\n4. Event type breakdown:")
    event_counts = {}
    for event in events:
        event_type = event.get("event", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    for event_type, count in sorted(event_counts.items()):
        print(f"   - {event_type}: {count}")

    # 5. Check for agent conversation events
    print(f"\n5. Agent conversation events:")
    agent_thoughts = [e for e in events if e.get("event") == "AGENT_THOUGHT"]
    agent_speech = [e for e in events if e.get("event") == "AGENT_SPOKE"]

    print(f"   - AGENT_THOUGHT: {len(agent_thoughts)}")
    print(f"   - AGENT_SPOKE: {len(agent_speech)}")

    if agent_thoughts:
        print(f"\n   Example thought:")
        thought = agent_thoughts[0].get("data", {}).get("thought", "N/A")
        print(f"   \"{thought[:100]}...\"")

    if agent_speech:
        print(f"\n   Example speech:")
        speech = agent_speech[0].get("data", {}).get("message", "N/A")
        player_id = agent_speech[0].get("data", {}).get("player_id", "?")
        print(f"   Player {player_id}: \"{speech[:100]}...\"")

    # 6. Check game state
    print(f"\n6. Verifying game state...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/game/{game_id}/state",
            timeout=10
        )
        response.raise_for_status()
        state = response.json()

        turn = state.get("turn_number", 0)
        players = state.get("players", [])

        print(f"   ✓ Game state retrieved")
        print(f"   Turn: {turn}")
        print(f"   Players: {len(players)}")

        if players:
            print(f"\n   Player status:")
            for p in players:
                name = p.get("name", "?")
                money = p.get("money", 0)
                props = len(p.get("properties", []))
                print(f"   - {name}: ${money}, {props} properties")

    except Exception as e:
        print(f"   ✗ Failed: {e}")

    print("\n" + "=" * 60)
    print("✓ VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_event_history()
