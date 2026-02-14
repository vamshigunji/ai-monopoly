# 🏘️ Asset Panel Display Example

## How the Asset Panel Shows Multiple Properties

The Asset Panel on the right side of the screen displays all properties owned by the selected player. Here's what it looks like with 5 properties:

---

## Example: The Shark with 5 Properties

### Header (Dropdown Selector)
```
┌────────────────────────────────────┐
│ Asset Details                      │
│ ┌────────────────────────────────┐ │
│ │ 🦈 The Shark              ▼    │ │  ← Click to switch players
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

### Summary Section
```
┌────────────────────────────────────┐
│         Cash           Properties  │
│        $670                5       │
│                                    │
│    Property Value    Total Worth   │
│         $500            $1,170     │
└────────────────────────────────────┘
```

### Properties List (Scrollable)
```
┌────────────────────────────────────┐
│ ┃ Mediterranean Avenue      $60    │ ← Brown color bar on left
│ ┃                                  │
│ ┃ Rent: $2                         │
├────────────────────────────────────┤
│ ┃ Baltic Avenue             $60    │ ← Brown color bar
│ ┃                                  │
│ ┃ Rent: $4                         │
├────────────────────────────────────┤
│ ┃ Oriental Avenue          $100    │ ← Light blue color bar
│ ┃                                  │
│ ┃ Rent: $6                         │
├────────────────────────────────────┤
│ ┃ Vermont Avenue           $100    │ ← Light blue color bar
│ ┃                                  │
│ ┃ Rent: $6                         │
├────────────────────────────────────┤
│ ┃ Tennessee Avenue         $180    │ ← Orange color bar
│ ┃                                  │
│ ┃ Rent: $14                        │
└────────────────────────────────────┘
```

### Footer
```
┌────────────────────────────────────┐
│ 5 properties · Total value: $500   │
└────────────────────────────────────┘
```

---

## With Houses/Hotels

If a property has houses or a hotel:

```
┌────────────────────────────────────┐
│ ┃ Mediterranean Avenue      $60    │
│ ┃ 🏠🏠 2 houses                     │ ← Shows house count
│ ┃ Rent: $30                        │ ← Rent increases with houses
├────────────────────────────────────┤
│ ┃ Baltic Avenue             $60    │
│ ┃ 🏨 Hotel                         │ ← Shows hotel icon
│ ┃ Rent: $250                       │ ← Maximum rent!
└────────────────────────────────────┘
```

---

## When a Property is Mortgaged

```
┌────────────────────────────────────┐
│ ┃ Oriental Avenue          $100    │
│ ┃ 🔒 MORTGAGED                     │ ← Shows mortgage status
│ ┃ Rent: $0 (mortgaged)             │
└────────────────────────────────────┘
```

---

## Scrolling Behavior

If a player owns more than ~6 properties, the list becomes scrollable:

```
┌────────────────────────────────────┐
│ Asset Details                      │
│ ┌────────────────────────────────┐ │
│ │ 🦈 The Shark              ▼    │ │
│ └────────────────────────────────┘ │
├────────────────────────────────────┤
│         Cash           Properties  │
│        $450                12      │ ← Many properties!
│                                    │
│    Property Value    Total Worth   │
│       $1,780           $2,230      │
├────────────────────────────────────┤
│ ┃ Mediterranean Avenue      $60    │
│ ┃ Rent: $2                         │
├────────────────────────────────────┤
│ ┃ Baltic Avenue             $60    │  ↑ Scroll up
│ ┃ Rent: $4                         │  │
├────────────────────────────────────┤  │ Scrollable
│ ┃ Oriental Avenue          $100    │  │ area
│ ┃ Rent: $6                         │  │
├────────────────────────────────────┤  │
│ ... (more properties below) ...    │  ↓ Scroll down
│                                    │
├────────────────────────────────────┤
│ 12 properties · Total value: $1,780│
└────────────────────────────────────┘
```

---

## Color-Coded by Monopoly Status

The left border color shows the property's color group:

```
BROWN     ┃ Mediterranean Avenue
BROWN     ┃ Baltic Avenue
L.BLUE    ┃ Oriental Avenue
L.BLUE    ┃ Vermont Avenue
L.BLUE    ┃ Connecticut Avenue    ← Complete monopoly!
ORANGE    ┃ Tennessee Avenue
RED       ┃ Kentucky Avenue
YELLOW    ┃ Atlantic Avenue
GREEN     ┃ Pennsylvania Avenue
D.BLUE    ┃ Park Place
```

---

## Empty State

When a player owns **0 properties**:

```
┌────────────────────────────────────┐
│ Asset Details                      │
│ ┌────────────────────────────────┐ │
│ │ 🐢 The Turtle             ▼    │ │
│ └────────────────────────────────┘ │
├────────────────────────────────────┤
│         Cash           Properties  │
│       $1500                0       │
│                                    │
│    Property Value    Total Worth   │
│          $0            $1,500      │
├────────────────────────────────────┤
│                                    │
│          🐢                        │
│                                    │
│   No properties owned yet          │
│                                    │
│                                    │
└────────────────────────────────────┘
```

---

## Comparison: All 4 Agents

| Agent | Properties | Property Value | Total Worth |
|-------|-----------|----------------|-------------|
| 🦈 Shark | 5 | $500 | $1,170 |
| 🎓 Professor | 3 | $350 | $1,550 |
| 🎭 Hustler | 2 | $280 | $880 |
| 🐢 Turtle | 2 | $580 | $2,380 |

Select each agent from the dropdown to see their unique portfolio!

---

## Technical Implementation

The Asset Panel component:
1. **Fetches player data** from `gameState.players[selectedAssetAgent]`
2. **Maps through properties** array to get all positions
3. **Looks up each property** in BOARD_SPACES to get name, price, color
4. **Calculates rent** based on houses/hotels
5. **Displays in scrollable list** with color-coded borders

All data updates in real-time via WebSocket events!

---

## Testing the Asset Panel

1. Start a game
2. Wait for players to acquire properties (5-10 turns)
3. Click the dropdown at top of Asset Panel
4. Select "🦈 The Shark"
5. You should see:
   - Cash amount
   - Number of properties
   - Total property value
   - List of all owned properties
   - Rent values for each

Try switching between agents to see different portfolios!
