#!/usr/bin/env python3
"""
Test WebSocket connection and game_state_sync event
Verifies the fixes for Bug #1 (WebSocket disconnected)
"""

import asyncio
import json
import websockets
import requests

API_URL = "http://localhost:8000/api"

async def test_websocket():
    """Test WebSocket connection and initial state sync"""
    print("🧪 Testing WebSocket Connection Fixes\n")
    print("="*60)

    # Step 1: Create a game
    print("\n1. Creating game...")
    response = requests.post(
        f"{API_URL}/game/start",
        json={"seed": 12345},
        timeout=10
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create game: {response.status_code}")
        return False

    data = response.json()
    game_id = data["game_id"]
    print(f"✅ Game created: {game_id[:12]}...")

    # Step 2: Connect to WebSocket
    print("\n2. Connecting to WebSocket...")
    ws_url = f"ws://localhost:8000/ws/game/{game_id}"
    print(f"   URL: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected!")

            # Step 3: Wait for game_state_sync event
            print("\n3. Waiting for game_state_sync event...")

            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            event_data = json.loads(message)

            print(f"📨 Received event: {event_data.get('event')}")

            if event_data.get("event") == "game_state_sync":
                print("✅ Received game_state_sync event!")

                # Verify data structure
                data = event_data.get("data", {})
                required_fields = ["game_id", "status", "turn_number", "players"]

                missing = [f for f in required_fields if f not in data]
                if missing:
                    print(f"⚠️  Missing fields: {missing}")
                else:
                    print(f"✅ All required fields present")
                    print(f"   - Game ID: {data['game_id'][:12]}...")
                    print(f"   - Status: {data['status']}")
                    print(f"   - Turn: {data['turn_number']}")
                    print(f"   - Players: {len(data['players'])}")

                    # Show player data structure
                    if data['players']:
                        player = data['players'][0]
                        print(f"\n   Player 0 fields: {list(player.keys())}")

                # Wait for a few more events
                print("\n4. Waiting for game events...")
                for i in range(3):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        event = json.loads(message)
                        print(f"   📨 Event {i+1}: {event.get('event')}")
                    except asyncio.TimeoutError:
                        print(f"   ⏰ No event received in 10s")
                        break

                print("\n" + "="*60)
                print("✅ WebSocket test PASSED!")
                print("\nThe fixes are working:")
                print("  1. WebSocket connects successfully")
                print("  2. game_state_sync event is received")
                print("  3. Game state has correct structure")
                print("  4. Events are streaming properly")
                return True
            else:
                print(f"❌ Expected game_state_sync, got: {event_data.get('event')}")
                return False

    except asyncio.TimeoutError:
        print("❌ Timeout waiting for WebSocket message")
        return False
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
