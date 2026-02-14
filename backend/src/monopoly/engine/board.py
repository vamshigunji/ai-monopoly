"""Monopoly board layout — all 40 spaces with complete property data."""

from monopoly.engine.types import (
    ColorGroup,
    PropertyData,
    RailroadData,
    Space,
    SpaceType,
    TaxData,
    UtilityData,
)


# ── Property definitions with full rent tables ──────────────────────────────
# Rent tuple: (base, 1_house, 2_houses, 3_houses, 4_houses, hotel)

PROPERTIES: dict[int, PropertyData] = {
    1: PropertyData("Mediterranean Avenue", 1, ColorGroup.BROWN, 60, 30,
                    (2, 10, 30, 90, 160, 250), 50),
    3: PropertyData("Baltic Avenue", 3, ColorGroup.BROWN, 60, 30,
                    (4, 20, 60, 180, 320, 450), 50),

    6: PropertyData("Oriental Avenue", 6, ColorGroup.LIGHT_BLUE, 100, 50,
                    (6, 30, 90, 270, 400, 550), 50),
    8: PropertyData("Vermont Avenue", 8, ColorGroup.LIGHT_BLUE, 100, 50,
                    (6, 30, 90, 270, 400, 550), 50),
    9: PropertyData("Connecticut Avenue", 9, ColorGroup.LIGHT_BLUE, 120, 60,
                    (8, 40, 100, 300, 450, 600), 50),

    11: PropertyData("St. Charles Place", 11, ColorGroup.PINK, 140, 70,
                     (10, 50, 150, 450, 625, 750), 100),
    13: PropertyData("States Avenue", 13, ColorGroup.PINK, 140, 70,
                     (10, 50, 150, 450, 625, 750), 100),
    14: PropertyData("Virginia Avenue", 14, ColorGroup.PINK, 160, 80,
                     (12, 60, 180, 500, 700, 900), 100),

    16: PropertyData("St. James Place", 16, ColorGroup.ORANGE, 180, 90,
                     (14, 70, 200, 550, 750, 950), 100),
    18: PropertyData("Tennessee Avenue", 18, ColorGroup.ORANGE, 180, 90,
                     (14, 70, 200, 550, 750, 950), 100),
    19: PropertyData("New York Avenue", 19, ColorGroup.ORANGE, 200, 100,
                     (16, 80, 220, 600, 800, 1000), 100),

    21: PropertyData("Kentucky Avenue", 21, ColorGroup.RED, 220, 110,
                     (18, 90, 250, 700, 875, 1050), 150),
    23: PropertyData("Indiana Avenue", 23, ColorGroup.RED, 220, 110,
                     (18, 90, 250, 700, 875, 1050), 150),
    24: PropertyData("Illinois Avenue", 24, ColorGroup.RED, 240, 120,
                     (20, 100, 300, 750, 925, 1100), 150),

    26: PropertyData("Atlantic Avenue", 26, ColorGroup.YELLOW, 260, 130,
                     (22, 110, 330, 800, 975, 1150), 150),
    27: PropertyData("Ventnor Avenue", 27, ColorGroup.YELLOW, 260, 130,
                     (22, 110, 330, 800, 975, 1150), 150),
    29: PropertyData("Marvin Gardens", 29, ColorGroup.YELLOW, 280, 140,
                     (24, 120, 360, 850, 1025, 1200), 150),

    31: PropertyData("Pacific Avenue", 31, ColorGroup.GREEN, 300, 150,
                     (26, 130, 390, 900, 1100, 1275), 200),
    32: PropertyData("North Carolina Avenue", 32, ColorGroup.GREEN, 300, 150,
                     (26, 130, 390, 900, 1100, 1275), 200),
    34: PropertyData("Pennsylvania Avenue", 34, ColorGroup.GREEN, 320, 160,
                     (28, 150, 450, 1000, 1200, 1400), 200),

    37: PropertyData("Park Place", 37, ColorGroup.DARK_BLUE, 350, 175,
                     (35, 175, 500, 1100, 1300, 1500), 200),
    39: PropertyData("Boardwalk", 39, ColorGroup.DARK_BLUE, 400, 200,
                     (50, 200, 600, 1400, 1700, 2000), 200),
}

RAILROADS: dict[int, RailroadData] = {
    5: RailroadData("Reading Railroad", 5),
    15: RailroadData("Pennsylvania Railroad", 15),
    25: RailroadData("B&O Railroad", 25),
    35: RailroadData("Short Line Railroad", 35),
}

UTILITIES: dict[int, UtilityData] = {
    12: UtilityData("Electric Company", 12),
    28: UtilityData("Water Works", 28),
}

# Railroad rent based on number owned
RAILROAD_RENTS = {1: 25, 2: 50, 3: 100, 4: 200}

# Utility multiplier based on number owned
UTILITY_MULTIPLIERS = {1: 4, 2: 10}

# Color group to positions mapping
COLOR_GROUP_POSITIONS: dict[ColorGroup, list[int]] = {
    ColorGroup.BROWN: [1, 3],
    ColorGroup.LIGHT_BLUE: [6, 8, 9],
    ColorGroup.PINK: [11, 13, 14],
    ColorGroup.ORANGE: [16, 18, 19],
    ColorGroup.RED: [21, 23, 24],
    ColorGroup.YELLOW: [26, 27, 29],
    ColorGroup.GREEN: [31, 32, 34],
    ColorGroup.DARK_BLUE: [37, 39],
}

BOARD_SIZE = 40


def _build_spaces() -> list[Space]:
    """Build all 40 board spaces."""
    spaces: list[Space] = []

    definitions = {
        0: ("GO", SpaceType.GO),
        1: ("Mediterranean Avenue", SpaceType.PROPERTY),
        2: ("Community Chest", SpaceType.COMMUNITY_CHEST),
        3: ("Baltic Avenue", SpaceType.PROPERTY),
        4: ("Income Tax", SpaceType.TAX),
        5: ("Reading Railroad", SpaceType.RAILROAD),
        6: ("Oriental Avenue", SpaceType.PROPERTY),
        7: ("Chance", SpaceType.CHANCE),
        8: ("Vermont Avenue", SpaceType.PROPERTY),
        9: ("Connecticut Avenue", SpaceType.PROPERTY),
        10: ("Jail / Just Visiting", SpaceType.JAIL),
        11: ("St. Charles Place", SpaceType.PROPERTY),
        12: ("Electric Company", SpaceType.UTILITY),
        13: ("States Avenue", SpaceType.PROPERTY),
        14: ("Virginia Avenue", SpaceType.PROPERTY),
        15: ("Pennsylvania Railroad", SpaceType.RAILROAD),
        16: ("St. James Place", SpaceType.PROPERTY),
        17: ("Community Chest", SpaceType.COMMUNITY_CHEST),
        18: ("Tennessee Avenue", SpaceType.PROPERTY),
        19: ("New York Avenue", SpaceType.PROPERTY),
        20: ("Free Parking", SpaceType.FREE_PARKING),
        21: ("Kentucky Avenue", SpaceType.PROPERTY),
        22: ("Chance", SpaceType.CHANCE),
        23: ("Indiana Avenue", SpaceType.PROPERTY),
        24: ("Illinois Avenue", SpaceType.PROPERTY),
        25: ("B&O Railroad", SpaceType.RAILROAD),
        26: ("Atlantic Avenue", SpaceType.PROPERTY),
        27: ("Ventnor Avenue", SpaceType.PROPERTY),
        28: ("Water Works", SpaceType.UTILITY),
        29: ("Marvin Gardens", SpaceType.PROPERTY),
        30: ("Go To Jail", SpaceType.GO_TO_JAIL),
        31: ("Pacific Avenue", SpaceType.PROPERTY),
        32: ("North Carolina Avenue", SpaceType.PROPERTY),
        33: ("Community Chest", SpaceType.COMMUNITY_CHEST),
        34: ("Pennsylvania Avenue", SpaceType.PROPERTY),
        35: ("Short Line Railroad", SpaceType.RAILROAD),
        36: ("Chance", SpaceType.CHANCE),
        37: ("Park Place", SpaceType.PROPERTY),
        38: ("Luxury Tax", SpaceType.TAX),
        39: ("Boardwalk", SpaceType.PROPERTY),
    }

    taxes = {
        4: TaxData("Income Tax", 4, 200),
        38: TaxData("Luxury Tax", 38, 100),
    }

    for pos in range(BOARD_SIZE):
        name, space_type = definitions[pos]
        spaces.append(Space(
            position=pos,
            name=name,
            space_type=space_type,
            property_data=PROPERTIES.get(pos),
            railroad_data=RAILROADS.get(pos),
            utility_data=UTILITIES.get(pos),
            tax_data=taxes.get(pos),
        ))

    return spaces


class Board:
    """The Monopoly game board with all 40 spaces."""

    def __init__(self) -> None:
        self.spaces: list[Space] = _build_spaces()
        self.size = BOARD_SIZE

    def get_space(self, position: int) -> Space:
        """Get the space at a given position (0-39)."""
        return self.spaces[position % self.size]

    def get_color_group(self, color: ColorGroup) -> list[int]:
        """Get all property positions in a color group."""
        return COLOR_GROUP_POSITIONS[color]

    def get_property_data(self, position: int) -> PropertyData | None:
        """Get property data for a position, or None if not a property."""
        return PROPERTIES.get(position)

    def get_railroad_data(self, position: int) -> RailroadData | None:
        """Get railroad data for a position, or None if not a railroad."""
        return RAILROADS.get(position)

    def get_utility_data(self, position: int) -> UtilityData | None:
        """Get utility data for a position, or None if not a utility."""
        return UTILITIES.get(position)

    def distance_to(self, from_pos: int, to_pos: int) -> int:
        """Calculate clockwise distance from one position to another."""
        return (to_pos - from_pos) % self.size

    def get_nearest_railroad(self, position: int) -> int:
        """Get the position of the nearest railroad ahead of the given position."""
        railroad_positions = sorted(RAILROADS.keys())  # [5, 15, 25, 35]
        for rr in railroad_positions:
            if rr > position:
                return rr
        return railroad_positions[0]  # wrap around to Reading Railroad

    def get_nearest_utility(self, position: int) -> int:
        """Get the position of the nearest utility ahead of the given position."""
        utility_positions = sorted(UTILITIES.keys())  # [12, 28]
        for util in utility_positions:
            if util > position:
                return util
        return utility_positions[0]  # wrap around to Electric Company

    def is_purchasable(self, position: int) -> bool:
        """Check if a space can be purchased."""
        space = self.get_space(position)
        return space.space_type in (SpaceType.PROPERTY, SpaceType.RAILROAD, SpaceType.UTILITY)

    def get_purchase_price(self, position: int) -> int:
        """Get the purchase price for a buyable space."""
        if position in PROPERTIES:
            return PROPERTIES[position].price
        if position in RAILROADS:
            return RAILROADS[position].price
        if position in UTILITIES:
            return UTILITIES[position].price
        return 0
