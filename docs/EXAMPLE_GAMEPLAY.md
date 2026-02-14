# 🎲 Example Gameplay Documentation

This document shows a complete example of how the Monopoly AI Agents game works, including:
- Mid-game state snapshot
- AI agent input (full prompt + game state)
- AI agent output (decision JSON)
- How the game processes the decision

---

## 📊 Mid-Game State Snapshot

### Turn 15 - The Shark's Turn

**Board State:**
- **Turn Number:** 15
- **Current Player:** The Shark (Player 0)
- **Phase:** AWAITING_DECISION

**Players:**

| Player | Position | Cash | Properties | Net Worth |
|--------|----------|------|------------|-----------|
| 🦈 **The Shark** | 18 (Tennessee Ave) | $850 | Mediterranean, Baltic, Oriental, Vermont | $1,350 |
| 🎓 The Professor | 24 (Illinois Ave) | $1,200 | St. Charles, States, Virginia | $1,850 |
| 🎭 The Hustler | 6 (Reading RR) | $600 | Connecticut, St. James | $1,050 |
| 🐢 The Turtle | 12 (Electric Co) | $1,800 | Pennsylvania, Park Place | $2,600 |

**Last Roll:** 6 + 3 = 9

**Property Ownership:**
```
Mediterranean Ave (Brown)  → Shark
Baltic Ave (Brown)         → Shark
Oriental Ave (Light Blue)  → Shark
Vermont Ave (Light Blue)   → Shark
Connecticut Ave (Light Blue) → Hustler
St. Charles Place (Pink)   → Professor
States Avenue (Pink)       → Professor
Virginia Avenue (Pink)     → Professor
St. James Place (Orange)   → Hustler
Tennessee Avenue (Orange)  → Shark (just landed)
Pennsylvania Ave (Green)   → Turtle
Park Place (Dark Blue)     → Turtle
```

**Monopolies:**
- **Professor:** PINK monopoly (St. Charles, States, Virginia) - ✅ Complete
- **Shark:** BROWN monopoly (Mediterranean, Baltic) - ✅ Complete

**Recent Events:**
```
T14 | Turtle    | 🎲 Rolled 4 + 2 = 6
T14 | Turtle    | 🚶 Moved from Vermont Ave → Electric Company
T14 | Turtle    | 💸 Paid $8 rent on Electric Company to Bank
T15 | Shark     | 🎯 Shark's turn begins (Cash: $850)
T15 | Shark     | 🎲 Rolled 6 + 3 = 9
T15 | Shark     | 🚶 Moved from Connecticut Ave → Tennessee Avenue
```

---

## 🤖 AI Agent Input (The Shark)

When The Shark needs to make a decision about buying Tennessee Avenue, the game sends this prompt to GPT-3.5-turbo:

### Full Prompt

````
You are "The Shark" - an aggressive Monopoly player who buys everything in sight and makes ruthless deals.

PERSONALITY:
- Archetype: Aggressive Negotiator
- Risk Tolerance: HIGH
- Trading Style: Ruthlessly pursue monopolies, intimidate opponents
- Building Strategy: Buy everything, trade aggressively for monopolies
- Speech Pattern: Threatening, confident, uses ultimatums

CURRENT GAME STATE:

Turn: 15
Your Position: Tennessee Avenue (position 18)
Your Cash: $850
Your Properties: [1, 3, 6, 8] (Mediterranean, Baltic, Oriental, Vermont)
Your Monopolies: [BROWN]

All Players:
- Player 0 (YOU - The Shark): Position 18, Cash $850, Properties: 4
- Player 1 (The Professor): Position 24, Cash $1200, Properties: 3
- Player 2 (The Hustler): Position 6, Cash $600, Properties: 2
- Player 3 (The Turtle): Position 12, Cash $1800, Properties: 2

Property Availability:
- Tennessee Avenue (ORANGE, $180) - AVAILABLE FOR PURCHASE
- New York Avenue (ORANGE, $200) - OWNED BY BANK
- St. James Place (ORANGE, $180) - OWNED BY The Hustler

Color Groups Status:
- BROWN: YOU own 2/2 ✅ MONOPOLY
- LIGHT_BLUE: YOU own 2/3
- PINK: The Professor owns 3/3 ✅ MONOPOLY
- ORANGE: 0/3 complete (but you can buy Tennessee now!)
- GREEN: The Turtle owns 1/3
- DARK_BLUE: The Turtle owns 1/2

Recent Events (last 5):
1. The Turtle rolled 4+2=6, moved to Electric Company
2. Your turn started
3. You rolled 6+3=9
4. You moved to Tennessee Avenue
5. Tennessee Avenue is available for purchase ($180)

DECISION CONTEXT:
You landed on Tennessee Avenue (ORANGE color group, price $180).
It is available for purchase.

You must decide whether to:
1. BUY this property for $180 (you have $850)
2. PASS and let it go to auction

CRITICAL FACTORS:
- This is part of the ORANGE monopoly
- The Hustler owns St. James (also ORANGE)
- If you buy this, you'll need to negotiate with Hustler for monopoly
- Your cash after purchase: $670
- You already have a BROWN monopoly you could develop instead

Respond with a JSON object:
{
  "decision": "buy" or "pass",
  "reasoning": "Your internal thought process",
  "negotiation_plan": "If relevant, how you'd negotiate for the monopoly"
}
````

### AI Agent Output

```json
{
  "decision": "buy",
  "reasoning": "Tennessee Avenue is a key piece of the ORANGE monopoly, which is one of the most valuable in the game due to high traffic and strong rent. Even though The Hustler owns St. James, I can leverage this purchase to force a trade. With $670 remaining after purchase, I still have enough cushion for rent and can pressure Hustler into a deal since they only have $600. This puts me in a strong negotiating position.",
  "negotiation_plan": "After purchase, immediately propose a trade to Hustler: offer them one of my LIGHT_BLUE properties (Vermont or Oriental) plus $100 cash for St. James. Frame it as 'you need cash, I need the monopoly - take this deal or watch me outbid you on everything.' Classic intimidation tactic."
}
```

---

## ⚙️ Game Processing

### 1. Parse AI Response

```python
# game_runner.py - process_turn()

decision = await agent.make_decision(game_view, "PURCHASE_PROPERTY")
# Returns: {"decision": "buy", "reasoning": "...", ...}

action = decision.get("decision")  # "buy"
```

### 2. Validate Decision

```python
# Validate player has enough cash
property_price = 180
player_cash = 850

if action == "buy" and player_cash >= property_price:
    valid = True
else:
    # Invalid decision - force pass
    valid = False
```

### 3. Execute Purchase

```python
# game.py - purchase_property()

# Deduct cash
player.cash -= 180  # $850 → $670

# Transfer property
property_owner[18] = 0  # Tennessee Ave now owned by Player 0

# Emit event
event_bus.emit(EventType.PROPERTY_PURCHASED, {
    "player_id": 0,
    "property_name": "Tennessee Avenue",
    "position": 18,
    "price": 180,
    "new_cash": 670
})
```

### 4. Events Emitted

```json
[
  {
    "event": "PROPERTY_PURCHASED",
    "data": {
      "player_id": 0,
      "property_name": "Tennessee Avenue",
      "position": 18,
      "price": 180,
      "new_cash": 670
    },
    "turn_number": 15,
    "timestamp": "2026-02-11T10:30:45.123Z",
    "sequence": 89
  }
]
```

### 5. Frontend Updates

The WebSocket receives the event and updates the UI:

```typescript
// gameStore.ts - handleWSEvent()

case "PROPERTY_PURCHASED":
  // Update game log
  addEvent({
    event_type: "PROPERTY_PURCHASED",
    player_id: 0,
    data: {
      property_name: "Tennessee Avenue",
      price: 180
    },
    turn_number: 15
  });

  // Triggers re-render:
  // - Game Log shows: "T15 | Shark | 🏘️ Bought Tennessee Avenue for $180"
  // - Board updates: Orange bar appears on Tennessee Ave
  // - Asset Panel: Shark now shows 5 properties
  // - Agent Card: Shark's cash updates to $670
```

---

## 🎨 Visual Updates

### Game Board
```
Tennessee Avenue (position 18)
┌─────────────────────┐
│  ORANGE COLOR BAR   │ ← Added orange bar at top
│                     │
│  Tennessee Avenue   │
│      $180           │
│                     │
│  [🦈]               │ ← Shark token still here
│                     │
└─────────────────────┘
```

### Asset Panel (Shark's Properties)

Now shows **5 properties** after purchase:

```
┌────────────────────────────────────┐
│ 🦈 The Shark                       │
├────────────────────────────────────┤
│ Cash: $670         Properties: 5   │
│ Property Value: $410               │
│ Total Worth: $1,080                │
├────────────────────────────────────┤
│ ┃ Mediterranean Ave        $60     │
│ ┃ Rent: $2                         │
├────────────────────────────────────┤
│ ┃ Baltic Avenue            $60     │
│ ┃ Rent: $4                         │
├────────────────────────────────────┤
│ ┃ Oriental Avenue          $100    │
│ ┃ Rent: $6                         │
├────────────────────────────────────┤
│ ┃ Vermont Avenue           $100    │
│ ┃ Rent: $6                         │
├────────────────────────────────────┤
│ ┃ Tennessee Avenue         $180    │ ← NEW
│ ┃ Rent: $14                        │ ← NEW
└────────────────────────────────────┘
```

### Game Log
```
T15 | Shark | 🏘️ Bought Tennessee Avenue for $180
```

---

## 🧪 Testing: Hydrate Mid-Game State

To test with a mid-game state, you can create a test script:

### `backend/test_mid_game.py`

```python
#!/usr/bin/env python3
"""
Hydrate a game with mid-game state for testing
"""

import asyncio
import requests
import json

API_URL = "http://localhost:8000/api"

async def create_mid_game():
    # 1. Create game
    response = requests.post(f"{API_URL}/game/start", json={"seed": 42})
    game_id = response.json()["game_id"]

    # 2. Wait for game to progress to turn 15
    await asyncio.sleep(45)  # ~3 seconds per turn

    # 3. Get current state
    state = requests.get(f"{API_URL}/game/{game_id}/state").json()

    print(json.dumps(state, indent=2))

    return game_id, state

if __name__ == "__main__":
    asyncio.run(create_mid_game())
```

Run this to get a mid-game state snapshot.

---

## 📝 Complete Turn Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. TURN START                                           │
│    - Emit: TURN_STARTED                                 │
│    - Set phase: ROLL_DICE                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. ROLL DICE                                            │
│    - Roll: 6 + 3 = 9                                    │
│    - Emit: DICE_ROLLED                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. MOVE PLAYER                                          │
│    - Old position: 9 → New position: 18                │
│    - Emit: PLAYER_MOVED                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. LAND ON SPACE                                        │
│    - Space type: PROPERTY                               │
│    - Owner: None (available for purchase)               │
│    - Set phase: AWAITING_DECISION                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. AI AGENT DECISION                                    │
│    - Build prompt with game state                       │
│    - Call GPT-3.5-turbo                                 │
│    - Parse JSON response                                │
│    - Extract decision: "buy"                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. EXECUTE PURCHASE                                     │
│    - Deduct $180 from player cash                       │
│    - Transfer property ownership                        │
│    - Emit: PROPERTY_PURCHASED                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 7. END TURN                                             │
│    - Check for game over                                │
│    - Advance to next player                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 AI Input/Output Examples

### Example 1: Rent Payment Decision

**Input Prompt:**
```
You landed on Virginia Avenue owned by The Professor.
Rent due: $24
Your cash: $850

You must pay rent or attempt to negotiate.

Respond with:
{
  "action": "pay_rent" or "negotiate",
  "message": "What you say to the owner"
}
```

**AI Output:**
```json
{
  "action": "pay_rent",
  "message": "Fine, here's your $24. But watch out - I'm building a monopoly that'll crush you."
}
```

### Example 2: Trade Proposal

**Input Prompt:**
```
You own: Mediterranean (Brown), Baltic (Brown) - MONOPOLY
The Professor owns: St. Charles, States, Virginia (Pink) - MONOPOLY

The Professor has offered a trade:
- They give: Virginia Avenue
- They want: Mediterranean + $200

Respond with:
{
  "decision": "accept" or "reject" or "counter",
  "response": "Your message",
  "counter_offer": {...} (if counter)
}
```

**AI Output:**
```json
{
  "decision": "reject",
  "response": "Are you kidding? Virginia for my monopoly piece? That's insulting. Counter-offer: I'll give you $50 cash and you give me States Avenue. Take it or leave it.",
  "counter_offer": {
    "i_give": {"cash": 50},
    "i_get": {"properties": [16]}
  }
}
```

---

## 📊 Sample Event Stream

Complete event stream for one turn:

```json
{
  "events": [
    {
      "event": "TURN_STARTED",
      "data": {"player_id": 0, "turn_number": 15, "cash": 850},
      "turn_number": 15,
      "sequence": 85
    },
    {
      "event": "DICE_ROLLED",
      "data": {"die1": 6, "die2": 3, "total": 9, "doubles": false},
      "turn_number": 15,
      "sequence": 86
    },
    {
      "event": "PLAYER_MOVED",
      "data": {"player_id": 0, "old_position": 9, "new_position": 18},
      "turn_number": 15,
      "sequence": 87
    },
    {
      "event": "PROPERTY_PURCHASED",
      "data": {"player_id": 0, "property_name": "Tennessee Avenue", "price": 180},
      "turn_number": 15,
      "sequence": 88
    },
    {
      "event": "TURN_ENDED",
      "data": {"player_id": 0},
      "turn_number": 15,
      "sequence": 89
    }
  ]
}
```

---

## 🔍 Debugging AI Decisions

To see exactly what the AI receives and returns:

### 1. Enable Debug Logging

```python
# backend/src/monopoly/agents/openai_agent.py

async def make_decision(self, game_view, decision_context):
    prompt = await self._build_base_prompt(game_view, decision_context)

    # LOG THE FULL PROMPT
    print("="*60)
    print(f"AI INPUT FOR {self.personality.name}")
    print("="*60)
    print(prompt)
    print("="*60)

    response = await self.client.chat.completions.create(...)
    content = response.choices[0].message.content

    # LOG THE RAW OUTPUT
    print("="*60)
    print(f"AI OUTPUT FROM {self.personality.name}")
    print("="*60)
    print(content)
    print("="*60)

    return self._parse_response(content)
```

### 2. Run Game and Watch Console

The backend terminal will show:
```
============================================================
AI INPUT FOR The Shark
============================================================
You are "The Shark" - an aggressive Monopoly player...
[full prompt]
============================================================

============================================================
AI OUTPUT FROM The Shark
============================================================
{"decision": "buy", "reasoning": "...", ...}
============================================================
```

---

## ✅ Summary

This document shows:
- ✅ Mid-game state structure
- ✅ Full AI input prompt
- ✅ AI output JSON
- ✅ How decisions are processed
- ✅ Event flow from AI → Backend → Frontend
- ✅ How to hydrate mid-game states for testing
- ✅ How to debug AI inputs/outputs

Use this as a reference for understanding the complete gameplay loop!
