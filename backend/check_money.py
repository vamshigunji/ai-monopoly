import requests
import json

game_id = "09c1bdd4-0a64-4228-8ada-7bb4c19a3ee6"
response = requests.get(f"http://localhost:8000/api/game/{game_id}/state")
data = response.json()

print("Player Money Check:")
print("=" * 60)
for player in data.get("players", []):
    print(f"\nPlayer: {player.get('name')}")
    print(f"  ID: {player.get('id')}")
    print(f"  Money: ${player.get('money', 'NOT FOUND')}")
    print(f"  Cash: ${player.get('cash', 'NOT FOUND')}")
    print(f"  Properties: {len(player.get('properties', []))}")
    print(f"  Position: {player.get('position')}")
    print(f"  Status: {player.get('status', 'NOT FOUND')}")

print("\n" + "=" * 60)
print("\nFull player data sample:")
if data.get("players"):
    print(json.dumps(data["players"][0], indent=2))
