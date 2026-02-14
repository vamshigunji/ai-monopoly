# Data Model Reference -- Monopoly AI Agents

Complete reference of all data types, enumerations, dataclasses, mutable state classes, and their relationships in the Monopoly game engine.

**Source package:** `monopoly.engine`

**Modules covered:**

| Module | File | Purpose |
|--------|------|---------|
| `types` | `engine/types.py` | All enums, frozen dataclasses, and event types |
| `board` | `engine/board.py` | Board layout, 40 spaces, static property data, constants |
| `player` | `engine/player.py` | Mutable player state and operations |
| `bank` | `engine/bank.py` | House/hotel inventory management |
| `cards` | `engine/cards.py` | Chance and Community Chest decks |
| `dice` | `engine/dice.py` | Deterministic dice with injectable RNG |
| `rules` | `engine/rules.py` | Stateless rule enforcement (rent, building, mortgage, trade) |
| `trade` | `engine/trade.py` | Trade execution logic |
| `game` | `engine/game.py` | Core game state machine and event bus |

---

## 1. Overview

The engine follows a strict separation of concerns:

- **Immutable data** (`@dataclass(frozen=True)`) represents static game definitions: board spaces, property stats, card effects, dice rolls. These never change after creation.
- **Mutable state** (`@dataclass` or plain classes) represents runtime game objects: players, the bank, decks, and the game itself.
- **Stateless rules** (the `Rules` class) encapsulates all Monopoly rule logic, taking state as input and returning decisions. It never mutates state directly.
- **Events** (`GameEvent`) are emitted by the `Game` class as an append-only log, enabling WebSocket broadcast to connected clients.

All positions on the board are integers in the range `0..39`, used as the primary key for property ownership, building counts, and mortgage status.

---

## 2. Enumerations

All enumerations are defined in `engine/types.py` using Python's `enum.Enum` with `auto()` values.

### 2.1 SpaceType

Classifies each of the 40 board spaces.

| Value | Description |
|-------|-------------|
| `PROPERTY` | A colored property that can be purchased, improved with houses/hotels, and charges rent. 22 spaces total. |
| `RAILROAD` | One of the four railroads. Rent scales with the number of railroads the owner holds. Positions: 5, 15, 25, 35. |
| `UTILITY` | Electric Company (12) or Water Works (28). Rent is a multiplier of the dice roll. |
| `TAX` | Income Tax (position 4, $200) or Luxury Tax (position 38, $100). Payment is mandatory. |
| `CHANCE` | Draw a card from the Chance deck. Positions: 7, 22, 36. |
| `COMMUNITY_CHEST` | Draw a card from the Community Chest deck. Positions: 2, 17, 33. |
| `GO` | Position 0. Players collect $200 salary when passing or landing here. |
| `JAIL` | Position 10. Serves dual purpose: "Just Visiting" when passing through, or held in jail. |
| `FREE_PARKING` | Position 20. No game effect (standard rules). |
| `GO_TO_JAIL` | Position 30. Player is immediately sent to jail (position 10) without collecting GO salary. |

### 2.2 ColorGroup

Identifies the eight property color groups. The `value` is a lowercase string identifier.

| Value | String | Properties | Positions | House Cost |
|-------|--------|------------|-----------|------------|
| `BROWN` | `"brown"` | 2 | 1, 3 | $50 |
| `LIGHT_BLUE` | `"light_blue"` | 3 | 6, 8, 9 | $50 |
| `PINK` | `"pink"` | 3 | 11, 13, 14 | $100 |
| `ORANGE` | `"orange"` | 3 | 16, 18, 19 | $100 |
| `RED` | `"red"` | 3 | 21, 23, 24 | $150 |
| `YELLOW` | `"yellow"` | 3 | 26, 27, 29 | $150 |
| `GREEN` | `"green"` | 3 | 31, 32, 34 | $200 |
| `DARK_BLUE` | `"dark_blue"` | 2 | 37, 39 | $200 |

### 2.3 CardType

Identifies which deck a card belongs to.

| Value | Description |
|-------|-------------|
| `CHANCE` | Chance card deck (16 cards). Drawn at positions 7, 22, 36. |
| `COMMUNITY_CHEST` | Community Chest card deck (16 cards). Drawn at positions 2, 17, 33. |

### 2.4 CardEffectType

Describes the mechanical effect of a drawn card. Different fields on `CardEffect` are relevant depending on the effect type.

| Value | Description | Relevant Fields |
|-------|-------------|-----------------|
| `ADVANCE_TO` | Move to a specific board position. Collect $200 if passing GO (unless destination is jail). | `destination` |
| `ADVANCE_TO_NEAREST` | Move forward to the nearest railroad or utility. Special rent rules apply. | `target_type` (`"railroad"` or `"utility"`) |
| `GO_BACK` | Move backwards N spaces from current position. Process landing at new space. | `value` (number of spaces) |
| `COLLECT` | Collect money from the bank. | `value` (dollar amount) |
| `PAY` | Pay money to the bank. | `value` (dollar amount) |
| `PAY_EACH_PLAYER` | Pay every other active (non-bankrupt) player N dollars. | `value` (per-player amount) |
| `COLLECT_FROM_EACH` | Collect N dollars from every other active player. | `value` (per-player amount) |
| `REPAIRS` | Pay a repair cost based on the number of houses and hotels the player owns. | `per_house`, `per_hotel` |
| `GO_TO_JAIL` | Go directly to jail. Do not pass GO, do not collect $200. | _(none)_ |
| `GET_OUT_OF_JAIL` | Receive a "Get Out of Jail Free" card. Kept until used, then returned to the deck. | _(none)_ |

### 2.5 JailAction

Actions available to a player who is currently in jail.

| Value | Description | Cost / Condition |
|-------|-------------|------------------|
| `PAY_FINE` | Pay the $50 jail fine to be released immediately. | Requires `cash >= 50` |
| `USE_CARD` | Use a "Get Out of Jail Free" card. Card is returned to its deck. | Requires `get_out_of_jail_cards > 0` |
| `ROLL_DOUBLES` | Attempt to roll doubles. If successful, player is freed and moves. After 3 failed attempts, the $50 fine is automatically paid. | No cost unless forced after 3 turns |

### 2.6 TurnPhase

Tracks the phase within a single player's turn.

| Value | Description |
|-------|-------------|
| `PRE_ROLL` | Before the dice are rolled. Player may take pre-roll actions (e.g., trade, build, mortgage). |
| `ROLL` | Dice have been rolled; movement is pending. |
| `LANDED` | Player has landed on a space; landing effects are being processed. |
| `POST_ROLL` | Landing resolution complete. Player may take post-roll actions (build, mortgage, trade). |
| `END_TURN` | Turn is complete. Ready to advance to the next player. |

### 2.7 GamePhase

High-level game lifecycle phases.

| Value | Description |
|-------|-------------|
| `SETUP` | Game is being initialized (players joining, configuration). |
| `IN_PROGRESS` | Game is actively being played. |
| `FINISHED` | Game is over. A winner has been determined (or all players bankrupt). |

### 2.8 EventType

Events emitted by the `Game` class onto the event bus. Each event is wrapped in a `GameEvent` dataclass.

| Value | Description | Typical `data` Payload |
|-------|-------------|------------------------|
| `GAME_STARTED` | Game has been initialized and is beginning. | `{}` |
| `TURN_STARTED` | A new turn has begun for a player. | `{"turn_number": int}` |
| `DICE_ROLLED` | Dice have been rolled. | `{"die1": int, "die2": int, "total": int, "doubles": bool}` |
| `PLAYER_MOVED` | A player moved to a new position. | `{"new_position": int, "spaces_moved": int}` or `{"new_position": int, "direct_move": true}` or `{"new_position": int, "went_back": int}` |
| `PASSED_GO` | A player passed or landed on GO. | `{"salary": 200}` |
| `PROPERTY_PURCHASED` | A player bought a property at list price. | `{"position": int, "price": int, "name": str}` |
| `AUCTION_STARTED` | An auction has been initiated for an unowned property. | _(context-dependent)_ |
| `AUCTION_BID` | A player placed a bid in an auction. | _(context-dependent)_ |
| `AUCTION_WON` | A player won an auction. | `{"position": int, "bid": int, "name": str}` |
| `RENT_PAID` | A player paid rent to another player. | `{"amount": int, "to_player": int}` |
| `CARD_DRAWN` | A Chance or Community Chest card was drawn. | `{"description": str, "deck": str}` |
| `CARD_EFFECT` | A card effect was applied. | _(context-dependent)_ |
| `TAX_PAID` | A player paid a tax. | `{"amount": int, "space": str}` |
| `HOUSE_BUILT` | A house was built on a property. | `{"position": int, "houses": int, "name": str}` |
| `HOTEL_BUILT` | A hotel was built (upgrade from 4 houses). | `{"position": int, "name": str}` |
| `BUILDING_SOLD` | A house or hotel was sold back to the bank. | `{"position": int, "refund": int}` |
| `PROPERTY_MORTGAGED` | A property was mortgaged. | `{"position": int, "value": int}` |
| `PROPERTY_UNMORTGAGED` | A property was unmortgaged. | `{"position": int, "cost": int}` |
| `TRADE_PROPOSED` | A trade was proposed between two players. | _(context-dependent)_ |
| `TRADE_ACCEPTED` | A trade was accepted and executed. | `{"proposer_id": int, "receiver_id": int, "offered_properties": list, "requested_properties": list, "offered_cash": int, "requested_cash": int}` |
| `TRADE_REJECTED` | A trade was rejected. | `{"reason": str}` |
| `PLAYER_JAILED` | A player was sent to jail. | `{}` |
| `PLAYER_FREED` | A player was released from jail. | `{"method": str}` where method is `"paid_fine"`, `"used_card"`, `"rolled_doubles"`, or `"forced_payment"`. May include `"roll": int`. |
| `PLAYER_BANKRUPT` | A player went bankrupt and is eliminated. | `{"creditor_id": int or None}` |
| `AGENT_SPOKE` | An AI agent produced a chat message. | _(agent-layer defined)_ |
| `AGENT_THOUGHT` | An AI agent's internal reasoning was logged. | _(agent-layer defined)_ |
| `GAME_OVER` | The game has ended. | _(context-dependent)_ |

---

## 3. Core Data Classes (Immutable)

All classes in this section are decorated with `@dataclass(frozen=True)` and are therefore immutable after construction. They represent static game data and results.

### 3.1 DiceRoll

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

Result of rolling two six-sided dice.

| Field / Property | Type | Description |
|------------------|------|-------------|
| `die1` | `int` | Value of the first die (1--6). |
| `die2` | `int` | Value of the second die (1--6). |
| `total` | `int` (property) | Sum of both dice: `die1 + die2`. Range: 2--12. |
| `is_doubles` | `bool` (property) | `True` if `die1 == die2`. Triggers extra turn or jail on third consecutive doubles. |

### 3.2 PropertyData

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

Static data for a colored property space. There are 22 properties defined in the `PROPERTIES` dict in `engine/board.py`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name (e.g., `"Boardwalk"`). |
| `position` | `int` | Board position (0--39). |
| `color_group` | `ColorGroup` | The color group this property belongs to. |
| `price` | `int` | Purchase price in dollars. |
| `mortgage_value` | `int` | Cash received when mortgaging (always `price // 2`). |
| `rent` | `tuple[int, ...]` | Rent schedule: `(base, 1_house, 2_houses, 3_houses, 4_houses, hotel)`. 6 elements. |
| `house_cost` | `int` | Cost to build one house (or upgrade to hotel). Same for all properties in the color group. |

**Rent schedule example (Boardwalk):**

| Index | Level | Rent |
|-------|-------|------|
| 0 | Base (unimproved) | $50 |
| 1 | 1 house | $200 |
| 2 | 2 houses | $600 |
| 3 | 3 houses | $1,400 |
| 4 | 4 houses | $1,700 |
| 5 | Hotel | $2,000 |

Note: With a monopoly (full color group, no houses), base rent is **doubled** automatically by the Rules engine.

### 3.3 RailroadData

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

Static data for a railroad space. There are exactly 4 railroads.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Display name (e.g., `"Reading Railroad"`). |
| `position` | `int` | -- | Board position. |
| `price` | `int` | `200` | Purchase price. All railroads cost $200. |
| `mortgage_value` | `int` | `100` | Mortgage value. All railroads mortgage for $100. |

**Railroad inventory:**

| Position | Name |
|----------|------|
| 5 | Reading Railroad |
| 15 | Pennsylvania Railroad |
| 25 | B&O Railroad |
| 35 | Short Line Railroad |

### 3.4 UtilityData

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

Static data for a utility space. There are exactly 2 utilities.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Display name. |
| `position` | `int` | -- | Board position. |
| `price` | `int` | `150` | Purchase price. Both utilities cost $150. |
| `mortgage_value` | `int` | `75` | Mortgage value. Both utilities mortgage for $75. |

**Utility inventory:**

| Position | Name |
|----------|------|
| 12 | Electric Company |
| 28 | Water Works |

### 3.5 TaxData

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

Static data for a tax space.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name. |
| `position` | `int` | Board position. |
| `amount` | `int` | Tax amount to pay. |

**Tax spaces:**

| Position | Name | Amount |
|----------|------|--------|
| 4 | Income Tax | $200 |
| 38 | Luxury Tax | $100 |

### 3.6 Space

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

A single space on the 40-space Monopoly board. Acts as a discriminated union over space types using optional typed data fields.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `position` | `int` | -- | Board position (0--39). |
| `name` | `str` | -- | Display name of the space. |
| `space_type` | `SpaceType` | -- | Discriminator for the type of space. |
| `property_data` | `Optional[PropertyData]` | `None` | Present only when `space_type == PROPERTY`. |
| `railroad_data` | `Optional[RailroadData]` | `None` | Present only when `space_type == RAILROAD`. |
| `utility_data` | `Optional[UtilityData]` | `None` | Present only when `space_type == UTILITY`. |
| `tax_data` | `Optional[TaxData]` | `None` | Present only when `space_type == TAX`. |

**Usage pattern:**
```python
space = board.get_space(39)
if space.space_type == SpaceType.PROPERTY:
    rent = space.property_data.rent[0]  # base rent
```

### 3.7 CardEffect

**Module:** `engine/types.py`
**Decorator:** `@dataclass(frozen=True)`

Describes the mechanical effect of a Chance or Community Chest card. Which fields are relevant depends on the `effect_type`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | `str` | -- | Human-readable card text (e.g., `"Advance to Boardwalk"`). |
| `effect_type` | `CardEffectType` | -- | The type of effect. Determines which other fields are used. |
| `value` | `int` | `0` | Dollar amount (for `COLLECT`, `PAY`, `PAY_EACH_PLAYER`, `COLLECT_FROM_EACH`) or number of spaces (for `GO_BACK`). |
| `destination` | `int` | `-1` | Target board position for `ADVANCE_TO`. `-1` means unused. |
| `target_type` | `str` | `""` | `"railroad"` or `"utility"` for `ADVANCE_TO_NEAREST`. Empty means unused. |
| `per_house` | `int` | `0` | Per-house cost for `REPAIRS`. |
| `per_hotel` | `int` | `0` | Per-hotel cost for `REPAIRS`. |

**Field usage by effect type:**

| Effect Type | `value` | `destination` | `target_type` | `per_house` | `per_hotel` |
|-------------|---------|---------------|---------------|-------------|-------------|
| `ADVANCE_TO` | -- | position | -- | -- | -- |
| `ADVANCE_TO_NEAREST` | -- | -- | `"railroad"` / `"utility"` | -- | -- |
| `GO_BACK` | spaces | -- | -- | -- | -- |
| `COLLECT` | dollars | -- | -- | -- | -- |
| `PAY` | dollars | -- | -- | -- | -- |
| `PAY_EACH_PLAYER` | dollars | -- | -- | -- | -- |
| `COLLECT_FROM_EACH` | dollars | -- | -- | -- | -- |
| `REPAIRS` | -- | -- | -- | dollars | dollars |
| `GO_TO_JAIL` | -- | -- | -- | -- | -- |
| `GET_OUT_OF_JAIL` | -- | -- | -- | -- | -- |

### 3.8 Card

**Module:** `engine/types.py`
**Decorator:** `@dataclass` (mutable, but only for deck management)

A Chance or Community Chest card. The `Card` itself is a thin wrapper pairing a deck type with an effect.

| Field | Type | Description |
|-------|------|-------------|
| `deck` | `CardType` | Which deck this card belongs to (`CHANCE` or `COMMUNITY_CHEST`). |
| `effect` | `CardEffect` | The frozen effect data describing what this card does. |

### 3.9 TradeProposal

**Module:** `engine/types.py`
**Decorator:** `@dataclass`

A trade proposal between two players. Validated by `Rules.validate_trade()` before execution.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `proposer_id` | `int` | -- | Player ID of the player proposing the trade. |
| `receiver_id` | `int` | -- | Player ID of the player receiving the offer. |
| `offered_properties` | `list[int]` | `[]` | Board positions of properties the proposer is offering. |
| `requested_properties` | `list[int]` | `[]` | Board positions of properties the proposer wants from the receiver. |
| `offered_cash` | `int` | `0` | Cash the proposer is offering. |
| `requested_cash` | `int` | `0` | Cash the proposer is requesting from the receiver. |
| `offered_jail_cards` | `int` | `0` | Number of "Get Out of Jail Free" cards the proposer is offering. |
| `requested_jail_cards` | `int` | `0` | Number of "Get Out of Jail Free" cards the proposer is requesting. |

**Trade validation rules** (enforced by `Rules.validate_trade()`):
- Proposer must own all offered properties.
- Receiver must own all requested properties.
- No buildings may exist on any traded property (must sell buildings first).
- Both parties must have sufficient cash.
- Both parties must have sufficient jail cards.
- At least one item must be exchanged.
- Mortgaged properties can be traded; the receiver pays a 10% transfer fee immediately.

### 3.10 GameEvent

**Module:** `engine/types.py`
**Decorator:** `@dataclass`

An event emitted during gameplay. Events form an append-only log used for WebSocket broadcast and game history replay.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `event_type` | `EventType` | -- | The type of event (see Section 2.8). |
| `player_id` | `int` | `-1` | The player this event relates to. `-1` for global events. |
| `data` | `dict` | `{}` | Arbitrary payload specific to the event type. |
| `turn_number` | `int` | `0` | The turn number when this event occurred. |

### 3.11 LandingResult

**Module:** `engine/game.py`
**Decorator:** `@dataclass`

Result of landing on a space. Returned by `Game.process_landing()` to inform the caller what action is needed.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `space_type` | `SpaceType` | -- | The type of space landed on. |
| `position` | `int` | -- | The board position landed on. |
| `requires_buy_decision` | `bool` | `False` | `True` if the space is unowned and purchasable. Player must buy or trigger auction. |
| `rent_owed` | `int` | `0` | Amount of rent owed to another player. `0` if no rent due. |
| `rent_to_player` | `int` | `-1` | Player ID of the rent recipient. `-1` if no rent due. |
| `card_drawn` | `Optional[str]` | `None` | Description text of a drawn card, or `None` if no card was drawn. |
| `tax_amount` | `int` | `0` | Tax amount paid, or `0` if not a tax space. |
| `sent_to_jail` | `bool` | `False` | `True` if the player was sent to jail. |

---

## 4. Mutable State Classes

### 4.1 Player

**Module:** `engine/player.py`
**Decorator:** `@dataclass`

A Monopoly player's complete mutable state. Tracks position, finances, property portfolio, buildings, mortgage status, jail status, and bankruptcy.

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `player_id` | `int` | -- | Unique player identifier (0-indexed). |
| `name` | `str` | -- | Display name (default: `"Player{id+1}"`). |
| `position` | `int` | `0` | Current board position (0--39). Starts at GO. |
| `cash` | `int` | `1500` | Current cash balance in dollars. |
| `properties` | `list[int]` | `[]` | Board positions of all owned properties (properties, railroads, utilities). |
| `houses` | `dict[int, int]` | `{}` | Map of `position -> house_count`. Values 1--4 represent houses; `5` represents a hotel. Absent keys mean 0 houses. |
| `mortgaged` | `set[int]` | `set()` | Set of board positions of mortgaged properties. |
| `in_jail` | `bool` | `False` | `True` if the player is currently in jail. |
| `jail_turns` | `int` | `0` | Number of turns spent in jail trying to roll doubles. Max 3. |
| `get_out_of_jail_cards` | `int` | `0` | Number of "Get Out of Jail Free" cards held. |
| `is_bankrupt` | `bool` | `False` | `True` if the player has been eliminated. |
| `consecutive_doubles` | `int` | `0` | Number of consecutive doubles rolled this turn. 3 consecutive doubles sends the player to jail. |

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `add_cash` | `(amount: int) -> None` | -- | Add cash to the player's balance. |
| `remove_cash` | `(amount: int) -> bool` | `bool` | Subtract cash. Returns `False` if insufficient funds (cash is still deducted if `True`). |
| `add_property` | `(position: int) -> None` | -- | Add a property position to the portfolio. No-op if already owned. |
| `remove_property` | `(position: int) -> None` | -- | Remove a property. Also clears its mortgage status and house count. |
| `owns_property` | `(position: int) -> bool` | `bool` | Check if this player owns the property at the given position. |
| `mortgage_property` | `(position: int) -> None` | -- | Mark a property as mortgaged. |
| `unmortgage_property` | `(position: int) -> None` | -- | Mark a property as unmortgaged. |
| `is_mortgaged` | `(position: int) -> bool` | `bool` | Check if a specific property is mortgaged. |
| `get_house_count` | `(position: int) -> int` | `int` | Get house count for a position. Returns `0` if no houses. `5` means hotel. |
| `set_houses` | `(position: int, count: int) -> None` | -- | Set the house count. `0` removes the key from the dict. |
| `send_to_jail` | `() -> None` | -- | Move player to position 10, set `in_jail = True`, reset `jail_turns` and `consecutive_doubles`. |
| `release_from_jail` | `() -> None` | -- | Set `in_jail = False`, reset `jail_turns` to 0. |
| `move_to` | `(position: int) -> bool` | `bool` | Move to an absolute position (mod 40). Returns `True` if the player passed GO. |
| `move_forward` | `(spaces: int) -> bool` | `bool` | Move forward by N spaces (mod 40). Returns `True` if passed GO. |
| `net_worth` | `(board) -> int` | `int` | Calculate total net worth: cash + property values (face value if unmortgaged, mortgage value if mortgaged) + building values (house_cost * count). |

### 4.2 Bank

**Module:** `engine/bank.py`
**Decorator:** `@dataclass`

Manages the finite supply of houses and hotels according to official Monopoly rules. The bank has unlimited cash (not tracked).

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `houses_available` | `int` | `32` | Number of houses remaining in the bank's inventory. |
| `hotels_available` | `int` | `12` | Number of hotels remaining in the bank's inventory. |

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `buy_house` | `() -> bool` | `bool` | Remove one house from inventory. Returns `False` if none available. |
| `return_house` | `() -> None` | -- | Return one house to inventory. Capped at `MAX_HOUSES` (32). |
| `buy_hotel` | `() -> bool` | `bool` | Remove one hotel from inventory. Returns `False` if none available. |
| `return_hotel` | `() -> None` | -- | Return one hotel to inventory. Capped at `MAX_HOTELS` (12). |
| `upgrade_to_hotel` | `() -> bool` | `bool` | Upgrade 4 houses to 1 hotel: removes 1 hotel from inventory, returns 4 houses. Returns `False` if no hotels available. |
| `downgrade_from_hotel` | `() -> bool` | `bool` | Downgrade 1 hotel to 4 houses: returns 1 hotel, removes 4 houses. Returns `False` if fewer than 4 houses available. |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `has_housing_shortage` | `bool` | `True` when `houses_available == 0`. |
| `has_hotel_shortage` | `bool` | `True` when `hotels_available == 0`. |

### 4.3 Board

**Module:** `engine/board.py`
**Class:** Plain class (not a dataclass)

The Monopoly game board containing all 40 spaces. Constructed once at game start via `_build_spaces()`. Provides lookup methods for spaces and property data.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `spaces` | `list[Space]` | All 40 `Space` objects, indexed by position (0--39). |
| `size` | `int` | Always `40` (`BOARD_SIZE`). |

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_space` | `(position: int) -> Space` | `Space` | Get the space at a position. Position is taken mod 40. |
| `get_color_group` | `(color: ColorGroup) -> list[int]` | `list[int]` | Get all property positions in a color group. |
| `get_property_data` | `(position: int) -> PropertyData or None` | `PropertyData or None` | Get property data for a position, or `None` if not a colored property. |
| `get_railroad_data` | `(position: int) -> RailroadData or None` | `RailroadData or None` | Get railroad data for a position, or `None` if not a railroad. |
| `get_utility_data` | `(position: int) -> UtilityData or None` | `UtilityData or None` | Get utility data for a position, or `None` if not a utility. |
| `distance_to` | `(from_pos: int, to_pos: int) -> int` | `int` | Calculate clockwise distance between two positions (mod 40). |
| `get_nearest_railroad` | `(position: int) -> int` | `int` | Get the position of the next railroad ahead (clockwise). Wraps around. |
| `get_nearest_utility` | `(position: int) -> int` | `int` | Get the position of the next utility ahead (clockwise). Wraps around. |
| `is_purchasable` | `(position: int) -> bool` | `bool` | `True` if the space is a `PROPERTY`, `RAILROAD`, or `UTILITY`. |
| `get_purchase_price` | `(position: int) -> int` | `int` | Get the listed purchase price. Returns `0` for non-purchasable spaces. |

### 4.4 Deck

**Module:** `engine/cards.py`
**Class:** Plain class

A shuffleable card deck with support for "Get Out of Jail Free" card removal and return.

#### Constructor

```python
Deck(cards: list[Card], seed: int | None = None)
```

The deck is automatically shuffled upon construction.

#### Internal Fields

| Field | Type | Description |
|-------|------|-------------|
| `_cards` | `list[Card]` | Master list of all cards in this deck (never modified). |
| `_draw_pile` | `list[Card]` | Current draw pile. Cards are popped from the front (index 0). |
| `_rng` | `random.Random` | Seeded random number generator for deterministic shuffling. |
| `_jail_card_held` | `bool` | `True` if a "Get Out of Jail Free" card from this deck is currently held by a player. |

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `shuffle` | `() -> None` | -- | Shuffle all master cards back into the draw pile. |
| `draw` | `() -> Card` | `Card` | Draw the top card. If the pile is empty, reshuffle (excluding held jail cards). |
| `return_jail_card` | `() -> None` | -- | Mark that the held jail card has been returned to the deck. |
| `remove_jail_card` | `() -> None` | -- | Mark that a jail card is being held by a player (excluded from reshuffles). |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `cards_remaining` | `int` | Number of cards left in the draw pile. |

**Factory functions:**

| Function | Returns | Description |
|----------|---------|-------------|
| `create_chance_deck(seed=None)` | `Deck` | Creates a shuffled 16-card Chance deck. |
| `create_community_chest_deck(seed=None)` | `Deck` | Creates a shuffled 16-card Community Chest deck. |

### 4.5 Dice

**Module:** `engine/dice.py`
**Class:** Plain class

Two six-sided dice with an injectable random number generator for deterministic testing.

#### Constructor

```python
Dice(seed: int | None = None)
```

#### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `roll` | `() -> DiceRoll` | `DiceRoll` | Roll both dice. Returns a frozen `DiceRoll` with `die1` and `die2` each in range 1--6. |

### 4.6 Rules

**Module:** `engine/rules.py`
**Class:** Plain class

Stateless rule enforcement. Receives game state as input parameters and returns decisions. Never mutates state directly.

#### Constructor

```python
Rules(board: Board)
```

#### Rent Calculation

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `calculate_rent` | `(position, owner, dice_roll=None) -> int` | `int` | Master rent calculator. Dispatches to property/railroad/utility rent. Returns `0` if mortgaged. |

**Rent logic by space type:**

- **Property:** Uses `PropertyData.rent[house_count]`. If unimproved and the owner has a monopoly, base rent is doubled.
- **Railroad:** Looks up `RAILROAD_RENTS[count]` where `count` is the number of unmortgaged railroads owned.
- **Utility:** `dice_roll.total * UTILITY_MULTIPLIERS[count]` where `count` is the number of unmortgaged utilities owned. Raises `ValueError` if `dice_roll` is `None`.

#### Monopoly Check

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `has_monopoly` | `(player, color_group) -> bool` | `bool` | `True` if the player owns every property in the color group. |

#### Building Rules

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `can_build_house` | `(player, position, bank) -> bool` | `bool` | Checks: is a property, has monopoly, no mortgaged properties in group, house count < 4, even-build rule satisfied, sufficient cash, bank has houses. |
| `can_build_hotel` | `(player, position, bank) -> bool` | `bool` | Checks: is a property, has monopoly, no mortgaged in group, exactly 4 houses, even-build rule, sufficient cash, bank has hotels. |
| `can_sell_house` | `(player, position) -> bool` | `bool` | Checks: has 1--4 houses (not 0 or hotel), even sell-back rule (no property in group has more houses). |
| `can_sell_hotel` | `(player, position, bank) -> bool` | `bool` | Checks: has a hotel (house count == 5). Always returns `True` (can sell down to 0 if no houses available in bank). |

#### Mortgage Rules

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `can_mortgage` | `(player, position) -> bool` | `bool` | Checks: player owns it, not already mortgaged, no buildings on any property in the same color group. |
| `can_unmortgage` | `(player, position) -> bool` | `bool` | Checks: player owns it, is currently mortgaged, player has enough cash for unmortgage cost. |
| `unmortgage_cost` | `(position) -> int` | `int` | `int(mortgage_value * 1.1)` -- mortgage value plus 10% interest, truncated. |
| `get_mortgage_value` | `(position) -> int` | `int` | Returns the mortgage value for any purchasable space. |
| `mortgage_transfer_fee` | `(position) -> int` | `int` | `int(mortgage_value * 0.1)` -- 10% fee paid when receiving a mortgaged property in a trade. |

#### Buying Rules

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `can_buy_property` | `(player, position) -> bool` | `bool` | Space is purchasable and player has enough cash. |

#### Trade Validation

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `validate_trade` | `(proposal, proposer, receiver) -> tuple[bool, str]` | `(bool, str)` | Returns `(True, "")` if valid, or `(False, reason_string)` if invalid. |

### 4.7 Game

**Module:** `engine/game.py`
**Class:** Plain class

The core game state machine. Owns all game objects, manages turns, emits events, and delegates rule checks to the `Rules` class.

#### Constructor

```python
Game(num_players: int = 4, seed: int | None = None)
```

Creates the board, dice, bank, rules, both card decks, and `num_players` Player objects. The Community Chest deck uses `seed + 1` for independent shuffling.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `board` | `Board` | The 40-space game board. |
| `dice` | `Dice` | The dice roller (seeded RNG). |
| `bank` | `Bank` | House/hotel inventory manager. |
| `rules` | `Rules` | Stateless rule enforcement. |
| `chance_deck` | `Deck` | The Chance card deck (16 cards). |
| `community_chest_deck` | `Deck` | The Community Chest card deck (16 cards). |
| `players` | `list[Player]` | All players (including bankrupt ones). |
| `current_player_index` | `int` | Index into `players` of the current player. |
| `turn_number` | `int` | Current turn number (incremented on `advance_turn()`). |
| `phase` | `GamePhase` | High-level game phase (`SETUP`, `IN_PROGRESS`, `FINISHED`). |
| `turn_phase` | `TurnPhase` | Current phase within the active turn. |
| `last_roll` | `DiceRoll or None` | The most recent dice roll. Used for utility rent calculation. |
| `events` | `list[GameEvent]` | Append-only event log. |
| `_property_owners` | `dict[int, int]` | Internal mapping of `position -> player_id`. Private; use accessor methods. |

#### Property Ownership Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `current_player` | _(property)_ | `Player` | The player whose turn it is. |
| `get_property_owner` | `(position) -> Player or None` | `Player or None` | Get the owning player, or `None` if unowned. |
| `is_property_owned` | `(position) -> bool` | `bool` | Check if a position is owned. |
| `assign_property` | `(player, position)` | -- | Assign ownership to a player. |
| `transfer_property` | `(from_player, to_player, position)` | -- | Transfer ownership between players. |
| `unown_property` | `(position)` | -- | Remove ownership (e.g., bankruptcy to bank). |

#### Dice and Movement

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `roll_dice` | `() -> DiceRoll` | `DiceRoll` | Roll the dice. Stores result in `last_roll`. Emits `DICE_ROLLED`. |
| `move_player` | `(player, spaces) -> bool` | `bool` | Move forward by N spaces. Emits `PLAYER_MOVED`. Awards GO salary if passed GO. |
| `move_player_to` | `(player, position, collect_go=True) -> bool` | `bool` | Move to an absolute position. Optionally collects GO salary. |

#### Landing and Space Processing

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `process_landing` | `(player) -> LandingResult` | `LandingResult` | Process landing on the player's current space. Handles property, railroad, utility, tax, card, and go-to-jail spaces. |

#### Property Transactions

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `buy_property` | `(player, position) -> bool` | `bool` | Buy at list price. Emits `PROPERTY_PURCHASED`. |
| `auction_property` | `(position, bids) -> int or None` | `int or None` | Auction to highest valid bidder. Emits `AUCTION_WON`. |
| `pay_rent` | `(payer, owner_id, amount)` | -- | Transfer rent from payer to owner. Emits `RENT_PAID`. |

#### Building

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `build_house` | `(player, position) -> bool` | `bool` | Build a house if rules permit. Emits `HOUSE_BUILT`. |
| `build_hotel` | `(player, position) -> bool` | `bool` | Build a hotel (upgrade from 4 houses). Emits `HOTEL_BUILT`. |
| `sell_house` | `(player, position) -> bool` | `bool` | Sell a house at half price. Emits `BUILDING_SOLD`. |
| `sell_hotel` | `(player, position) -> bool` | `bool` | Sell/downgrade a hotel. Downgrades to 4 houses if available, otherwise sells entirely. Emits `BUILDING_SOLD`. |

#### Mortgage

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `mortgage_property` | `(player, position) -> bool` | `bool` | Mortgage a property. Emits `PROPERTY_MORTGAGED`. |
| `unmortgage_property` | `(player, position) -> bool` | `bool` | Unmortgage (pay mortgage + 10%). Emits `PROPERTY_UNMORTGAGED`. |

#### Jail

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `handle_jail_turn` | `(player, action) -> DiceRoll or None` | `DiceRoll or None` | Handle a jailed player's action. Returns the dice roll if `ROLL_DOUBLES` was chosen (and player is freed). |

#### Trading

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `execute_trade` | `(proposal) -> tuple[bool, str]` | `(bool, str)` | Validate and execute a trade. Updates `_property_owners`. Returns `(success, reason)`. |

#### Bankruptcy

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `declare_bankruptcy` | `(player, creditor_id=None)` | -- | Eliminate a player. If `creditor_id` is provided, all assets transfer to creditor. Otherwise, buildings return to bank and properties become unowned. |

#### Turn Management

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `advance_turn` | `()` | -- | Advance to the next non-bankrupt player. Increments `turn_number`. Emits `TURN_STARTED`. |
| `is_over` | `() -> bool` | `bool` | `True` if one or fewer active players remain. |
| `get_winner` | `() -> Player or None` | `Player or None` | Returns the sole surviving player, or `None` if game is not over. |
| `get_active_players` | `() -> list[Player]` | `list[Player]` | All non-bankrupt players. |

#### Event System

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_events_since` | `(index) -> list[GameEvent]` | `list[GameEvent]` | Get all events emitted after the given index. Used for incremental WebSocket updates. |

---

## 5. Entity Relationship Diagram

```
+-----------------------------------------------------------+
|                          Game                              |
|-----------------------------------------------------------|
| board: Board                                              |
| dice: Dice                                                |
| bank: Bank                                                |
| rules: Rules                                              |
| chance_deck: Deck                                         |
| community_chest_deck: Deck                                |
| players: list[Player]                                     |
| events: list[GameEvent]                                   |
| _property_owners: dict[int, int]                          |
| phase: GamePhase                                          |
| turn_phase: TurnPhase                                     |
| last_roll: DiceRoll?                                      |
+----------------------------+------------------------------+
             |               |               |
             |               |               |
    +--------v---+   +-------v------+   +----v----------+
    |   Board    |   |    Bank      |   |   Player      |
    |------------|   |--------------|   |---------------|
    | spaces[40] |   | houses: 32   |   | player_id     |
    | size: 40   |   | hotels: 12   |   | name          |
    +-----+------+   +--------------+   | position      |
          |                             | cash          |
          |  contains 40                | properties[]  |
          |                             | houses{}      |
    +-----v------+                      | mortgaged{}   |
    |   Space    |                      | in_jail       |
    |------------|                      | jail_turns    |
    | position   |                      | jail_cards    |
    | name       |                      | is_bankrupt   |
    | space_type |                      | consec_doubles|
    | prop_data? |                      +---------------+
    | rr_data?   |
    | util_data? |
    | tax_data?  |
    +--+-+-+-+---+
       | | | |
       | | | +---- TaxData (frozen)
       | | +------ UtilityData (frozen)
       | +-------- RailroadData (frozen)
       +---------- PropertyData (frozen)
                        |
                        +-- color_group: ColorGroup
                        +-- rent: tuple[int, ...]


    +----------+        +-----------+        +------------+
    |   Deck   | ------>|   Card    |------->| CardEffect |
    |----------|  has   |-----------|  has   |------------|
    | _cards[] |  many  | deck:     |        | description|
    | _draw[]  |        |  CardType |        | effect_type|
    | _rng     |        +-----------+        | value      |
    | _jail_   |                             | destination|
    |  held    |                             | target_type|
    +----------+                             | per_house  |
                                             | per_hotel  |
                                             +------------+

    +----------+        +--------------+
    |   Dice   |------->|  DiceRoll    |
    |----------|  rolls |  (frozen)    |
    | _rng     |        |--------------|
    +----------+        | die1         |
                        | die2         |
                        | .total       |
                        | .is_doubles  |
                        +--------------+

    +------------------+
    |  TradeProposal   |    validated by     +----------+
    |------------------|-------------------->|  Rules   |
    | proposer_id      |                     |----------|
    | receiver_id      |                     | board    |
    | offered_props[]  |                     +----------+
    | requested_props[]|                         |
    | offered_cash     |    executed by      +---v------+
    | requested_cash   |<-------------------| trade.py |
    | offered_jail     |  execute_trade()   +----------+
    | requested_jail   |
    +------------------+

    +----------------+
    |   GameEvent    |
    |----------------|    appended to
    | event_type     |----------------> Game.events[]
    | player_id      |
    | data: dict     |
    | turn_number    |
    +----------------+
```

### Relationship Summary

| Relationship | Type | Description |
|-------------|------|-------------|
| Game HAS Board | 1:1 | Game owns a single Board instance. |
| Game HAS Bank | 1:1 | Game owns a single Bank instance. |
| Game HAS Dice | 1:1 | Game owns a single Dice instance. |
| Game HAS Rules | 1:1 | Game owns a single Rules instance (Rules references Board). |
| Game HAS Players | 1:N | Game owns 2--8 Player instances. |
| Game HAS Decks | 1:2 | Game owns a Chance deck and a Community Chest deck. |
| Game HAS Events | 1:N | Game maintains an append-only event log. |
| Board HAS Spaces | 1:40 | Board contains exactly 40 Space objects. |
| Space HAS Data | 1:0..1 | Each Space has at most one typed data object (PropertyData, RailroadData, UtilityData, or TaxData). |
| PropertyData REFERENCES ColorGroup | N:1 | Multiple properties share a color group. |
| Deck HAS Cards | 1:16 | Each deck contains exactly 16 cards. |
| Card HAS CardEffect | 1:1 | Each card has exactly one effect. |
| Player OWNS Properties | 1:N | Player's `properties` list holds board positions. Mirrored in `Game._property_owners`. |
| Player HAS Houses | 1:N | Player's `houses` dict maps positions to house counts. |
| TradeProposal REFERENCES Players | N:2 | Each proposal involves exactly two players (proposer and receiver). |

---

## 6. Constants

### Game Constants

Defined across multiple modules.

| Constant | Value | Module | Description |
|----------|-------|--------|-------------|
| `BOARD_SIZE` | `40` | `board.py` | Total number of spaces on the board. |
| `STARTING_CASH` | `1500` | `player.py` | Cash each player starts with. |
| `GO_SALARY` | `200` | `game.py` | Cash collected when passing or landing on GO. |
| `JAIL_FINE` | `50` | `game.py` | Fine to pay to get out of jail. |
| `MAX_JAIL_TURNS` | `3` | `game.py` | Maximum turns a player can attempt to roll doubles in jail before being forced to pay. |
| `MAX_HOUSES` | `32` | `bank.py` | Total house pieces in the game. Enforces housing shortages. |
| `MAX_HOTELS` | `12` | `bank.py` | Total hotel pieces in the game. Enforces hotel shortages. |

### Rent Tables

#### Railroad Rents

Defined in `board.py` as `RAILROAD_RENTS`.

| Railroads Owned | Rent |
|-----------------|------|
| 1 | $25 |
| 2 | $50 |
| 3 | $100 |
| 4 | $200 |

#### Utility Multipliers

Defined in `board.py` as `UTILITY_MULTIPLIERS`. Rent = dice roll total * multiplier.

| Utilities Owned | Multiplier | Example (roll of 8) |
|-----------------|------------|---------------------|
| 1 | 4x | $32 |
| 2 | 10x | $80 |

### Color Group Positions

Defined in `board.py` as `COLOR_GROUP_POSITIONS`.

| Color Group | Positions | Property Count |
|-------------|-----------|----------------|
| `BROWN` | 1, 3 | 2 |
| `LIGHT_BLUE` | 6, 8, 9 | 3 |
| `PINK` | 11, 13, 14 | 3 |
| `ORANGE` | 16, 18, 19 | 3 |
| `RED` | 21, 23, 24 | 3 |
| `YELLOW` | 26, 27, 29 | 3 |
| `GREEN` | 31, 32, 34 | 3 |
| `DARK_BLUE` | 37, 39 | 2 |

### Complete Board Layout

| Pos | Name | Type | Price | Mortgage |
|-----|------|------|-------|----------|
| 0 | GO | GO | -- | -- |
| 1 | Mediterranean Avenue | PROPERTY (Brown) | $60 | $30 |
| 2 | Community Chest | COMMUNITY_CHEST | -- | -- |
| 3 | Baltic Avenue | PROPERTY (Brown) | $60 | $30 |
| 4 | Income Tax | TAX ($200) | -- | -- |
| 5 | Reading Railroad | RAILROAD | $200 | $100 |
| 6 | Oriental Avenue | PROPERTY (Light Blue) | $100 | $50 |
| 7 | Chance | CHANCE | -- | -- |
| 8 | Vermont Avenue | PROPERTY (Light Blue) | $100 | $50 |
| 9 | Connecticut Avenue | PROPERTY (Light Blue) | $120 | $60 |
| 10 | Jail / Just Visiting | JAIL | -- | -- |
| 11 | St. Charles Place | PROPERTY (Pink) | $140 | $70 |
| 12 | Electric Company | UTILITY | $150 | $75 |
| 13 | States Avenue | PROPERTY (Pink) | $140 | $70 |
| 14 | Virginia Avenue | PROPERTY (Pink) | $160 | $80 |
| 15 | Pennsylvania Railroad | RAILROAD | $200 | $100 |
| 16 | St. James Place | PROPERTY (Orange) | $180 | $90 |
| 17 | Community Chest | COMMUNITY_CHEST | -- | -- |
| 18 | Tennessee Avenue | PROPERTY (Orange) | $180 | $90 |
| 19 | New York Avenue | PROPERTY (Orange) | $200 | $100 |
| 20 | Free Parking | FREE_PARKING | -- | -- |
| 21 | Kentucky Avenue | PROPERTY (Red) | $220 | $110 |
| 22 | Chance | CHANCE | -- | -- |
| 23 | Indiana Avenue | PROPERTY (Red) | $220 | $110 |
| 24 | Illinois Avenue | PROPERTY (Red) | $240 | $120 |
| 25 | B&O Railroad | RAILROAD | $200 | $100 |
| 26 | Atlantic Avenue | PROPERTY (Yellow) | $260 | $130 |
| 27 | Ventnor Avenue | PROPERTY (Yellow) | $260 | $130 |
| 28 | Water Works | UTILITY | $150 | $75 |
| 29 | Marvin Gardens | PROPERTY (Yellow) | $280 | $140 |
| 30 | Go To Jail | GO_TO_JAIL | -- | -- |
| 31 | Pacific Avenue | PROPERTY (Green) | $300 | $150 |
| 32 | North Carolina Avenue | PROPERTY (Green) | $300 | $150 |
| 33 | Community Chest | COMMUNITY_CHEST | -- | -- |
| 34 | Pennsylvania Avenue | PROPERTY (Green) | $320 | $160 |
| 35 | Short Line Railroad | RAILROAD | $200 | $100 |
| 36 | Chance | CHANCE | -- | -- |
| 37 | Park Place | PROPERTY (Dark Blue) | $350 | $175 |
| 38 | Luxury Tax | TAX ($100) | -- | -- |
| 39 | Boardwalk | PROPERTY (Dark Blue) | $400 | $200 |

### Complete Rent Table for All Properties

| Pos | Name | Color | Base | 1H | 2H | 3H | 4H | Hotel | House Cost |
|-----|------|-------|------|-----|-----|-----|-----|-------|------------|
| 1 | Mediterranean Ave | Brown | $2 | $10 | $30 | $90 | $160 | $250 | $50 |
| 3 | Baltic Ave | Brown | $4 | $20 | $60 | $180 | $320 | $450 | $50 |
| 6 | Oriental Ave | Light Blue | $6 | $30 | $90 | $270 | $400 | $550 | $50 |
| 8 | Vermont Ave | Light Blue | $6 | $30 | $90 | $270 | $400 | $550 | $50 |
| 9 | Connecticut Ave | Light Blue | $8 | $40 | $100 | $300 | $450 | $600 | $50 |
| 11 | St. Charles Place | Pink | $10 | $50 | $150 | $450 | $625 | $750 | $100 |
| 13 | States Ave | Pink | $10 | $50 | $150 | $450 | $625 | $750 | $100 |
| 14 | Virginia Ave | Pink | $12 | $60 | $180 | $500 | $700 | $900 | $100 |
| 16 | St. James Place | Orange | $14 | $70 | $200 | $550 | $750 | $950 | $100 |
| 18 | Tennessee Ave | Orange | $14 | $70 | $200 | $550 | $750 | $950 | $100 |
| 19 | New York Ave | Orange | $16 | $80 | $220 | $600 | $800 | $1,000 | $100 |
| 21 | Kentucky Ave | Red | $18 | $90 | $250 | $700 | $875 | $1,050 | $150 |
| 23 | Indiana Ave | Red | $18 | $90 | $250 | $700 | $875 | $1,050 | $150 |
| 24 | Illinois Ave | Red | $20 | $100 | $300 | $750 | $925 | $1,100 | $150 |
| 26 | Atlantic Ave | Yellow | $22 | $110 | $330 | $800 | $975 | $1,150 | $150 |
| 27 | Ventnor Ave | Yellow | $22 | $110 | $330 | $800 | $975 | $1,150 | $150 |
| 29 | Marvin Gardens | Yellow | $24 | $120 | $360 | $850 | $1,025 | $1,200 | $150 |
| 31 | Pacific Ave | Green | $26 | $130 | $390 | $900 | $1,100 | $1,275 | $200 |
| 32 | North Carolina Ave | Green | $26 | $130 | $390 | $900 | $1,100 | $1,275 | $200 |
| 34 | Pennsylvania Ave | Green | $28 | $150 | $450 | $1,000 | $1,200 | $1,400 | $200 |
| 37 | Park Place | Dark Blue | $35 | $175 | $500 | $1,100 | $1,300 | $1,500 | $200 |
| 39 | Boardwalk | Dark Blue | $50 | $200 | $600 | $1,400 | $1,700 | $2,000 | $200 |

---

## 7. Card Decks

### 7.1 Chance Cards (16 total)

| # | Description | Effect Type | Key Parameters |
|---|-------------|-------------|----------------|
| 1 | Advance to Boardwalk | `ADVANCE_TO` | `destination=39` |
| 2 | Advance to GO (Collect $200) | `ADVANCE_TO` | `destination=0` |
| 3 | Advance to Illinois Avenue | `ADVANCE_TO` | `destination=24` |
| 4 | Advance to St. Charles Place | `ADVANCE_TO` | `destination=11` |
| 5 | Advance to the nearest Railroad (pay double) | `ADVANCE_TO_NEAREST` | `target_type="railroad"` |
| 6 | Advance to the nearest Railroad (pay double) | `ADVANCE_TO_NEAREST` | `target_type="railroad"` |
| 7 | Advance to the nearest Utility (pay 10x dice) | `ADVANCE_TO_NEAREST` | `target_type="utility"` |
| 8 | Bank pays you dividend of $50 | `COLLECT` | `value=50` |
| 9 | Get Out of Jail Free | `GET_OUT_OF_JAIL` | -- |
| 10 | Go Back 3 Spaces | `GO_BACK` | `value=3` |
| 11 | Go to Jail | `GO_TO_JAIL` | -- |
| 12 | Make general repairs ($25/house, $100/hotel) | `REPAIRS` | `per_house=25, per_hotel=100` |
| 13 | Speeding fine $15 | `PAY` | `value=15` |
| 14 | Take a trip to Reading Railroad | `ADVANCE_TO` | `destination=5` |
| 15 | Chairman of the Board -- pay each player $50 | `PAY_EACH_PLAYER` | `value=50` |
| 16 | Building loan matures -- collect $150 | `COLLECT` | `value=150` |

### 7.2 Community Chest Cards (16 total)

| # | Description | Effect Type | Key Parameters |
|---|-------------|-------------|----------------|
| 1 | Advance to GO (Collect $200) | `ADVANCE_TO` | `destination=0` |
| 2 | Bank error in your favor -- collect $200 | `COLLECT` | `value=200` |
| 3 | Doctor's fee -- pay $50 | `PAY` | `value=50` |
| 4 | From sale of stock you get $50 | `COLLECT` | `value=50` |
| 5 | Get Out of Jail Free | `GET_OUT_OF_JAIL` | -- |
| 6 | Go to Jail | `GO_TO_JAIL` | -- |
| 7 | Grand Opera Night -- collect $50 from every player | `COLLECT_FROM_EACH` | `value=50` |
| 8 | Income tax refund -- collect $20 | `COLLECT` | `value=20` |
| 9 | It is your birthday -- collect $10 from every player | `COLLECT_FROM_EACH` | `value=10` |
| 10 | Life insurance matures -- collect $100 | `COLLECT` | `value=100` |
| 11 | Hospital fees -- pay $100 | `PAY` | `value=100` |
| 12 | School fees -- pay $50 | `PAY` | `value=50` |
| 13 | Receive $25 consultancy fee | `COLLECT` | `value=25` |
| 14 | Street repairs ($40/house, $115/hotel) | `REPAIRS` | `per_house=40, per_hotel=115` |
| 15 | Beauty contest -- collect $10 | `COLLECT` | `value=10` |
| 16 | You inherit $100 | `COLLECT` | `value=100` |

---

## 8. Serialization Notes

The engine does **not** include built-in JSON serialization methods. None of the data classes define `to_dict()`, `to_json()`, or similar methods. Serialization for WebSocket transmission and frontend consumption is handled at the API layer.

### Recommended Serialization Approach

Since all frozen dataclasses are compatible with `dataclasses.asdict()`, the following strategies apply:

#### Frozen Dataclasses (DiceRoll, PropertyData, Space, CardEffect, etc.)

```python
from dataclasses import asdict

roll = DiceRoll(die1=3, die2=5)
asdict(roll)  # {"die1": 3, "die2": 5}
# Note: computed properties (total, is_doubles) are NOT included by asdict()
```

For frozen types with computed properties, manual serialization is needed:

```python
{
    "die1": roll.die1,
    "die2": roll.die2,
    "total": roll.total,
    "is_doubles": roll.is_doubles,
}
```

#### Enum Serialization

All enums should serialize to their name or value:

| Enum | Serialization Strategy | Example |
|------|----------------------|---------|
| `SpaceType` | `.name` (uppercase string) | `"PROPERTY"` |
| `ColorGroup` | `.value` (lowercase string) | `"dark_blue"` |
| `CardType` | `.name` | `"CHANCE"` |
| `CardEffectType` | `.name` | `"ADVANCE_TO"` |
| `JailAction` | `.name` | `"PAY_FINE"` |
| `TurnPhase` | `.name` | `"PRE_ROLL"` |
| `GamePhase` | `.name` | `"IN_PROGRESS"` |
| `EventType` | `.name` | `"DICE_ROLLED"` |

Note: `ColorGroup` uses `.value` (the string) rather than `.name` because the value is a human-readable slug, while for all other enums `.name` is the conventional choice.

#### Mutable State (Player, Bank, Game)

These require custom serialization. Key considerations:

- **Player.properties:** Serialize as `list[int]` (already JSON-compatible).
- **Player.houses:** Serialize as `dict[str, int]` (JSON requires string keys; convert `int` keys to strings).
- **Player.mortgaged:** Serialize as `list[int]` (convert `set` to sorted list for determinism).
- **Game._property_owners:** Serialize with string keys.

#### GameEvent Serialization

`GameEvent` is the primary type sent over WebSocket connections. Its `data` field is already a `dict` with JSON-compatible values (strings, ints, bools, lists), so it serializes naturally:

```python
{
    "event_type": event.event_type.name,     # "DICE_ROLLED"
    "player_id": event.player_id,            # 0
    "data": event.data,                      # {"die1": 3, "die2": 5, ...}
    "turn_number": event.turn_number,        # 12
}
```

#### Full Game State Snapshot (for reconnection or state sync)

A complete game state for frontend consumption should include:

```python
{
    "phase": game.phase.name,
    "turn_phase": game.turn_phase.name,
    "turn_number": game.turn_number,
    "current_player_index": game.current_player_index,
    "last_roll": {
        "die1": game.last_roll.die1,
        "die2": game.last_roll.die2,
        "total": game.last_roll.total,
        "is_doubles": game.last_roll.is_doubles,
    } if game.last_roll else None,
    "bank": {
        "houses_available": game.bank.houses_available,
        "hotels_available": game.bank.hotels_available,
    },
    "players": [
        {
            "player_id": p.player_id,
            "name": p.name,
            "position": p.position,
            "cash": p.cash,
            "properties": p.properties,
            "houses": {str(k): v for k, v in p.houses.items()},
            "mortgaged": sorted(p.mortgaged),
            "in_jail": p.in_jail,
            "jail_turns": p.jail_turns,
            "get_out_of_jail_cards": p.get_out_of_jail_cards,
            "is_bankrupt": p.is_bankrupt,
            "consecutive_doubles": p.consecutive_doubles,
            "net_worth": p.net_worth(game.board),
        }
        for p in game.players
    ],
    "property_owners": {
        str(pos): pid for pos, pid in game._property_owners.items()
    },
}
```

---

## 9. Design Notes

### Immutability Strategy

The engine uses Python's `@dataclass(frozen=True)` for all static game data. This provides:
- **Thread safety:** Frozen objects can be shared across threads without locks.
- **Hashability:** Frozen dataclasses are hashable and can be used as dictionary keys or set members.
- **Correctness:** Prevents accidental mutation of game rules data during gameplay.

### Deterministic Randomness

Both the `Dice` and `Deck` classes accept an optional `seed` parameter. When provided, all random operations are deterministic, enabling:
- **Reproducible tests:** Same seed always produces the same game.
- **Replay:** A game can be replayed from its seed.
- **AI training:** Agents can train on deterministic game sequences.

The Community Chest deck uses `seed + 1` to ensure independent shuffling from the Chance deck.

### Event Sourcing

The `Game.events` list is an append-only log. Combined with the initial seed, the full game state can be reconstructed from events alone. The `get_events_since(index)` method supports incremental updates -- the API layer tracks each client's last-seen index and sends only new events.

### Ownership Tracking Redundancy

Property ownership is tracked in two places:
1. **`Player.properties`** -- a list on each player for fast "what do I own?" queries.
2. **`Game._property_owners`** -- a dict for fast "who owns this?" lookups.

Both are kept in sync by `assign_property()`, `transfer_property()`, and `unown_property()`. This dual tracking trades a small amount of storage for O(1) lookups in both directions.
