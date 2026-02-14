# Monopoly Game Rules Reference

> **Purpose**: This document serves as the authoritative specification for implementing a digital Monopoly game engine. All rules follow the official Hasbro Monopoly rules unless otherwise noted. Every value, card, space, and rule needed for a complete implementation is documented here.

---

## Table of Contents

1. [Board Layout (All 40 Spaces)](#1-board-layout-all-40-spaces)
2. [Complete Property Rent Tables](#2-complete-property-rent-tables)
3. [Railroads](#3-railroads)
4. [Utilities](#4-utilities)
5. [Chance Cards (All 16)](#5-chance-cards-all-16)
6. [Community Chest Cards (All 16)](#6-community-chest-cards-all-16)
7. [Complete Game Rules](#7-complete-game-rules)
8. [Edge Cases and Special Rules](#8-edge-cases-and-special-rules)

---

## 1. Board Layout (All 40 Spaces)

The board consists of 40 spaces numbered 0-39 arranged clockwise. Players move in ascending order (0 -> 1 -> 2 -> ... -> 39 -> 0).

| Position | Name | Type | Color Group | Price |
|----------|------|------|-------------|-------|
| 0 | GO | Corner | -- | -- |
| 1 | Mediterranean Avenue | Property | Brown | $60 |
| 2 | Community Chest | Card Draw | -- | -- |
| 3 | Baltic Avenue | Property | Brown | $60 |
| 4 | Income Tax | Tax | -- | $200 |
| 5 | Reading Railroad | Railroad | -- | $200 |
| 6 | Oriental Avenue | Property | Light Blue | $100 |
| 7 | Chance | Card Draw | -- | -- |
| 8 | Vermont Avenue | Property | Light Blue | $100 |
| 9 | Connecticut Avenue | Property | Light Blue | $120 |
| 10 | Jail / Just Visiting | Corner | -- | -- |
| 11 | St. Charles Place | Property | Pink | $140 |
| 12 | Electric Company | Utility | -- | $150 |
| 13 | States Avenue | Property | Pink | $140 |
| 14 | Virginia Avenue | Property | Pink | $160 |
| 15 | Pennsylvania Railroad | Railroad | -- | $200 |
| 16 | St. James Place | Property | Orange | $180 |
| 17 | Community Chest | Card Draw | -- | -- |
| 18 | Tennessee Avenue | Property | Orange | $180 |
| 19 | New York Avenue | Property | Orange | $200 |
| 20 | Free Parking | Corner | -- | -- |
| 21 | Kentucky Avenue | Property | Red | $220 |
| 22 | Chance | Card Draw | -- | -- |
| 23 | Indiana Avenue | Property | Red | $220 |
| 24 | Illinois Avenue | Property | Red | $240 |
| 25 | B&O Railroad | Railroad | -- | $200 |
| 26 | Atlantic Avenue | Property | Yellow | $260 |
| 27 | Ventnor Avenue | Property | Yellow | $260 |
| 28 | Water Works | Utility | -- | $150 |
| 29 | Marvin Gardens | Property | Yellow | $280 |
| 30 | Go To Jail | Corner | -- | -- |
| 31 | Pacific Avenue | Property | Green | $300 |
| 32 | North Carolina Avenue | Property | Green | $300 |
| 33 | Community Chest | Card Draw | -- | -- |
| 34 | Pennsylvania Avenue | Property | Green | $320 |
| 35 | Short Line Railroad | Railroad | -- | $200 |
| 36 | Chance | Card Draw | -- | -- |
| 37 | Park Place | Property | Dark Blue | $350 |
| 38 | Luxury Tax | Tax | -- | $100 |
| 39 | Boardwalk | Property | Dark Blue | $400 |

### Space Types Summary

| Type | Positions | Count |
|------|-----------|-------|
| Corner (GO, Jail, Free Parking, Go To Jail) | 0, 10, 20, 30 | 4 |
| Color Properties | 1, 3, 6, 8, 9, 11, 13, 14, 16, 18, 19, 21, 23, 24, 26, 27, 29, 31, 32, 34, 37, 39 | 22 |
| Railroads | 5, 15, 25, 35 | 4 |
| Utilities | 12, 28 | 2 |
| Chance | 7, 22, 36 | 3 |
| Community Chest | 2, 17, 33 | 3 |
| Tax | 4, 38 | 2 |

### Color Groups Summary

| Color Group | Properties | Count | House Cost |
|-------------|-----------|-------|------------|
| Brown | Mediterranean Ave, Baltic Ave | 2 | $50 |
| Light Blue | Oriental Ave, Vermont Ave, Connecticut Ave | 3 | $50 |
| Pink | St. Charles Place, States Ave, Virginia Ave | 3 | $100 |
| Orange | St. James Place, Tennessee Ave, New York Ave | 3 | $100 |
| Red | Kentucky Ave, Indiana Ave, Illinois Ave | 3 | $150 |
| Yellow | Atlantic Ave, Ventnor Ave, Marvin Gardens | 3 | $150 |
| Green | Pacific Ave, North Carolina Ave, Pennsylvania Ave | 3 | $200 |
| Dark Blue | Park Place, Boardwalk | 2 | $200 |

---

## 2. Complete Property Rent Tables

Rent values are listed as: Base Rent / Monopoly Rent (2x base) / 1 House / 2 Houses / 3 Houses / 4 Houses / Hotel.

Mortgage value is always half the purchase price.

### Brown Group (House Cost: $50)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| Mediterranean Avenue | 1 | $60 | $30 | $2 | $4 | $10 | $30 | $90 | $160 | $250 |
| Baltic Avenue | 3 | $60 | $30 | $4 | $8 | $20 | $60 | $180 | $320 | $450 |

### Light Blue Group (House Cost: $50)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| Oriental Avenue | 6 | $100 | $50 | $6 | $12 | $30 | $90 | $270 | $400 | $550 |
| Vermont Avenue | 8 | $100 | $50 | $6 | $12 | $30 | $90 | $270 | $400 | $550 |
| Connecticut Avenue | 9 | $120 | $60 | $8 | $16 | $40 | $100 | $300 | $450 | $600 |

### Pink Group (House Cost: $100)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| St. Charles Place | 11 | $140 | $70 | $10 | $20 | $50 | $150 | $450 | $625 | $750 |
| States Avenue | 13 | $140 | $70 | $10 | $20 | $50 | $150 | $450 | $625 | $750 |
| Virginia Avenue | 14 | $160 | $80 | $12 | $24 | $60 | $180 | $500 | $700 | $900 |

### Orange Group (House Cost: $100)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| St. James Place | 16 | $180 | $90 | $14 | $28 | $70 | $200 | $550 | $750 | $950 |
| Tennessee Avenue | 18 | $180 | $90 | $14 | $28 | $70 | $200 | $550 | $750 | $950 |
| New York Avenue | 19 | $200 | $100 | $16 | $32 | $80 | $220 | $600 | $800 | $1000 |

### Red Group (House Cost: $150)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| Kentucky Avenue | 21 | $220 | $110 | $18 | $36 | $90 | $250 | $700 | $875 | $1050 |
| Indiana Avenue | 23 | $220 | $110 | $18 | $36 | $90 | $250 | $700 | $875 | $1050 |
| Illinois Avenue | 24 | $240 | $120 | $20 | $40 | $100 | $300 | $750 | $925 | $1100 |

### Yellow Group (House Cost: $150)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| Atlantic Avenue | 26 | $260 | $130 | $22 | $44 | $110 | $330 | $800 | $975 | $1150 |
| Ventnor Avenue | 27 | $260 | $130 | $22 | $44 | $110 | $330 | $800 | $975 | $1150 |
| Marvin Gardens | 29 | $280 | $140 | $24 | $48 | $120 | $360 | $850 | $1025 | $1200 |

### Green Group (House Cost: $200)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| Pacific Avenue | 31 | $300 | $150 | $26 | $52 | $130 | $390 | $900 | $1100 | $1275 |
| North Carolina Avenue | 32 | $300 | $150 | $26 | $52 | $130 | $390 | $900 | $1100 | $1275 |
| Pennsylvania Avenue | 34 | $320 | $160 | $28 | $56 | $150 | $450 | $1000 | $1200 | $1400 |

### Dark Blue Group (House Cost: $200)

| Property | Position | Price | Mortgage | Base | Monopoly | 1 House | 2 Houses | 3 Houses | 4 Houses | Hotel |
|----------|----------|-------|----------|------|----------|---------|----------|----------|----------|-------|
| Park Place | 37 | $350 | $175 | $35 | $70 | $175 | $500 | $1100 | $1300 | $1500 |
| Boardwalk | 39 | $400 | $200 | $50 | $100 | $200 | $600 | $1400 | $1700 | $2000 |

---

## 3. Railroads

All four railroads cost **$200** each. Mortgage value: **$100** each.

| Railroad | Position |
|----------|----------|
| Reading Railroad | 5 |
| Pennsylvania Railroad | 15 |
| B&O Railroad | 25 |
| Short Line Railroad | 35 |

### Railroad Rent Schedule

Rent is determined by how many railroads the **same owner** controls:

| Railroads Owned | Rent |
|----------------|------|
| 1 | $25 |
| 2 | $50 |
| 3 | $100 |
| 4 | $200 |

**Note**: The rent formula doubles with each additional railroad: `$25 * 2^(n-1)` where `n` is the number of railroads owned.

**Special case**: The Chance card "Advance to nearest Railroad" requires the landing player to pay **double** the normal rent if the railroad is owned. If unowned, the player may buy it at $200.

---

## 4. Utilities

Both utilities cost **$150** each. Mortgage value: **$75** each.

| Utility | Position |
|---------|----------|
| Electric Company | 12 |
| Water Works | 28 |

### Utility Rent Schedule

Rent is determined by the dice roll that brought the player to the utility, multiplied by a factor based on how many utilities the **same owner** controls:

| Utilities Owned | Rent Multiplier |
|----------------|-----------------|
| 1 | 4x the dice roll |
| 2 | 10x the dice roll |

**Example**: If a player rolls a 9 and lands on a utility where the owner has both utilities, rent = 9 * 10 = $90.

**Special case**: The Chance card "Advance to nearest Utility" requires the player to roll the dice again and pay **10x** the roll regardless of how many utilities the owner has. If unowned, the player may buy it at $150.

---

## 5. Chance Cards (All 16)

The Chance deck contains exactly 16 cards. Before the game begins, the deck is shuffled. When a player draws a card, they follow its instructions and return it to the bottom of the deck (except "Get Out of Jail Free" which is held until used or traded).

Chance card draw positions on the board: **7, 22, 36**.

| # | Card Text | Effect | Implementation Notes |
|---|-----------|--------|---------------------|
| 1 | Advance to Boardwalk | Move to position 39 | Do not collect $200 (player moves forward, but Boardwalk is typically ahead or behind depending on current position; since this is a direct "advance to" it does not trigger GO salary unless the path crosses GO) |
| 2 | Advance to GO (Collect $200) | Move to position 0, collect $200 | Always collect $200 |
| 3 | Advance to Illinois Avenue. If you pass GO, collect $200 | Move to position 24 | Collect $200 if current position > 24 (wrapping past GO) |
| 4 | Advance to St. Charles Place. If you pass GO, collect $200 | Move to position 11 | Collect $200 if current position > 11 (wrapping past GO) |
| 5 | Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled | Move to nearest railroad (5, 15, 25, or 35) | From position 7: advance to 15. From position 22: advance to 25. From position 36: advance to 5 (collect $200 for passing GO). Pay 2x normal railroad rent if owned. |
| 6 | Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled | Same as card 5 | There are two copies of this card in the Chance deck |
| 7 | Advance to the nearest Utility. If unowned, you may buy it from the Bank. If owned, throw dice and pay owner a total of 10 times the amount thrown | Move to nearest utility (12 or 28) | From position 7: advance to 12. From position 22: advance to 28. From position 36: advance to 12 (collect $200 for passing GO). If owned, roll dice and pay 10x regardless of how many utilities owner has. |
| 8 | Bank pays you dividend of $50 | Collect $50 from the bank | Credit player $50 |
| 9 | Get Out of Jail Free | Player keeps this card until used or traded | Remove from deck; return to bottom of Chance deck when used |
| 10 | Go Back 3 Spaces | Move backward 3 spaces | From position 7: go to 4 (Income Tax). From position 22: go to 19 (New York Ave). From position 36: go to 33 (Community Chest). Resolve the space landed on normally. |
| 11 | Go to Jail. Go directly to Jail, do not pass GO, do not collect $200 | Move to position 10 (Jail) | Player is IN jail, not visiting. Do not collect GO salary. |
| 12 | Make general repairs on all your property. For each house pay $25. For each hotel pay $100 | Pay bank based on buildings owned | Count all houses and hotels across all properties. Pay $25 per house + $100 per hotel. |
| 13 | Speeding fine $15 | Pay $15 to the bank | Debit player $15 |
| 14 | Take a trip to Reading Railroad. If you pass GO, collect $200 | Move to position 5 | Collect $200 if current position > 5 (wrapping past GO) |
| 15 | You have been elected Chairman of the Board. Pay each player $50 | Pay $50 to every other player | Total cost = $50 * (number of other active players) |
| 16 | Your building loan matures. Collect $150 | Collect $150 from the bank | Credit player $150 |

---

## 6. Community Chest Cards (All 16)

The Community Chest deck contains exactly 16 cards. Before the game begins, the deck is shuffled. When a player draws a card, they follow its instructions and return it to the bottom of the deck (except "Get Out of Jail Free" which is held until used or traded).

Community Chest card draw positions on the board: **2, 17, 33**.

| # | Card Text | Effect | Implementation Notes |
|---|-----------|--------|---------------------|
| 1 | Advance to GO (Collect $200) | Move to position 0, collect $200 | Always collect $200 |
| 2 | Bank error in your favor. Collect $200 | Collect $200 from the bank | Credit player $200 |
| 3 | Doctor's fee. Pay $50 | Pay $50 to the bank | Debit player $50 |
| 4 | From sale of stock you get $50 | Collect $50 from the bank | Credit player $50 |
| 5 | Get Out of Jail Free | Player keeps this card until used or traded | Remove from deck; return to bottom of Community Chest deck when used |
| 6 | Go to Jail. Go directly to Jail, do not pass GO, do not collect $200 | Move to position 10 (Jail) | Player is IN jail, not visiting. Do not collect GO salary. |
| 7 | Grand Opera Night. Collect $50 from every player for opening night seats | Collect $50 from every other player | Total income = $50 * (number of other active players) |
| 8 | Income tax refund. Collect $20 | Collect $20 from the bank | Credit player $20 |
| 9 | It is your birthday. Collect $10 from every player | Collect $10 from every other player | Total income = $10 * (number of other active players) |
| 10 | Life insurance matures. Collect $100 | Collect $100 from the bank | Credit player $100 |
| 11 | Hospital fees. Pay $100 | Pay $100 to the bank | Debit player $100 |
| 12 | School fees. Pay $50 | Pay $50 to the bank | Debit player $50 |
| 13 | Receive $25 consultancy fee | Collect $25 from the bank | Credit player $25 |
| 14 | You are assessed for street repairs. $40 per house. $115 per hotel | Pay bank based on buildings owned | Count all houses and hotels across all properties. Pay $40 per house + $115 per hotel. |
| 15 | You have won second prize in a beauty contest. Collect $10 | Collect $10 from the bank | Credit player $10 |
| 16 | You inherit $100 | Collect $100 from the bank | Credit player $100 |

---

## 7. Complete Game Rules

### 7.1 Game Setup

#### Players
- Minimum: 2 players
- Maximum: 8 players (standard edition has 8 tokens)
- Recommended: 3-6 players

#### Starting Money
Each player begins with **$1,500** distributed as follows:

| Denomination | Count | Subtotal |
|-------------|-------|----------|
| $500 | 2 | $1,000 |
| $100 | 2 | $200 |
| $50 | 2 | $100 |
| $20 | 6 | $120 |
| $10 | 5 | $50 |
| $5 | 5 | $25 |
| $1 | 5 | $5 |
| **Total** | **27 bills** | **$1,500** |

**Note for digital implementation**: Denominations are informational only. The engine tracks integer dollar amounts.

#### Initial Setup Steps
1. Each player selects a token (game piece).
2. All players place their tokens on GO (position 0).
3. Both card decks (Chance and Community Chest) are shuffled independently.
4. All properties start unowned, unmortgaged, with no buildings.
5. The bank starts with 32 houses and 12 hotels.
6. Each player rolls two dice; highest total goes first. Re-roll ties.
7. Play proceeds clockwise from the first player.

### 7.2 Turn Sequence

A player's turn consists of the following steps in order:

```
1. PRE-ROLL PHASE (optional actions)
   - Trade with other players
   - Buy/sell houses and hotels
   - Mortgage/unmortgage properties

2. ROLL PHASE
   a. Roll two six-sided dice
   b. Check for third consecutive doubles -> Go to Jail immediately (skip to step 5)
   c. Move token forward (clockwise) by the total of both dice
   d. Resolve the space landed on (see Landing Actions below)

3. POST-ROLL PHASE (optional actions)
   - Trade with other players
   - Buy/sell houses and hotels
   - Mortgage/unmortgage properties

4. DOUBLES CHECK
   - If doubles were rolled (and it wasn't the 3rd consecutive), return to step 2
   - The doubles counter increments each consecutive doubles roll

5. END TURN
   - Reset doubles counter to 0
   - Pass turn to next player clockwise
```

### 7.3 Landing Actions

The action depends on the type of space landed on:

#### Unowned Property (Color Property, Railroad, or Utility)
1. The landing player may **buy** the property at its listed price.
2. If the player **declines** to buy, the property goes to **auction immediately**.
3. In the auction, all players (including the one who declined) may bid.
4. The highest bidder pays their bid amount and receives the property.
5. Bidding can start at any amount ($1 minimum).
6. If no player bids, the property remains unowned.

#### Owned Property (Not Mortgaged)
1. The landing player must pay **rent** to the property owner.
2. Rent amount depends on:
   - **Color property**: Base rent, monopoly rent, or house/hotel rent (see rent tables).
   - **Railroad**: Based on how many railroads the owner controls (see Section 3).
   - **Utility**: Based on dice roll and how many utilities the owner controls (see Section 4).
3. **Important**: The owner must **ask for rent** before the next player rolls. If the owner fails to notice, rent is not owed. (Implementation note: in the digital version, rent is always collected automatically.)

#### Owned Property (Mortgaged)
- **No rent is owed.** The landing player pays nothing.

#### GO (Position 0)
- Collect $200 salary when **landing on** or **passing** GO.
- A player can only collect $200 once per pass (not $200 for passing AND $200 for landing).

#### Income Tax (Position 4)
- Pay **$200** to the bank (flat rate, modern rules).

#### Luxury Tax (Position 38)
- Pay **$100** to the bank.

#### Chance (Positions 7, 22, 36)
- Draw the top card from the Chance deck.
- Follow the card's instructions immediately.
- Return the card to the bottom of the deck (unless it is "Get Out of Jail Free").

#### Community Chest (Positions 2, 17, 33)
- Draw the top card from the Community Chest deck.
- Follow the card's instructions immediately.
- Return the card to the bottom of the deck (unless it is "Get Out of Jail Free").

#### Jail / Just Visiting (Position 10)
- If the player lands here by normal movement, they are **Just Visiting** -- no penalty.
- If sent to Jail (by card or "Go To Jail" space), see Jail Rules (Section 7.7).

#### Free Parking (Position 20)
- **Nothing happens.** The player's turn continues normally.
- No money is collected. (This follows official rules; no house rules.)

#### Go To Jail (Position 30)
- Move **directly** to Jail (position 10).
- Do **not** pass GO.
- Do **not** collect $200.
- Turn ends immediately (no doubles re-roll).

### 7.4 Buying Property

- A player may only buy a property when they **land on it** and it is **unowned**.
- The purchase price is the listed price on the board (see Section 1).
- Payment goes to the bank.
- The player receives the title deed card.
- If the player cannot afford or chooses not to buy, the property goes to auction.

### 7.5 Building Houses and Hotels

#### Prerequisites for Building
- The player must own **ALL** properties in a color group (a **monopoly**).
- **None** of the properties in the group can be mortgaged.
- The player must have enough cash to pay the house cost.
- There must be houses available in the bank supply.

#### Even Building Rule
- Houses must be built **evenly** across all properties in a color group.
- The difference in house count between any two properties in the same group can never exceed 1.
- When building: you must build on the property with the fewest houses first.
- When selling: you must sell from the property with the most houses first.

**Example (Orange group: St. James, Tennessee, New York)**:
- Valid: 1-1-1 (one house each), 2-2-1, 2-2-2, 3-3-2, etc.
- Invalid: 2-0-0, 3-1-0, 2-2-0

#### Hotels
- After a property has **4 houses**, the player may upgrade to a **hotel**.
- Cost: the hotel purchase price (same as house cost for that group) + return of 4 houses to the bank.
- Each property can have at most **1 hotel**.
- The 4 returned houses become available for other players.
- **Maximum per property**: 1 hotel (equivalent to 5 houses in rent calculation).

#### Building Supply Limits
- The game contains a maximum of **32 houses** and **12 hotels**.
- If not enough houses are available, the player cannot build.
- A player may **not** skip from houses directly to a hotel without having 4 houses first (in physical game). In digital: the house supply must support 4 houses before converting to hotel.

#### When to Build
- Players may build during their **own turn** (before or after rolling).
- Players may also build **between other players' turns** (optional rule; for simplicity, the digital version may restrict building to the active player's turn).
- Players may **not** build while they owe money.

### 7.6 Mortgage Rules

#### Mortgaging a Property
- A player may mortgage any **unimproved** property they own.
- **All buildings** in the property's color group must be sold before any property in that group can be mortgaged.
- The bank pays the player the **mortgage value** (half the purchase price).
- The property remains owned by the player but is flipped face-down (mortgaged).

#### While Mortgaged
- **No rent** can be collected on a mortgaged property.
- The property **can be traded** to other players.
- The owner still **owns** the property (it counts toward monopoly ownership for rent purposes, but since it is mortgaged, building is not allowed in the group).

#### Unmortgaging a Property
- To unmortgage, the player pays the bank: **mortgage value + 10% interest** (rounded to the nearest dollar if needed).
- Formula: `unmortgage_cost = mortgage_value * 1.10` (round up to nearest whole dollar).

#### Mortgage Values Quick Reference

| Property | Price | Mortgage Value | Unmortgage Cost |
|----------|-------|---------------|-----------------|
| Mediterranean Ave | $60 | $30 | $33 |
| Baltic Ave | $60 | $30 | $33 |
| Oriental Ave | $100 | $50 | $55 |
| Vermont Ave | $100 | $50 | $55 |
| Connecticut Ave | $120 | $60 | $66 |
| St. Charles Place | $140 | $70 | $77 |
| States Ave | $140 | $70 | $77 |
| Virginia Ave | $160 | $80 | $88 |
| St. James Place | $180 | $90 | $99 |
| Tennessee Ave | $180 | $90 | $99 |
| New York Ave | $200 | $100 | $110 |
| Kentucky Ave | $220 | $110 | $121 |
| Indiana Ave | $220 | $110 | $121 |
| Illinois Ave | $240 | $120 | $132 |
| Atlantic Ave | $260 | $130 | $143 |
| Ventnor Ave | $260 | $130 | $143 |
| Marvin Gardens | $280 | $140 | $154 |
| Pacific Ave | $300 | $150 | $165 |
| North Carolina Ave | $300 | $150 | $165 |
| Pennsylvania Ave | $320 | $160 | $176 |
| Park Place | $350 | $175 | $193 |
| Boardwalk | $400 | $200 | $220 |
| Each Railroad | $200 | $100 | $110 |
| Each Utility | $150 | $75 | $83 |

#### Selling Buildings
- Buildings are sold back to the bank at **half their purchase price**.
- Buildings must be sold evenly (reverse of even building rule).
- Hotels are downgraded to 4 houses first (if houses are available), then houses are sold one at a time.
- If not enough houses are available to downgrade a hotel, the player must sell the hotel outright (receive half hotel cost) and sell down to a level the housing supply can support.

| Group | House Cost | House Sell Price | Hotel Cost | Hotel Sell Price |
|-------|-----------|-----------------|------------|-----------------|
| Brown | $50 | $25 | $50 | $25 |
| Light Blue | $50 | $25 | $50 | $25 |
| Pink | $100 | $50 | $100 | $50 |
| Orange | $100 | $50 | $100 | $50 |
| Red | $150 | $75 | $150 | $75 |
| Yellow | $150 | $75 | $150 | $75 |
| Green | $200 | $100 | $200 | $100 |
| Dark Blue | $200 | $100 | $200 | $100 |

### 7.7 Trading Rules

#### What Can Be Traded
- **Properties** (title deed cards) -- improved or unimproved (but buildings must be sold first)
- **Cash** (any amount)
- **Get Out of Jail Free** cards

#### What Cannot Be Traded
- **Buildings** (houses/hotels) -- they must be sold to the bank; they cannot be transferred between players
- **Immunity deals** or future promises (per official rules; these are not enforceable)

#### When Trading Can Occur
- On the active player's turn, before or after rolling.
- Both players involved must agree to the terms.
- Trades must be completed in a single transaction (no installment plans).

#### Trading Mortgaged Properties
When a mortgaged property changes hands via trade:
1. The new owner must **immediately** choose one of two options:
   - **Option A**: Pay 10% of the mortgage value as a **transfer fee** and keep the property mortgaged. Later, to unmortgage, they pay the full mortgage value + another 10% interest.
   - **Option B**: Pay the 10% transfer fee **AND** the full mortgage value to unmortgage the property immediately. (Total = mortgage value + 10% of mortgage value, same as normal unmortgage cost.)
2. The 10% transfer fee is **always** paid regardless of the option chosen.

### 7.8 Jail Rules

#### Ways to Go to Jail
1. Landing on the **"Go To Jail"** space (position 30).
2. Drawing a **"Go to Jail"** card from Chance or Community Chest.
3. Rolling **doubles three times in a row** on the same turn.

#### Entering Jail
- Move directly to position 10 (Jail).
- Do **not** pass GO.
- Do **not** collect $200.
- Your turn ends immediately (even if you rolled doubles that sent you to jail via the 3-doubles rule).

#### While in Jail
- You **can** still:
  - Collect rent on your properties.
  - Trade with other players.
  - Buy and sell houses/hotels.
  - Participate in auctions.
- You **cannot**:
  - Move around the board.

#### Getting Out of Jail
There are four ways to leave jail:

| Method | When | Details |
|--------|------|---------|
| Pay $50 fine | At the **start** of your turn (before rolling) | Pay $50 to the bank, then roll and move normally |
| Use Get Out of Jail Free card | At the **start** of your turn (before rolling) | Return the card to the bottom of its respective deck, then roll and move normally |
| Roll doubles | During your turn's roll | If you roll doubles, you move that number of spaces but do **not** get an extra roll for doubles |
| Forced payment after 3 turns | After failing to roll doubles for 3 turns | You **must** pay $50 and move based on your last (3rd) dice roll |

#### Jail Turn Counting
- Each attempt to roll doubles counts as one jail turn.
- A player has a maximum of 3 turns in jail.
- On the 3rd turn, if no doubles are rolled, the player pays $50 and moves the rolled amount.

### 7.9 Bankruptcy

A player becomes bankrupt when they **owe more money than they can raise** through selling buildings and mortgaging properties.

#### Steps Before Bankruptcy
1. **Sell buildings** back to the bank at half price (following even selling rules).
2. **Mortgage properties** to the bank for their mortgage value.
3. **Trade properties** with other players for cash (if any player is willing).
4. If the player still cannot pay, they are **bankrupt**.

#### Bankruptcy to Another Player
- All remaining assets (properties, cash, Get Out of Jail Free cards) transfer to the **creditor** (the player owed money).
- Mortgaged properties transfer to the creditor. The creditor must immediately decide for each:
  - Pay 10% transfer fee and keep it mortgaged, OR
  - Pay 10% fee + mortgage value to unmortgage it.
- The bankrupt player is **eliminated** from the game.

#### Bankruptcy to the Bank
- This occurs when the player owes the bank (taxes, repair cards, etc.) and cannot pay.
- All properties are **unmortgaged** and auctioned off individually to the remaining players.
- All buildings are returned to the bank supply.
- Any Get Out of Jail Free cards are returned to the bottom of their respective decks.
- Any remaining cash goes to the bank.
- The bankrupt player is **eliminated** from the game.

### 7.10 Winning the Game

#### Standard Victory
- The **last player remaining** after all others are bankrupt wins the game.

#### Timed Game (Optional Variant)
- Set a predetermined time limit or turn limit before the game begins.
- When the limit is reached, the game ends.
- Each player calculates their **total net worth**:
  - Cash on hand
  - Properties at their **printed price** (not mortgage value)
  - Mortgaged properties at **half** their printed price (mortgage value)
  - Houses at **purchase price** each
  - Hotels at **purchase price + 4 house purchase prices** each (total investment)
- The player with the **highest net worth** wins.

---

## 8. Edge Cases and Special Rules

### 8.1 Housing Shortage

- The game contains exactly **32 houses** and **12 hotels**.
- These are a finite shared resource among all players.
- If a player wants to buy houses but not enough are available, they can only buy what is available (following the even building rule).
- **Housing shortage auction**: When two or more players want to buy the last available house(s) at the same time, the houses are auctioned one at a time to the highest bidder.
- A player may **strategically** choose not to upgrade to hotels in order to create a housing shortage for other players. This is a legitimate strategy.

### 8.2 Hotel Downgrade During Housing Shortage

- If a player needs to sell a hotel but there are not enough houses in the bank to replace it with 4 houses, they must sell the hotel outright.
- The player receives half the hotel cost and must reduce to the maximum number of houses the bank can provide (which might be 0).
- The even building rule still applies when selling down.

### 8.3 Property Auction Rules

- Triggered when a player declines to buy an unowned property they landed on.
- **All players** (including the one who declined) may bid.
- Bidding starts at any amount (minimum $1).
- There is no prescribed auction format in official rules; common implementations use ascending open auction.
- The **highest bidder** wins and pays their bid amount to the bank.
- A player cannot bid more than they currently have in cash.
- If **no one bids**, the property remains unowned and no money changes hands.
- If there is a **tie** in sealed-bid format, the tied player closest to the left of the current player (clockwise) wins.

### 8.4 Rent Collection Rules

- **Owner must request rent** before the next player's dice roll (physical game rule).
- **Digital implementation**: Rent is collected automatically when a player lands on an owned property.
- Rent is **not** owed if the property is **mortgaged**.
- Rent is **not** owed if the owner is **bankrupt** (already eliminated).
- A player **cannot** waive rent for another player as a form of trade consideration (per strict official rules; this is sometimes allowed as a house rule).

### 8.5 Collecting $200 for Passing GO

- Collect $200 **every time** you pass over or land on GO.
- This applies when moving by dice roll during normal movement.
- This applies when moved by certain cards that say "If you pass GO, collect $200" or "Advance to GO."
- This does **NOT** apply when a card says "Go directly to Jail" or when landing on "Go To Jail" -- no $200 is collected even if the Jail is "past" GO on the board.
- A player collects $200 only **once** per pass, not once for passing and once for landing.

### 8.6 Get Out of Jail Free Card

- There are **2** Get Out of Jail Free cards in the game total: 1 in Chance, 1 in Community Chest.
- When drawn, the player **keeps** the card (it is removed from its deck).
- It can be **used** at any time the player is in Jail (at the start of their turn, before rolling).
- It can be **traded** or **sold** to another player at any mutually agreed price.
- When used, it is returned to the **bottom** of its respective deck (Chance card returns to Chance deck, Community Chest card returns to Community Chest deck).

### 8.7 Free Parking

- Following **official rules**: nothing happens when landing on Free Parking.
- No money is placed in the center of the board.
- No taxes or fees are collected by landing players.
- This is purely a resting space.

### 8.8 Income Tax

- **Modern rule (implemented)**: Pay a flat **$200** to the bank.
- **Legacy rule (not implemented)**: Player could choose between $200 or 10% of total assets (cash + property printed prices + building costs). The choice had to be made before calculating total assets.
- This implementation uses the modern flat $200 rule.

### 8.9 Luxury Tax

- Pay a flat **$100** to the bank.

### 8.10 Speed Die

- The Speed Die is an optional variant included in some editions.
- It is **NOT** included in this implementation.
- The game uses only two standard six-sided dice.

### 8.11 Rolling Doubles

- If a player rolls doubles (both dice show the same number), they get an **extra turn** after completing their current move.
- Doubles counter resets between turns (only consecutive doubles within the same turn count).
- On the **third consecutive doubles** in a single turn:
  - The player goes directly to Jail.
  - The player does **not** move based on the third roll.
  - The turn ends immediately.
- If a player rolls doubles to get out of Jail, they move but do **not** get an extra turn.

### 8.12 Card Movement and GO

When a card instructs a player to move to a specific location:

| Card Instruction | Passes GO? | Collects $200? |
|-----------------|-----------|----------------|
| "Advance to GO" | N/A (destination is GO) | Yes, always |
| "Advance to [property]" | If movement crosses GO | Yes, if passes GO |
| "Go to Jail" | Passes GO on board layout | **No** (explicitly stated) |
| "Go Back 3 Spaces" | Never (always moves backward) | No |

### 8.13 Landed on by Card vs. Dice

- When a card moves a player to a property, the same landing rules apply as if they rolled the dice to get there.
- If the property is unowned, the player may buy it or it goes to auction.
- If owned, the player pays rent (with special rules for "nearest Railroad" and "nearest Utility" Chance cards as detailed in Section 5).

### 8.14 Insufficient Funds

- If a player cannot pay an amount owed, they must:
  1. Sell buildings (at half price, following even building rules).
  2. Mortgage properties.
  3. Attempt trades with other players.
- Only after exhausting all options does the player go bankrupt.
- A player **cannot** borrow money from the bank or other players (no loans).
- A player **cannot** owe a debt -- it must be settled before their turn ends or they go bankrupt.

### 8.15 Negative Net Worth Situations

- If a player's total possible liquidation value (cash + building sell values + mortgage values) is less than the amount owed, they are bankrupt.
- There is no "debt" state -- players are either solvent or bankrupt.

### 8.16 Multiple Players on Same Space

- Multiple players **can** occupy the same space. There is no restriction.
- No interaction occurs between players sharing a space.

### 8.17 Order of Operations for Complex Turns

When a player's turn involves multiple events (e.g., rolling doubles, drawing cards, etc.), resolve them in order:

1. Roll dice.
2. Check for 3rd consecutive doubles (go to Jail if so; skip remaining steps).
3. Move token.
4. Resolve space (pay rent, draw card, etc.).
5. If a card moves the player, resolve the new space.
6. After all resolutions, if doubles were rolled, roll again (return to step 1).

### 8.18 Bank Cannot Go Bankrupt

- The bank has an unlimited supply of money.
- If the bank runs out of printed money in a physical game, the banker can use slips of paper (IOUs). In the digital version, this is not a concern.
- The bank's supply of **houses and hotels IS limited** (32 houses, 12 hotels).

---

## Appendix A: Quick Reference -- Dice Probabilities

For AI agent decision-making and probability calculations:

| Roll Total | Combinations | Probability | Cumulative |
|-----------|-------------|------------|------------|
| 2 | 1 (1+1) | 2.78% | 2.78% |
| 3 | 2 (1+2, 2+1) | 5.56% | 8.33% |
| 4 | 3 (1+3, 2+2, 3+1) | 8.33% | 16.67% |
| 5 | 4 (1+4, 2+3, 3+2, 4+1) | 11.11% | 27.78% |
| 6 | 5 (1+5, 2+4, 3+3, 4+2, 5+1) | 13.89% | 41.67% |
| 7 | 6 (1+6, 2+5, 3+4, 4+3, 5+2, 6+1) | 16.67% | 58.33% |
| 8 | 5 (2+6, 3+5, 4+4, 5+3, 6+2) | 13.89% | 72.22% |
| 9 | 4 (3+6, 4+5, 5+4, 6+3) | 11.11% | 83.33% |
| 10 | 3 (4+6, 5+5, 6+4) | 8.33% | 91.67% |
| 11 | 2 (5+6, 6+5) | 5.56% | 97.22% |
| 12 | 1 (6+6) | 2.78% | 100.00% |

**Probability of rolling doubles**: 6/36 = 16.67%
**Probability of rolling 3 doubles in a row**: (1/6)^3 = 0.46%

---

## Appendix B: Property Position Index

Quick lookup from property name to board position:

| Property | Position | Type |
|----------|----------|------|
| Atlantic Avenue | 26 | Yellow |
| B&O Railroad | 25 | Railroad |
| Baltic Avenue | 3 | Brown |
| Boardwalk | 39 | Dark Blue |
| Connecticut Avenue | 9 | Light Blue |
| Electric Company | 12 | Utility |
| Illinois Avenue | 24 | Red |
| Indiana Avenue | 23 | Red |
| Kentucky Avenue | 21 | Red |
| Marvin Gardens | 29 | Yellow |
| Mediterranean Avenue | 1 | Brown |
| New York Avenue | 19 | Orange |
| North Carolina Avenue | 32 | Green |
| Oriental Avenue | 6 | Light Blue |
| Pacific Avenue | 31 | Green |
| Park Place | 37 | Dark Blue |
| Pennsylvania Avenue | 34 | Green |
| Pennsylvania Railroad | 15 | Railroad |
| Reading Railroad | 5 | Railroad |
| Short Line Railroad | 35 | Railroad |
| St. Charles Place | 11 | Pink |
| St. James Place | 16 | Orange |
| States Avenue | 13 | Pink |
| Tennessee Avenue | 18 | Orange |
| Ventnor Avenue | 27 | Yellow |
| Vermont Avenue | 8 | Light Blue |
| Virginia Avenue | 14 | Pink |
| Water Works | 28 | Utility |

---

## Appendix C: Implementation Constants

Key constants for the game engine:

```
BOARD_SIZE = 40
GO_POSITION = 0
JAIL_POSITION = 10
FREE_PARKING_POSITION = 20
GO_TO_JAIL_POSITION = 30

GO_SALARY = 200
INCOME_TAX_AMOUNT = 200
LUXURY_TAX_AMOUNT = 100
JAIL_FINE = 50

MAX_HOUSES = 32
MAX_HOTELS = 12
MAX_PLAYERS = 8
MIN_PLAYERS = 2

STARTING_MONEY = 1500
MAX_JAIL_TURNS = 3
MAX_DOUBLES_BEFORE_JAIL = 3

MORTGAGE_INTEREST_RATE = 0.10  # 10%
BUILDING_SELL_RATIO = 0.50     # 50% of purchase price

CHANCE_POSITIONS = [7, 22, 36]
COMMUNITY_CHEST_POSITIONS = [2, 17, 33]
RAILROAD_POSITIONS = [5, 15, 25, 35]
UTILITY_POSITIONS = [12, 28]

COLOR_GROUPS = {
    "Brown": [1, 3],
    "Light Blue": [6, 8, 9],
    "Pink": [11, 13, 14],
    "Orange": [16, 18, 19],
    "Red": [21, 23, 24],
    "Yellow": [26, 27, 29],
    "Green": [31, 32, 34],
    "Dark Blue": [37, 39]
}

HOUSE_COSTS = {
    "Brown": 50,
    "Light Blue": 50,
    "Pink": 100,
    "Orange": 100,
    "Red": 150,
    "Yellow": 150,
    "Green": 200,
    "Dark Blue": 200
}

RAILROAD_RENT = {1: 25, 2: 50, 3: 100, 4: 200}
UTILITY_MULTIPLIER = {1: 4, 2: 10}
```

---

*Document Version: 1.0*
*Last Updated: 2026-02-11*
*Based on: Official Hasbro Monopoly Rules (standard US edition)*
