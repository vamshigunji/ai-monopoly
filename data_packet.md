# AI Agent Data Packet — Complete Specification

This document defines the **complete information package** sent to each AI agent
when it needs to make a decision during a Monopoly game. It covers what currently
exists in code, what is broken, and what the ideal packet should contain.

---

## Table of Contents

1. [Packet Architecture (Current vs Ideal)](#1-packet-architecture-current-vs-ideal)
2. [Critical Bugs in Current Implementation](#2-critical-bugs-in-current-implementation)
3. [Complete Board Reference (MISSING — Must Add)](#3-complete-board-reference-missing--must-add)
4. [Full Ideal Data Packet Example](#4-full-ideal-data-packet-example)
5. [Layer-by-Layer Specification](#5-layer-by-layer-specification)
6. [Available Actions per Decision Type](#6-available-actions-per-decision-type)
7. [Required Output Specification (What Agents Must Return)](#7-required-output-specification-what-agents-must-return)
8. [Agent Personality Configs](#8-agent-personality-configs)
9. [LLM API Call Parameters](#9-llm-api-call-parameters)
10. [Gap Analysis & Recommendations](#10-gap-analysis--recommendations)

---

## 1. Packet Architecture (Current vs Ideal)

### Current (What code actually sends today)

```
┌────────────────────────────────┐
│  Personality System Prompt     │  ✅ Exists — ~300 words, static per agent
├────────────────────────────────┤
│  Monopoly Rules Summary        │  ✅ Exists — ~120 words, static
├────────────────────────────────┤
│  Current Game State            │  ⚠️  Partial — bare integers, no names/rents
├────────────────────────────────┤
│  Public Conversation History   │  ❌ BROKEN — agents only hear themselves
├────────────────────────────────┤
│  Private Thought History       │  ✅ Exists — last 5 thoughts
├────────────────────────────────┤
│  Decision Context              │  ⚠️  Partial — no available actions list
├────────────────────────────────┤
│  Board Reference               │  ❌ MISSING — no property names/rents/colors
├────────────────────────────────┤
│  Packet Metadata               │  ❌ MISSING — no decision #, no turn tracking
├────────────────────────────────┤
│  Output Specification          │  ⚠️  Implicit — via function schema only
└────────────────────────────────┘
```

### Ideal (What should be sent)

```
┌────────────────────────────────────────────────────────────────────┐
│  1. PACKET METADATA              │  Decision #, turn, phase, agent │
├──────────────────────────────────┼─────────────────────────────────┤
│  2. PERSONALITY SYSTEM PROMPT    │  Who you are, how you play      │
├──────────────────────────────────┼─────────────────────────────────┤
│  3. MONOPOLY RULES SUMMARY      │  Core rules reference           │
├──────────────────────────────────┼─────────────────────────────────┤
│  4. FULL BOARD STATE             │  All 40 spaces with names,      │
│                                  │  owners, buildings, rents,      │
│                                  │  player positions               │
├──────────────────────────────────┼─────────────────────────────────┤
│  5. YOUR STATE (private)         │  Cash, properties, cards, etc.  │
├──────────────────────────────────┼─────────────────────────────────┤
│  6. OPPONENT STATES (public)     │  Cash, properties, positions    │
├──────────────────────────────────┼─────────────────────────────────┤
│  7. PUBLIC CONVERSATION HISTORY  │  ALL agents' messages (shared)  │
├──────────────────────────────────┼─────────────────────────────────┤
│  8. YOUR PRIVATE THOUGHT HISTORY │  Your last 5 strategic thoughts │
├──────────────────────────────────┼─────────────────────────────────┤
│  9. AVAILABLE ACTIONS            │  Explicit list of legal moves   │
├──────────────────────────────────┼─────────────────────────────────┤
│  10. DECISION CONTEXT            │  What you're being asked to do  │
├──────────────────────────────────┼─────────────────────────────────┤
│  11. REQUIRED OUTPUT FORMAT      │  Exact JSON you must return     │
└──────────────────────────────────┴─────────────────────────────────┘
         ↓ sent as system message to LLM
   ┌──────────────┐
   │  LLM API     │  OpenAI function calling / Gemini structured output
   └──────┬───────┘
          ↓ returns structured JSON
   ┌──────────────────────────────────────────────────┐
   │  {                                                │
   │    "<decision_field>": <value>,   // game action  │
   │    "public_speech": "...",        // said aloud   │
   │    "private_thought": "..."       // internal     │
   │  }                                                │
   └──────────────────────────────────────────────────┘
```

---

## 2. Critical Bugs in Current Implementation

### BUG 1: Agents Cannot Hear Each Other (Isolated Contexts)

**Severity: CRITICAL — Negotiations are impossible.**

Each agent has its own `ContextManager` instance. When Shark says "I'll trade you
Reds for your Oranges," that message is stored ONLY in Shark's `context.public_log`.
Professor, Hustler, and Turtle never see it.

**What happens during a trade:**
1. Shark proposes a trade and says "Take this deal or regret it" → stored in Shark's context only
2. Professor receives the trade proposal numbers but NEVER sees Shark's speech
3. Professor responds "The expected value is negative" → stored in Professor's context only
4. Shark never sees Professor's response

**Root cause:** `backend/src/monopoly/agents/openai_agent.py` line 48:
```python
self.context = context_manager or ContextManager(
    player_id, self._summarize_public_messages
)
```
Each agent creates its own ContextManager. No shared message bus exists.

**Fix needed:** Either a shared ContextManager per game, or a message broadcast
mechanism that copies each agent's `public_speech` to all other agents' contexts
after every decision.

### BUG 2: Board Positions Are Bare Integers (No Names, No Context)

**Severity: HIGH — Agents cannot reason about the board.**

The prompt says `Your position: 24` and `Your properties: [21, 23]`. The agent has
no way to know that:
- Position 24 = Illinois Avenue (Red, $240, rent table: $20/$100/$300/$750/$925/$1100)
- Position 21 = Kentucky Avenue (Red, $220)
- Position 23 = Indiana Avenue (Red, $220)
- Owning all three = Red monopoly

The engine HAS all this data in `backend/src/monopoly/engine/board.py` — it's just
never included in the prompt.

### BUG 3: AGENT_SPOKE/AGENT_THOUGHT Events Never Emitted

**Severity: HIGH — Frontend conversation panels are always empty.**

`EventType.AGENT_SPOKE` and `EventType.AGENT_THOUGHT` are defined in the event types
but GameRunner never calls `_emit_event()` with them. Agent messages are trapped in
the backend and never reach the WebSocket → frontend pipeline.

---

## 3. Complete Board Reference (MISSING — Must Add)

This is the full Monopoly board data that exists in the engine (`board.py`) but is
NOT currently sent to agents. This should be included in every prompt so agents can
reason about positions, rents, and strategy.

### All 40 Board Spaces

```
Pos  Name                      Type            Color       Price   Rent (base/1h/2h/3h/4h/hotel)  House Cost
───  ────────────────────────  ──────────────  ──────────  ──────  ──────────────────────────────  ──────────
 0   GO                        Pass → +$200    —           —       —                               —
 1   Mediterranean Avenue      Property        Brown       $60     $2/$10/$30/$90/$160/$250        $50
 2   Community Chest            Card            —           —       —                               —
 3   Baltic Avenue              Property        Brown       $60     $4/$20/$60/$180/$320/$450       $50
 4   Income Tax                Tax ($200)      —           —       —                               —
 5   Reading Railroad          Railroad        —           $200    $25/$50/$100/$200 (by count)    —
 6   Oriental Avenue           Property        Light Blue  $100    $6/$30/$90/$270/$400/$550       $50
 7   Chance                     Card            —           —       —                               —
 8   Vermont Avenue            Property        Light Blue  $100    $6/$30/$90/$270/$400/$550       $50
 9   Connecticut Avenue        Property        Light Blue  $120    $8/$40/$100/$300/$450/$600      $50
10   Jail / Just Visiting      —               —           —       —                               —
11   St. Charles Place         Property        Pink        $140    $10/$50/$150/$450/$625/$750     $100
12   Electric Company          Utility         —           $150    4x or 10x dice roll             —
13   States Avenue             Property        Pink        $140    $10/$50/$150/$450/$625/$750     $100
14   Virginia Avenue           Property        Pink        $160    $12/$60/$180/$500/$700/$900     $100
15   Pennsylvania Railroad     Railroad        —           $200    $25/$50/$100/$200 (by count)    —
16   St. James Place           Property        Orange      $180    $14/$70/$200/$550/$750/$950     $100
17   Community Chest            Card            —           —       —                               —
18   Tennessee Avenue          Property        Orange      $180    $14/$70/$200/$550/$750/$950     $100
19   New York Avenue           Property        Orange      $200    $16/$80/$220/$600/$800/$1000    $100
20   Free Parking              —               —           —       —                               —
21   Kentucky Avenue           Property        Red         $220    $18/$90/$250/$700/$875/$1050    $150
22   Chance                     Card            —           —       —                               —
23   Indiana Avenue            Property        Red         $220    $18/$90/$250/$700/$875/$1050    $150
24   Illinois Avenue           Property        Red         $240    $20/$100/$300/$750/$925/$1100   $150
25   B&O Railroad              Railroad        —           $200    $25/$50/$100/$200 (by count)    —
26   Atlantic Avenue           Property        Yellow      $260    $22/$110/$330/$800/$975/$1150   $150
27   Ventnor Avenue            Property        Yellow      $260    $22/$110/$330/$800/$975/$1150   $150
28   Water Works               Utility         —           $150    4x or 10x dice roll             —
29   Marvin Gardens            Property        Yellow      $280    $24/$120/$360/$850/$1025/$1200  $150
30   Go To Jail                → Jail          —           —       —                               —
31   Pacific Avenue            Property        Green       $300    $26/$130/$390/$900/$1100/$1275  $200
32   North Carolina Avenue     Property        Green       $300    $26/$130/$390/$900/$1100/$1275  $200
33   Community Chest            Card            —           —       —                               —
34   Pennsylvania Avenue       Property        Green       $320    $28/$150/$450/$1000/$1200/$1400 $200
35   Short Line Railroad       Railroad        —           $200    $25/$50/$100/$200 (by count)    —
36   Chance                     Card            —           —       —                               —
37   Park Place                Property        Dark Blue   $350    $35/$175/$500/$1100/$1300/$1500 $200
38   Luxury Tax                Tax ($100)      —           —       —                               —
39   Boardwalk                 Property        Dark Blue   $400    $50/$200/$600/$1400/$1700/$2000 $200
```

### Color Group Monopolies

```
Color        Positions              Properties Needed
──────────   ─────────────────────  ─────────────────
Brown        1, 3                   2 (Mediterranean, Baltic)
Light Blue   6, 8, 9               3 (Oriental, Vermont, Connecticut)
Pink         11, 13, 14            3 (St. Charles, States, Virginia)
Orange       16, 18, 19            3 (St. James, Tennessee, New York)
Red          21, 23, 24            3 (Kentucky, Indiana, Illinois)
Yellow       26, 27, 29            3 (Atlantic, Ventnor, Marvin Gardens)
Green        31, 32, 34            3 (Pacific, North Carolina, Pennsylvania)
Dark Blue    37, 39                2 (Park Place, Boardwalk)
```

### Rent Rules

- **Unimproved property**: Base rent from table
- **Monopoly (no houses)**: Base rent × 2
- **With houses**: Use rent table (1h through hotel)
- **Railroads**: $25 / $50 / $100 / $200 based on how many you own (unmortgaged)
- **Utilities**: Dice roll × 4 (own 1) or × 10 (own 2)
- **Mortgaged property**: Rent = $0

---

## 4. Full Ideal Data Packet Example

Below is what a **complete, ideal prompt** should look like for The Shark (Player 0)
deciding whether to buy Illinois Avenue on Turn 42, Decision #7 of that turn.

```
=== DECISION PACKET ===
Agent: The Shark (Player 0)
Turn: 42
Decision #: 7 (of this game)
Phase: PROPERTY_LANDING
Timestamp: 2026-02-11T14:23:07Z

---

You are THE SHARK, Player 0 in a 4-player Monopoly game.

PERSONALITY:
You are an aggressive, ruthless Monopoly player. You play to dominate, not
just to win. You want your opponents to feel the pressure of your growing
empire every single turn. You buy aggressively, build fast, and trade
ruthlessly. You view every property as a weapon and every opponent as prey.

STRATEGY GUIDELINES:
- Buy every property you can afford unless it would drop your cash below $100.
- In auctions, bid aggressively -- especially for properties that complete
  YOUR monopoly or BLOCK an opponent's monopoly.
- Propose trades that favor you. Frame them as urgent. Use pressure tactics.
- Build houses as soon as you have a monopoly. Speed matters more than safety.
- Mortgage properties freely to fund building -- you can unmortgage later.
- Keep minimum $100-200 cash reserve. You live on the edge.

SPEECH STYLE:
- Short, punchy, commanding sentences.
- Confident bordering on arrogant.
- Uses intimidation: "Pay up." "My property now." "You can't afford to say no."
- Occasionally sarcastic: "Nice landing. That'll cost you."
- Never shows weakness or uncertainty.

OPPONENTS:
- Player 1 "The Professor" (analytical, data-driven, patient)
- Player 2 "The Hustler" (charismatic, unpredictable, makes lots of trades)
- Player 3 "The Turtle" (ultra-conservative, hoards cash, rarely trades)

Remember: You are The Shark. Every decision should reflect aggression,
confidence, and a relentless drive to dominate the board.

---

MONOPOLY RULES SUMMARY:
- Board: 40 spaces. Pass GO = collect $200.
- Properties: Buy for listed price or auction. Monopoly = own all in color group.
- Rent: Doubles with monopoly. Houses: must build evenly across color group.
- Houses cost $50-$200 depending on color group. Hotels replace 4 houses.
- Railroads: $25/$50/$100/$200 based on count owned (unmortgaged only).
- Utilities: dice roll x4 (own 1) or x10 (own 2).
- Jail: Pay $50, use card, or try doubles (3 attempts, then forced to pay).
- Mortgage: Receive mortgage value. Unmortgage = mortgage + 10%.
- Bankruptcy: Sell buildings at half price, mortgage properties. If still short, you're out.
- Trading: Properties, cash, jail cards. No buildings on traded properties.
- Housing shortage: Only 32 houses and 12 hotels exist. First come, first served.

---

FULL BOARD STATE:
(* = your position, ^ = opponent position, [P0]-[P3] = owner, H1-H4 = houses, HT = hotel, M = mortgaged)

 0  GO
 1  Mediterranean Avenue    (Brown)     [P2] Hustler    H0  Rent: $4 (no monopoly base)
 2  Community Chest
 3  Baltic Avenue           (Brown)     UNOWNED              Price: $60
 4  Income Tax ($200)
 5  Reading Railroad                    [P1] Professor  ^Professor here    Rent: $50 (owns 2 RR)
 6  Oriental Avenue         (Lt Blue)   [P1] Professor  H2  Rent: $90
 7  Chance
 8  Vermont Avenue          (Lt Blue)   [P1] Professor  H2  Rent: $90
 9  Connecticut Avenue      (Lt Blue)   [P1] Professor  H2  Rent: $100  ← MONOPOLY
10  Jail / Just Visiting
11  St. Charles Place       (Pink)      UNOWNED              Price: $140
12  Electric Company                    [P2] Hustler         Rent: 4x dice (owns 1 utility)
13  States Avenue           (Pink)      UNOWNED              Price: $140
14  Virginia Avenue         (Pink)      [P3] Turtle          Rent: $12 (no monopoly)
15  Pennsylvania Railroad               [P1] Professor       Rent: $50 (owns 2 RR)
16  St. James Place         (Orange)    [P3] Turtle          Rent: $14 (no monopoly)
17  Community Chest
18  Tennessee Avenue        (Orange)    [P3] Turtle          Rent: $14 (no monopoly)
19  New York Avenue         (Orange)    UNOWNED              Price: $200
20  Free Parking                        ^Turtle here
21  Kentucky Avenue         (Red)       [P0] YOU        H0   Rent: $36 (monopoly, no houses)
22  Chance
23  Indiana Avenue          (Red)       [P0] YOU        H0   Rent: $36 (monopoly, no houses)
24  Illinois Avenue         (Red)       UNOWNED         *YOU ARE HERE   Price: $240
25  B&O Railroad                        [P2] Hustler         Rent: $25 (owns 1 RR)
26  Atlantic Avenue         (Yellow)    UNOWNED              Price: $260
27  Ventnor Avenue          (Yellow)    UNOWNED              Price: $260
28  Water Works                         UNOWNED              Price: $150
29  Marvin Gardens          (Yellow)    UNOWNED              Price: $280
30  Go To Jail
31  Pacific Avenue          (Green)     UNOWNED         ^Hustler here    Price: $300
32  North Carolina Avenue   (Green)     UNOWNED              Price: $300
33  Community Chest
34  Pennsylvania Avenue     (Green)     UNOWNED              Price: $320
35  Short Line Railroad                 UNOWNED              Price: $200
36  Chance
37  Park Place              (Dk Blue)   [P3] Turtle          Rent: $35 (no monopoly)
38  Luxury Tax ($100)
39  Boardwalk               (Dk Blue)   UNOWNED              Price: $400

Monopoly Status:
- Brown (1,3): SPLIT — P2 owns 1, P3 owns 0, 1 unowned
- Light Blue (6,8,9): P1 MONOPOLY ← Professor has all 3, 2 houses each
- Pink (11,13,14): SPLIT — P3 owns 14, 2 unowned
- Orange (16,18,19): SPLIT — P3 owns 16,18, 1 unowned
- Red (21,23,24): YOU own 21,23 — NEED 24 TO COMPLETE MONOPOLY
- Yellow (26,27,29): All unowned
- Green (31,32,34): All unowned
- Dark Blue (37,39): SPLIT — P3 owns 37, 39 unowned

Bank: 32/32 houses, 12/12 hotels available

---

YOUR STATE:
Cash: $1,050
Position: 24 (Illinois Avenue — Red — UNOWNED)
Properties owned:
  - 21 Kentucky Avenue (Red) — 0 houses, rent $36 (monopoly base x2)
  - 23 Indiana Avenue (Red) — 0 houses, rent $36 (monopoly base x2)
  NOTE: Buying position 24 would complete your RED MONOPOLY.
        House cost for Red = $150 each. Rent with houses: $90/$250/$700/$875/$1050
Mortgaged: none
Get Out of Jail Free cards: 1
In jail: no

---

OPPONENT STATES:
Player 1 — The Professor:
  Cash: $2,150 | Position: 5 (Reading Railroad) | Net worth: $3,400
  Properties: 5 (Reading RR), 6 (Oriental), 8 (Vermont), 9 (Connecticut), 15 (Pennsylvania RR)
  Has MONOPOLY: Light Blue (6,8,9) — 2 houses each
  In jail: no | Jail cards: 0

Player 2 — The Hustler:
  Cash: $500 | Position: 31 (Pacific Avenue) | Net worth: $975
  Properties: 1 (Mediterranean), 12 (Electric Company), 25 (B&O Railroad)
  No monopolies. Low cash — vulnerable.
  In jail: no | Jail cards: 0

Player 3 — The Turtle:
  Cash: $3,200 | Position: 20 (Free Parking) | Net worth: $3,990
  Properties: 14 (Virginia), 16 (St. James), 18 (Tennessee), 37 (Park Place)
  No monopolies. Sitting on Orange (16,18) — needs 19 to complete.
  WARNING: Turtle has most cash on the board.
  In jail: no | Jail cards: 0

---

PUBLIC CONVERSATION HISTORY:
(All agents' public statements — what everyone at the table can hear)

Earlier in the game (turns 1-31 summary):
The Professor quietly acquired Light Blue and built steadily. The Hustler
proposed 6 trades — all rejected. The Turtle accumulated cash and refused
every offer. Shark grabbed Kentucky and Indiana early.

Recent table talk:
- Turn 35, The Hustler: "Professor, trade me Connecticut for Mediterranean + $100? WIN-WIN!"
- Turn 35, The Professor: "The expected value of that trade is -$340 for me. No."
- Turn 36, The Shark: "Red is mine. Anyone who lands there will pay."
- Turn 37, The Turtle: "Pass."
- Turn 38, The Professor: "The expected return on building here is only 8% per turn."
- Turn 39, The Hustler: "Come on Turtle, I'll give you Electric Company for St. James! Trust me!"
- Turn 39, The Turtle: "No."
- Turn 40, The Shark: "Red is mine. Stay off my side of the board."
- Turn 41, The Professor: "Statistically, you're overextending, Shark."
- Turn 41, The Hustler: "Anyone want to trade for Pacific? BEST deal of the game!"
- Turn 42, The Turtle: "Pass."

---

YOUR PRIVATE THOUGHT HISTORY:
(Only you can see these — your previous strategic reasoning)

- Turn 38, strategy: "I have Kentucky and Indiana. Illinois completes the Red monopoly.
  I must buy it at any cost."
- Turn 39, opponent_analysis: "The Hustler is desperate with only $500 — I can exploit
  that later for a railroad trade."
- Turn 40, strategy: "Building houses on Red as soon as I complete it is the priority.
  3 houses = $700 rent on Kentucky/Indiana."
- Turn 41, opponent_analysis: "The Professor's Light Blues collect $90-100 rent with
  2 houses. My Red with 3 houses would collect $700. Far superior."
- Turn 42, valuation: "If I buy Illinois at $240, I'll have $810 left. That's enough
  for 3 houses ($450) with $360 buffer. Do it."

---

AVAILABLE ACTIONS FOR THIS DECISION:
You have landed on an unowned property. Your options are:
1. BUY — Purchase Illinois Avenue for $240 (you have $1,050)
2. AUCTION — Decline to buy; property goes to auction where ALL players bid

If you BUY:
  - You pay $240, leaving you with $810
  - You complete the Red monopoly (21, 23, 24)
  - Base rent on all Red properties doubles immediately (even without houses)
  - You can build houses on Red starting next turn ($150/house)

If you AUCTION:
  - All 4 players (including you) can bid any amount
  - You might get it cheaper, but opponents could also buy it
  - WARNING: If Turtle ($3,200 cash) buys it, they block your Red monopoly

---

DECISION REQUIRED:
You landed on Illinois Avenue (position 24, Red, $240), an unowned property.
Your cash: $1,050.

Should you buy this property at full price ($240), or let it go to auction?

---

REQUIRED RESPONSE FORMAT:
You MUST respond using the buy_decision function with this exact structure:

{
  "buy": <true or false>,
  "public_speech": "<what you say out loud to the table — max 30 words, stay in character>",
  "private_thought": "<your internal strategic reasoning — 2-3 sentences explaining WHY>"
}

Example response:
{
  "buy": true,
  "public_speech": "Mine. Red is locked down. Start worrying.",
  "private_thought": "Completes Red monopoly. $810 remaining covers 3 houses at $150
    each ($450) with $360 buffer. Aggressive but optimal."
}
```

### What the LLM would return:

```json
{
  "buy": true,
  "public_speech": "Mine. Red is locked down. Start worrying.",
  "private_thought": "Illinois completes my Red monopoly. At $240, I still have $810
    left — enough for 3 houses immediately next turn at $150 each. That leaves $360
    buffer. Professor's Light Blues max out at $600 hotel rent. My Red maxes at $1100.
    No contest."
}
```

---

## 5. Layer-by-Layer Specification

### Layer 1: Packet Metadata (MISSING — Must Add)

**Currently:** Not included.
**Should include:**

```
=== DECISION PACKET ===
Agent: The Shark (Player 0)
Turn: 42
Decision #: 7 (cumulative decisions this game)
Phase: PROPERTY_LANDING | PRE_ROLL | POST_ROLL | AUCTION | TRADE | JAIL | BANKRUPTCY
Timestamp: 2026-02-11T14:23:07Z
```

This gives the agent a sense of game progression and allows it to track its own
decision history across the game.

### Layer 2: Personality System Prompt (EXISTS — Working)

Defined in `backend/src/monopoly/agents/personalities.py`.
Each agent gets ~300-400 words covering personality, strategy guidelines, speech
style, and opponent descriptions. See [Section 8](#8-agent-personality-configs) for
all four personalities.

### Layer 3: Monopoly Rules Summary (EXISTS — Working)

A static ~120-word rules reference included in every prompt.
See the example prompt above for the exact text.

### Layer 4: Full Board State (MISSING — Must Add)

**Currently:** The prompt shows bare integers:
```
Your position: 24
Your properties: [21, 23]
Opponents:
- Player 1 (The Professor): $2150, position 5, 3 properties
```

**Should show:** All 40 spaces with names, owners, buildings, rents, player
positions, and monopoly status. See the ideal example in Section 4.

**Data source:** All this data exists in the engine:
- `backend/src/monopoly/engine/board.py` — Property names, prices, rent tables, color groups
- `GameView.property_ownership` — Who owns what
- `GameView.houses_on_board` — Building counts per position
- `GameView.opponents` — Player positions and properties

It just needs to be formatted into the prompt instead of sending bare integers.

### Layer 5: Your State / Opponent States (EXISTS — Needs Enhancement)

**Currently:** Exists as `GameView` dataclass. See Section 4 for the enhanced format
that includes property names, rent calculations, and monopoly proximity warnings.

**Key enhancement:** Show property NAMES and RENTS, not just position numbers.
Instead of `Your properties: [21, 23]`, show:
```
Properties owned:
  - 21 Kentucky Avenue (Red) — 0 houses, rent $36 (monopoly base x2)
  - 23 Indiana Avenue (Red) — 0 houses, rent $36 (monopoly base x2)
```

### Layer 6: Public Conversation History (EXISTS but BROKEN)

**Currently:** Managed by `ContextManager` in `backend/src/monopoly/agents/context.py`.
The code to build conversation context exists and works, BUT each agent has an
isolated context that only contains its own messages.

- **Sliding window:** Last 10 turns verbatim, older turns summarized
- **Summarizer:** Uses gpt-4o-mini (temp 0.3, max 150 tokens) to compress old messages
- **Format:** `"Turn {N}, {Player Name}: "{message}""`

**Bug:** Agents never hear each other. Must fix by sharing a single ContextManager
per game or broadcasting messages after each decision.

### Layer 7: Private Thought History (EXISTS — Working)

Last 5 private thoughts included verbatim. Older thoughts discarded.

Each thought has:
- `thought: str` — The strategic reasoning
- `turn_number: int` — When the agent thought this
- `category: str` — "strategy", "valuation", "opponent_analysis", "trade_evaluation", "risk_assessment"

**Format in prompt:**
```
Your previous strategic thoughts:
- Turn 38, strategy: "I have Kentucky and Indiana. Illinois completes the Red monopoly."
- Turn 39, opponent_analysis: "The Hustler is desperate — I can exploit that later."
```

### Layer 8: Available Actions (MISSING — Must Add)

**Currently:** The prompt says "Respond using the buy_decision function" but never
tells the agent what actions are available or what their consequences are.

**Should include:** An explicit list of legal moves with their consequences.
See [Section 6](#6-available-actions-per-decision-type) for the full specification.

### Layer 9: Decision Context (EXISTS — Needs Enhancement)

The decision-specific prompt section. Currently includes the question but should
also include the available actions and consequence analysis.

### Layer 10: Required Output Format (PARTIALLY EXISTS — Needs Explicit Spec)

**Currently:** The output format is implicitly defined by the function calling schema
or Gemini structured output schema. The agent is told "Respond using the X function"
but never shown an explicit JSON template.

**Should include:** An explicit "REQUIRED RESPONSE FORMAT" section showing the exact
JSON structure with field descriptions and an example response.

---

## 6. Available Actions per Decision Type

Every decision packet should include an explicit list of what the agent CAN do.

### Pre-Roll Phase
```
AVAILABLE ACTIONS:
You are about to roll the dice. Before rolling, you may:
1. PROPOSE_TRADE — Offer a trade to any opponent (properties, cash, jail cards)
2. BUILD — Build houses/hotels on your monopoly color groups (must build evenly)
3. MORTGAGE — Mortgage unimproved properties for cash (receive mortgage value)
4. UNMORTGAGE — Pay mortgage + 10% to unmortgage a property
5. DO_NOTHING — End pre-roll phase and roll the dice

You may take multiple actions (e.g., mortgage + build + propose trade).

Your buildable properties: [list with names, costs, current houses]
Your mortgageable properties: [list with names, mortgage values]
Your unmortgageable properties: [list with names, unmortgage costs]
```

### Buy or Auction
```
AVAILABLE ACTIONS:
1. BUY — Purchase {property_name} for ${price}
   → Consequence: cash reduced to ${remaining}, you gain {property description}
2. AUCTION — Decline to buy; all players bid
   → Consequence: you might get it cheaper, but opponents could buy it too
```

### Auction Bid
```
AVAILABLE ACTIONS:
1. BID $X — Place a bid (must be higher than current bid of ${current})
   → Maximum you can bid: ${your_cash}
2. BID $0 — Withdraw from auction
   → Property goes to highest remaining bidder
```

### Trade Proposal
```
AVAILABLE ACTIONS:
1. PROPOSE_TRADE — Offer a trade to one opponent
   → You can offer/request: properties (without buildings), cash, jail cards
   → Tradeable properties: {list with names}
2. SKIP — Don't propose any trade this turn
```

### Trade Response
```
AVAILABLE ACTIONS:
1. ACCEPT — Accept the trade as proposed
   → You give: {items}. You receive: {items}.
2. REJECT — Decline the trade
   → No exchange occurs.
```

### Jail Action
```
AVAILABLE ACTIONS:
1. PAY_FINE — Pay $50 to leave jail immediately (cash: ${your_cash})
2. USE_CARD — Use a Get Out of Jail Free card (you have {count})
3. ROLL_DOUBLES — Try to roll doubles to escape (attempt {N} of 3)
   → If doubles: leave jail free. If not: stay in jail.
   → After 3 failed attempts: forced to pay $50.
```

### Post-Roll Phase
```
AVAILABLE ACTIONS:
After landing, you may:
1. BUILD — Build houses/hotels on monopoly properties
2. MORTGAGE — Mortgage unimproved properties
3. UNMORTGAGE — Pay to unmortgage properties
4. DO_NOTHING — End your turn

Your buildable properties: [list with names, costs, current houses]
```

### Bankruptcy Resolution
```
AVAILABLE ACTIONS:
You owe ${amount} and have ${cash}. You must raise ${shortfall}.
1. SELL_HOUSES — Sell houses for half their build cost
   → Sellable: {list with names, sell prices}
2. SELL_HOTELS — Sell hotels (requires 4 houses per property from bank)
   → Sellable: {list with names, sell prices}
3. MORTGAGE — Mortgage unimproved properties
   → Mortgageable: {list with names, mortgage values}
4. DECLARE_BANKRUPTCY — Give up. All assets go to creditor.
   → Only use if you cannot raise enough funds.
```

---

## 7. Required Output Specification (What Agents Must Return)

Every agent response MUST include these three fields plus decision-specific fields.

### Common Fields (Always Required)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `public_speech` | string | What the agent says aloud to all players | Max 30 words. Must match personality speech style. |
| `private_thought` | string | Agent's internal strategic reasoning | 2-3 sentences. Explains the WHY behind the decision. |

### Decision-Specific Output Schemas

#### 1. Pre-Roll Decision → `pre_roll_decision`
```json
{
  "actions": ["build:21:house", "mortgage:14"],
  "public_speech": "Building on Kentucky. My empire grows.",
  "private_thought": "Adding houses to Red increases rent from $36 to $90. Worth the $150."
}
```
**Processing:** Each action string is parsed and executed by the engine.

#### 2. Buy Decision → `buy_decision`
```json
{
  "buy": true,
  "public_speech": "Mine. Red is locked down.",
  "private_thought": "Completes Red monopoly. Can build houses next turn."
}
```
**Processing:** `buy=true` → engine deducts price, assigns property. `buy=false` → auction starts.

#### 3. Auction Bid → `auction_bid_decision`
```json
{
  "bid": 180,
  "public_speech": "One-eighty. Try to keep up.",
  "private_thought": "I'll go up to $200 but no higher — need cash for houses."
}
```
**Processing:** Bid validated (≤ cash, > current bid). Highest bid wins. Bid 0 = withdraw.

#### 4. Trade Proposal → `trade_decision`
```json
{
  "propose_trade": true,
  "target_player": 3,
  "offer_properties": [1],
  "request_properties": [16],
  "offer_cash": 50,
  "request_cash": 0,
  "offer_jail_cards": 0,
  "request_jail_cards": 0,
  "public_speech": "Turtle, I'll sweeten the deal. Mediterranean plus $50 for St. James.",
  "private_thought": "If Turtle gives up St. James, they can't complete Orange. Worth overpaying."
}
```
**Processing:** Trade proposal sent to target player's `respond_to_trade()`. If accepted,
engine swaps assets.

#### 5. Trade Response → `trade_response_decision`
```json
{
  "accept": false,
  "public_speech": "No.",
  "private_thought": "St. James is part of my Orange strategy. Not giving it up for Mediterranean."
}
```
**Processing:** `accept=true` → trade executes. `accept=false` → trade cancelled.

#### 6. Jail Action → `jail_action_decision`
```json
{
  "action": "roll_doubles",
  "public_speech": "I'll roll my way out.",
  "private_thought": "Early in game — free turns in jail protect me from rent. Try doubles first."
}
```
**Processing:** Engine validates (e.g., can't USE_CARD with 0 cards). Executes action.

#### 7. Post-Roll Decision → `post_roll_decision`
```json
{
  "builds": [
    {"position": 21, "type": "house"},
    {"position": 23, "type": "house"},
    {"position": 24, "type": "house"}
  ],
  "mortgages": [],
  "unmortgages": [],
  "public_speech": "Three houses on Red. Rent just went through the roof.",
  "private_thought": "Building evenly across Red: 1 house each = $90/250/100 rent. $450 invested."
}
```
**Processing:** Engine validates even-building rule, sufficient cash, house availability.

#### 8. Bankruptcy Resolution → `bankruptcy_decision`
```json
{
  "sell_houses": [21, 23],
  "sell_hotels": [],
  "mortgage": [24],
  "declare_bankruptcy": false,
  "public_speech": "I'm not done yet.",
  "private_thought": "Selling 2 houses frees $150. Mortgaging Illinois adds $120. Total $270 raised."
}
```
**Processing:** Engine sells buildings at half cost, mortgages properties, checks if debt is covered.
If `declare_bankruptcy=true`, player is eliminated and assets transfer to creditor.

### How Responses Are Processed

```
LLM Response
    ↓
Parse JSON (function call arguments or structured output)
    ↓
Validate fields (types, ranges, affordability)
    ↓
Record public_speech → ContextManager.add_public_message()  ← MUST broadcast to all agents
Record private_thought → ContextManager.add_private_thought()
    ↓
Execute game action (buy, bid, trade, build, etc.)
    ↓
Emit events → EventBus → WebSocket → Frontend
    ↓
  AGENT_SPOKE event (public_speech → ConversationPanel)
  AGENT_THOUGHT event (private_thought → ThoughtPanel)
  Game action event (PROPERTY_BOUGHT, TRADE_COMPLETED, etc.)
```

---

## 8. Agent Personality Configs

All defined in `backend/src/monopoly/agents/personalities.py`.

| Agent | Model | Temperature | Archetype |
|-------|-------|-------------|-----------|
| **The Shark** (Player 0) | gpt-3.5-turbo | 0.7 | Aggressive dominator |
| **The Professor** (Player 1) | gpt-3.5-turbo | 0.3 | Analytical optimizer |
| **The Hustler** (Player 2) | gpt-3.5-turbo | 1.0 | Charismatic deal-maker |
| **The Turtle** (Player 3) | gpt-3.5-turbo | 0.2 | Ultra-conservative survivor |

### Behavioral Parameters (Fallback Heuristics)

| Parameter | Shark | Professor | Hustler | Turtle |
|-----------|-------|-----------|---------|--------|
| Buy Threshold | 0.95 | 0.70 | 0.80 | 0.50 |
| Trade Frequency | 0.80 | 0.40 | 0.95 | 0.10 |
| Max Trade Overpay % | 30% | 5% | 20% | 0% |
| Min Cash Reserve | $100 | $200 | $100 | $500 |
| Build Aggression | 0.90 | 0.60 | 0.70 | 0.30 |
| Auction Max Multiplier | 1.50x | 1.10x | 1.30x | 0.90x |
| Jail Pay Threshold | 0.80 | 0.50 | 0.60 | 0.30 |

---

## 9. LLM API Call Parameters

### OpenAI (Function Calling)

```python
response = await client.chat.completions.create(
    model="gpt-3.5-turbo",           # From personality config
    messages=[{
        "role": "system",
        "content": <full prompt from sections above>
    }],
    tools=[{
        "type": "function",
        "function": {
            "name": "<decision_function_name>",
            "description": "<what this decision does>",
            "parameters": <json schema for output>
        }
    }],
    tool_choice={"type": "function", "function": {"name": "<decision_function_name>"}},
    temperature=<personality.temperature>,  # 0.2 to 1.0
    max_tokens=500,
    timeout=30,
)
```

### Gemini (Structured Output)

```python
response = await model.generate_content_async(
    <full prompt from sections above>,
    generation_config=GenerationConfig(
        response_mime_type="application/json",
        response_schema=<json schema for output>,
        temperature=<personality.temperature>,  # 0.2 to 1.0
        max_output_tokens=500,
    ),
    request_options={"timeout": 30},
)
```

### Retry & Fallback Logic

1. **Attempt 1**: Call LLM with full prompt
2. **Attempt 2**: Retry on failure
3. **Fallback**: Use heuristic defaults if both attempts fail:
   - Buy: buy if `cash >= price * 2`
   - Auction: bid `current_bid + 10` up to `price * auction_max_multiplier`
   - Trade: skip (return None)
   - Jail: roll doubles
   - Bankruptcy: mortgage everything, then declare bankruptcy

### Token Usage Tracking

Both adapters track cumulative token usage per agent:
```python
self.token_usage = {
    "prompt_tokens": <accumulated>,
    "completion_tokens": <accumulated>
}
```

---

## 10. Gap Analysis & Recommendations

### Summary of Issues

| # | Issue | Severity | Status | Location |
|---|-------|----------|--------|----------|
| 1 | Agents can't hear each other (isolated contexts) | CRITICAL | BROKEN | `openai_agent.py:48`, `gemini_agent.py` |
| 2 | No board reference (bare position integers) | HIGH | MISSING | `_build_base_prompt()` in both agents |
| 3 | AGENT_SPOKE/THOUGHT events never emitted | HIGH | BROKEN | `game_runner.py` |
| 4 | No packet metadata (decision #, phase tracking) | MEDIUM | MISSING | `_build_base_prompt()` |
| 5 | No available actions list | MEDIUM | MISSING | Decision context sections |
| 6 | No explicit output format in prompt | MEDIUM | MISSING | Decision context sections |
| 7 | No property names in game state | HIGH | MISSING | `_format_opponents()`, state formatting |
| 8 | No rent tables in prompt | MEDIUM | MISSING | Board reference |
| 9 | No monopoly status summary | MEDIUM | MISSING | Game state section |
| 10 | All agents use gpt-3.5-turbo | LOW | DESIGN | `personalities.py` |
| 11 | Opponent mortgage status hidden | LOW | MISSING | `OpponentView` missing `mortgaged` |

### Recommended Fix Order

1. **Fix cross-agent messaging** (#1) — Without this, nothing else matters. Agents
   must be able to hear each other for negotiations to work.

2. **Add full board state to prompt** (#2, #7, #8, #9) — Include property names,
   owners, buildings, rents, and monopoly status so agents can actually reason about
   the board.

3. **Emit AGENT_SPOKE/THOUGHT events** (#3) — So the frontend can display
   conversations and thoughts.

4. **Add available actions** (#5) — Explicit list of legal moves per decision point.

5. **Add output specification** (#6) — Show the exact JSON format expected.

6. **Add packet metadata** (#4) — Decision number and phase tracking.

7. **Consider model upgrades** (#10) — gpt-3.5-turbo may not be strong enough for
   strategic Monopoly reasoning with these richer prompts. Consider gpt-4o-mini or
   gpt-4o.
