"""Comprehensive tests for the Monopoly board module."""

import pytest

from monopoly.engine.board import (
    BOARD_SIZE,
    COLOR_GROUP_POSITIONS,
    PROPERTIES,
    RAILROADS,
    UTILITIES,
    Board,
)
from monopoly.engine.types import ColorGroup, SpaceType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def board():
    """Create a fresh Board instance for each test."""
    return Board()


# ===========================================================================
# 1. Board size
# ===========================================================================

class TestBoardSize:
    """The board must have exactly 40 spaces."""

    def test_board_has_40_spaces(self, board):
        assert len(board.spaces) == 40

    def test_board_size_attribute(self, board):
        assert board.size == 40

    def test_board_size_matches_constant(self, board):
        assert board.size == BOARD_SIZE


# ===========================================================================
# 2. Corner spaces
# ===========================================================================

class TestCornerSpaces:
    """GO, Jail, Free Parking, and Go To Jail at their canonical positions."""

    def test_go_at_position_0(self, board):
        space = board.get_space(0)
        assert space.position == 0
        assert space.name == "GO"
        assert space.space_type == SpaceType.GO

    def test_jail_at_position_10(self, board):
        space = board.get_space(10)
        assert space.position == 10
        assert space.name == "Jail / Just Visiting"
        assert space.space_type == SpaceType.JAIL

    def test_free_parking_at_position_20(self, board):
        space = board.get_space(20)
        assert space.position == 20
        assert space.name == "Free Parking"
        assert space.space_type == SpaceType.FREE_PARKING

    def test_go_to_jail_at_position_30(self, board):
        space = board.get_space(30)
        assert space.position == 30
        assert space.name == "Go To Jail"
        assert space.space_type == SpaceType.GO_TO_JAIL


# ===========================================================================
# 3. Property positions, names, prices, and color groups
# ===========================================================================

class TestPropertyPositions:
    """All 22 properties must be at the correct positions with correct metadata."""

    EXPECTED_PROPERTIES = [
        # (position, name, price, color_group)
        (1, "Mediterranean Avenue", 60, ColorGroup.BROWN),
        (3, "Baltic Avenue", 60, ColorGroup.BROWN),
        (6, "Oriental Avenue", 100, ColorGroup.LIGHT_BLUE),
        (8, "Vermont Avenue", 100, ColorGroup.LIGHT_BLUE),
        (9, "Connecticut Avenue", 120, ColorGroup.LIGHT_BLUE),
        (11, "St. Charles Place", 140, ColorGroup.PINK),
        (13, "States Avenue", 140, ColorGroup.PINK),
        (14, "Virginia Avenue", 160, ColorGroup.PINK),
        (16, "St. James Place", 180, ColorGroup.ORANGE),
        (18, "Tennessee Avenue", 180, ColorGroup.ORANGE),
        (19, "New York Avenue", 200, ColorGroup.ORANGE),
        (21, "Kentucky Avenue", 220, ColorGroup.RED),
        (23, "Indiana Avenue", 220, ColorGroup.RED),
        (24, "Illinois Avenue", 240, ColorGroup.RED),
        (26, "Atlantic Avenue", 260, ColorGroup.YELLOW),
        (27, "Ventnor Avenue", 260, ColorGroup.YELLOW),
        (29, "Marvin Gardens", 280, ColorGroup.YELLOW),
        (31, "Pacific Avenue", 300, ColorGroup.GREEN),
        (32, "North Carolina Avenue", 300, ColorGroup.GREEN),
        (34, "Pennsylvania Avenue", 320, ColorGroup.GREEN),
        (37, "Park Place", 350, ColorGroup.DARK_BLUE),
        (39, "Boardwalk", 400, ColorGroup.DARK_BLUE),
    ]

    def test_exactly_22_properties(self):
        assert len(PROPERTIES) == 22

    @pytest.mark.parametrize(
        "position, name, price, color_group",
        EXPECTED_PROPERTIES,
        ids=[p[1] for p in EXPECTED_PROPERTIES],
    )
    def test_property_position_name_price_color(
        self, board, position, name, price, color_group
    ):
        space = board.get_space(position)
        assert space.space_type == SpaceType.PROPERTY
        assert space.name == name
        assert space.property_data is not None
        assert space.property_data.name == name
        assert space.property_data.price == price
        assert space.property_data.color_group == color_group
        assert space.property_data.position == position

    @pytest.mark.parametrize(
        "position, name, price, color_group",
        EXPECTED_PROPERTIES,
        ids=[p[1] + "_mortgage" for p in EXPECTED_PROPERTIES],
    )
    def test_property_mortgage_value_is_half_price(
        self, board, position, name, price, color_group
    ):
        prop = board.get_property_data(position)
        assert prop is not None
        assert prop.mortgage_value == price // 2

    @pytest.mark.parametrize(
        "position, name, price, color_group",
        EXPECTED_PROPERTIES,
        ids=[p[1] + "_rent_tuple" for p in EXPECTED_PROPERTIES],
    )
    def test_property_rent_tuple_length(
        self, board, position, name, price, color_group
    ):
        prop = board.get_property_data(position)
        assert prop is not None
        # (base, 1 house, 2 houses, 3 houses, 4 houses, hotel) = 6 entries
        assert len(prop.rent) == 6


# ===========================================================================
# 4. Railroads
# ===========================================================================

class TestRailroads:
    """All 4 railroads at correct positions with correct names and prices."""

    EXPECTED_RAILROADS = [
        (5, "Reading Railroad"),
        (15, "Pennsylvania Railroad"),
        (25, "B&O Railroad"),
        (35, "Short Line Railroad"),
    ]

    def test_exactly_4_railroads(self):
        assert len(RAILROADS) == 4

    @pytest.mark.parametrize(
        "position, name",
        EXPECTED_RAILROADS,
        ids=[r[1] for r in EXPECTED_RAILROADS],
    )
    def test_railroad_position_and_name(self, board, position, name):
        space = board.get_space(position)
        assert space.space_type == SpaceType.RAILROAD
        assert space.name == name
        assert space.railroad_data is not None
        assert space.railroad_data.name == name
        assert space.railroad_data.position == position

    @pytest.mark.parametrize(
        "position, name",
        EXPECTED_RAILROADS,
        ids=[r[1] + "_price" for r in EXPECTED_RAILROADS],
    )
    def test_railroad_price_is_200(self, board, position, name):
        rr = board.get_railroad_data(position)
        assert rr is not None
        assert rr.price == 200

    @pytest.mark.parametrize(
        "position, name",
        EXPECTED_RAILROADS,
        ids=[r[1] + "_mortgage" for r in EXPECTED_RAILROADS],
    )
    def test_railroad_mortgage_value_is_100(self, board, position, name):
        rr = board.get_railroad_data(position)
        assert rr is not None
        assert rr.mortgage_value == 100


# ===========================================================================
# 5. Utilities
# ===========================================================================

class TestUtilities:
    """Both utilities at correct positions with correct names and prices."""

    EXPECTED_UTILITIES = [
        (12, "Electric Company"),
        (28, "Water Works"),
    ]

    def test_exactly_2_utilities(self):
        assert len(UTILITIES) == 2

    @pytest.mark.parametrize(
        "position, name",
        EXPECTED_UTILITIES,
        ids=[u[1] for u in EXPECTED_UTILITIES],
    )
    def test_utility_position_and_name(self, board, position, name):
        space = board.get_space(position)
        assert space.space_type == SpaceType.UTILITY
        assert space.name == name
        assert space.utility_data is not None
        assert space.utility_data.name == name
        assert space.utility_data.position == position

    @pytest.mark.parametrize(
        "position, name",
        EXPECTED_UTILITIES,
        ids=[u[1] + "_price" for u in EXPECTED_UTILITIES],
    )
    def test_utility_price_is_150(self, board, position, name):
        util = board.get_utility_data(position)
        assert util is not None
        assert util.price == 150

    @pytest.mark.parametrize(
        "position, name",
        EXPECTED_UTILITIES,
        ids=[u[1] + "_mortgage" for u in EXPECTED_UTILITIES],
    )
    def test_utility_mortgage_value_is_75(self, board, position, name):
        util = board.get_utility_data(position)
        assert util is not None
        assert util.mortgage_value == 75


# ===========================================================================
# 6. Chance spaces
# ===========================================================================

class TestChanceSpaces:
    """Chance cards at positions 7, 22, 36."""

    CHANCE_POSITIONS = [7, 22, 36]

    @pytest.mark.parametrize("position", CHANCE_POSITIONS)
    def test_chance_position(self, board, position):
        space = board.get_space(position)
        assert space.space_type == SpaceType.CHANCE
        assert space.name == "Chance"

    def test_exactly_3_chance_spaces(self, board):
        chance_spaces = [
            s for s in board.spaces if s.space_type == SpaceType.CHANCE
        ]
        assert len(chance_spaces) == 3

    def test_chance_positions_are_correct(self, board):
        chance_positions = sorted(
            s.position for s in board.spaces if s.space_type == SpaceType.CHANCE
        )
        assert chance_positions == [7, 22, 36]


# ===========================================================================
# 7. Community Chest spaces
# ===========================================================================

class TestCommunityChestSpaces:
    """Community Chest at positions 2, 17, 33."""

    CC_POSITIONS = [2, 17, 33]

    @pytest.mark.parametrize("position", CC_POSITIONS)
    def test_community_chest_position(self, board, position):
        space = board.get_space(position)
        assert space.space_type == SpaceType.COMMUNITY_CHEST
        assert space.name == "Community Chest"

    def test_exactly_3_community_chest_spaces(self, board):
        cc_spaces = [
            s for s in board.spaces if s.space_type == SpaceType.COMMUNITY_CHEST
        ]
        assert len(cc_spaces) == 3

    def test_community_chest_positions_are_correct(self, board):
        cc_positions = sorted(
            s.position
            for s in board.spaces
            if s.space_type == SpaceType.COMMUNITY_CHEST
        )
        assert cc_positions == [2, 17, 33]


# ===========================================================================
# 8. Tax spaces
# ===========================================================================

class TestTaxSpaces:
    """Income Tax at position 4 ($200) and Luxury Tax at position 38 ($100)."""

    def test_income_tax_position_and_amount(self, board):
        space = board.get_space(4)
        assert space.space_type == SpaceType.TAX
        assert space.name == "Income Tax"
        assert space.tax_data is not None
        assert space.tax_data.amount == 200

    def test_luxury_tax_position_and_amount(self, board):
        space = board.get_space(38)
        assert space.space_type == SpaceType.TAX
        assert space.name == "Luxury Tax"
        assert space.tax_data is not None
        assert space.tax_data.amount == 100

    def test_exactly_2_tax_spaces(self, board):
        tax_spaces = [s for s in board.spaces if s.space_type == SpaceType.TAX]
        assert len(tax_spaces) == 2

    def test_tax_data_positions_match_space_positions(self, board):
        for space in board.spaces:
            if space.tax_data is not None:
                assert space.tax_data.position == space.position


# ===========================================================================
# 9. Color group sizes
# ===========================================================================

class TestColorGroupSizes:
    """Color groups must have the correct number of properties."""

    EXPECTED_GROUP_SIZES = [
        (ColorGroup.BROWN, 2),
        (ColorGroup.LIGHT_BLUE, 3),
        (ColorGroup.PINK, 3),
        (ColorGroup.ORANGE, 3),
        (ColorGroup.RED, 3),
        (ColorGroup.YELLOW, 3),
        (ColorGroup.GREEN, 3),
        (ColorGroup.DARK_BLUE, 2),
    ]

    @pytest.mark.parametrize(
        "color_group, expected_size",
        EXPECTED_GROUP_SIZES,
        ids=[cg[0].value for cg in EXPECTED_GROUP_SIZES],
    )
    def test_color_group_size(self, board, color_group, expected_size):
        positions = board.get_color_group(color_group)
        assert len(positions) == expected_size

    def test_total_properties_in_all_color_groups(self, board):
        total = sum(
            len(board.get_color_group(cg)) for cg in ColorGroup
        )
        assert total == 22

    def test_all_color_groups_present(self, board):
        assert len(COLOR_GROUP_POSITIONS) == 8

    def test_color_group_positions_match_properties(self, board):
        """Every position in a color group must correspond to a PROPERTY space."""
        for color_group in ColorGroup:
            for pos in board.get_color_group(color_group):
                space = board.get_space(pos)
                assert space.space_type == SpaceType.PROPERTY
                assert space.property_data is not None
                assert space.property_data.color_group == color_group


# ===========================================================================
# 10. get_space
# ===========================================================================

class TestGetSpace:
    """Board.get_space returns the correct data for every position."""

    def test_get_space_returns_correct_position(self, board):
        for pos in range(40):
            space = board.get_space(pos)
            assert space.position == pos

    def test_get_space_wraps_at_40(self, board):
        assert board.get_space(40).position == 0
        assert board.get_space(41).position == 1

    def test_get_space_wraps_large_value(self, board):
        assert board.get_space(80).position == 0
        assert board.get_space(83).position == 3

    def test_get_space_property_has_property_data(self, board):
        space = board.get_space(1)
        assert space.property_data is not None
        assert space.railroad_data is None
        assert space.utility_data is None
        assert space.tax_data is None

    def test_get_space_railroad_has_railroad_data(self, board):
        space = board.get_space(5)
        assert space.railroad_data is not None
        assert space.property_data is None
        assert space.utility_data is None
        assert space.tax_data is None

    def test_get_space_utility_has_utility_data(self, board):
        space = board.get_space(12)
        assert space.utility_data is not None
        assert space.property_data is None
        assert space.railroad_data is None
        assert space.tax_data is None

    def test_get_space_tax_has_tax_data(self, board):
        space = board.get_space(4)
        assert space.tax_data is not None
        assert space.property_data is None
        assert space.railroad_data is None
        assert space.utility_data is None

    def test_get_space_go_has_no_special_data(self, board):
        space = board.get_space(0)
        assert space.property_data is None
        assert space.railroad_data is None
        assert space.utility_data is None
        assert space.tax_data is None

    def test_get_space_chance_has_no_special_data(self, board):
        space = board.get_space(7)
        assert space.property_data is None
        assert space.railroad_data is None
        assert space.utility_data is None
        assert space.tax_data is None


# ===========================================================================
# 11. distance_to
# ===========================================================================

class TestDistanceTo:
    """Board.distance_to calculates clockwise distance correctly."""

    def test_same_position(self, board):
        assert board.distance_to(0, 0) == 0
        assert board.distance_to(20, 20) == 0

    def test_forward_movement(self, board):
        assert board.distance_to(0, 10) == 10
        assert board.distance_to(5, 15) == 10
        assert board.distance_to(0, 39) == 39

    def test_wrapping_movement(self, board):
        # From position 35 to position 5 is 10 spaces clockwise
        assert board.distance_to(35, 5) == 10

    def test_wrapping_from_last_to_first(self, board):
        # From position 39 to position 0 is 1 space
        assert board.distance_to(39, 0) == 1

    def test_wrapping_from_30_to_5(self, board):
        # From 30 to 5: 40 - 30 + 5 = 15
        assert board.distance_to(30, 5) == 15

    def test_nearly_full_lap(self, board):
        # From 1 to 0 is 39 spaces clockwise
        assert board.distance_to(1, 0) == 39

    def test_go_to_go_to_jail(self, board):
        assert board.distance_to(0, 30) == 30

    def test_go_to_jail_to_go(self, board):
        assert board.distance_to(30, 0) == 10

    def test_all_corner_distances(self, board):
        assert board.distance_to(0, 10) == 10
        assert board.distance_to(10, 20) == 10
        assert board.distance_to(20, 30) == 10
        assert board.distance_to(30, 0) == 10


# ===========================================================================
# 12. get_nearest_railroad
# ===========================================================================

class TestGetNearestRailroad:
    """Board.get_nearest_railroad returns the next railroad ahead clockwise."""

    def test_from_go(self, board):
        assert board.get_nearest_railroad(0) == 5

    def test_from_position_3(self, board):
        assert board.get_nearest_railroad(3) == 5

    def test_from_position_5_itself(self, board):
        # Position 5 IS a railroad; next one ahead should be 15
        assert board.get_nearest_railroad(5) == 15

    def test_from_position_6(self, board):
        assert board.get_nearest_railroad(6) == 15

    def test_from_position_14(self, board):
        assert board.get_nearest_railroad(14) == 15

    def test_from_position_15(self, board):
        assert board.get_nearest_railroad(15) == 25

    def test_from_position_20(self, board):
        assert board.get_nearest_railroad(20) == 25

    def test_from_position_25(self, board):
        assert board.get_nearest_railroad(25) == 35

    def test_from_position_34(self, board):
        assert board.get_nearest_railroad(34) == 35

    def test_from_position_35_wraps(self, board):
        # Past the last railroad, wraps to Reading Railroad (5)
        assert board.get_nearest_railroad(35) == 5

    def test_from_position_36_wraps(self, board):
        assert board.get_nearest_railroad(36) == 5

    def test_from_position_39_wraps(self, board):
        assert board.get_nearest_railroad(39) == 5


# ===========================================================================
# 13. get_nearest_utility
# ===========================================================================

class TestGetNearestUtility:
    """Board.get_nearest_utility returns the next utility ahead clockwise."""

    def test_from_go(self, board):
        assert board.get_nearest_utility(0) == 12

    def test_from_position_11(self, board):
        assert board.get_nearest_utility(11) == 12

    def test_from_position_12_goes_to_28(self, board):
        # On Electric Company, next is Water Works
        assert board.get_nearest_utility(12) == 28

    def test_from_position_13(self, board):
        assert board.get_nearest_utility(13) == 28

    def test_from_position_27(self, board):
        assert board.get_nearest_utility(27) == 28

    def test_from_position_28_wraps(self, board):
        # On Water Works, wraps to Electric Company
        assert board.get_nearest_utility(28) == 12

    def test_from_position_29_wraps(self, board):
        assert board.get_nearest_utility(29) == 12

    def test_from_position_39_wraps(self, board):
        assert board.get_nearest_utility(39) == 12

    def test_from_position_7(self, board):
        # Chance at 7 -> nearest utility is Electric Company (12)
        assert board.get_nearest_utility(7) == 12

    def test_from_position_22(self, board):
        # Chance at 22 -> nearest utility is Water Works (28)
        assert board.get_nearest_utility(22) == 28

    def test_from_position_36_wraps(self, board):
        # Chance at 36 -> wraps to Electric Company (12)
        assert board.get_nearest_utility(36) == 12


# ===========================================================================
# 14. is_purchasable
# ===========================================================================

class TestIsPurchasable:
    """Board.is_purchasable returns True for properties, railroads, and utilities."""

    @pytest.mark.parametrize("position", sorted(PROPERTIES.keys()))
    def test_properties_are_purchasable(self, board, position):
        assert board.is_purchasable(position) is True

    @pytest.mark.parametrize("position", sorted(RAILROADS.keys()))
    def test_railroads_are_purchasable(self, board, position):
        assert board.is_purchasable(position) is True

    @pytest.mark.parametrize("position", sorted(UTILITIES.keys()))
    def test_utilities_are_purchasable(self, board, position):
        assert board.is_purchasable(position) is True

    NON_PURCHASABLE = [0, 2, 4, 7, 10, 17, 20, 22, 30, 33, 36, 38]

    @pytest.mark.parametrize("position", NON_PURCHASABLE)
    def test_non_purchasable_spaces(self, board, position):
        assert board.is_purchasable(position) is False

    def test_go_is_not_purchasable(self, board):
        assert board.is_purchasable(0) is False

    def test_jail_is_not_purchasable(self, board):
        assert board.is_purchasable(10) is False

    def test_free_parking_is_not_purchasable(self, board):
        assert board.is_purchasable(20) is False

    def test_go_to_jail_is_not_purchasable(self, board):
        assert board.is_purchasable(30) is False

    def test_chance_is_not_purchasable(self, board):
        assert board.is_purchasable(7) is False

    def test_community_chest_is_not_purchasable(self, board):
        assert board.is_purchasable(2) is False

    def test_tax_is_not_purchasable(self, board):
        assert board.is_purchasable(4) is False


# ===========================================================================
# 15. get_purchase_price
# ===========================================================================

class TestGetPurchasePrice:
    """Board.get_purchase_price returns the correct price for purchasable spaces."""

    def test_property_prices(self, board):
        assert board.get_purchase_price(1) == 60    # Mediterranean Avenue
        assert board.get_purchase_price(39) == 400  # Boardwalk
        assert board.get_purchase_price(24) == 240  # Illinois Avenue

    def test_railroad_price(self, board):
        assert board.get_purchase_price(5) == 200
        assert board.get_purchase_price(15) == 200
        assert board.get_purchase_price(25) == 200
        assert board.get_purchase_price(35) == 200

    def test_utility_price(self, board):
        assert board.get_purchase_price(12) == 150
        assert board.get_purchase_price(28) == 150

    def test_non_purchasable_returns_0(self, board):
        assert board.get_purchase_price(0) == 0   # GO
        assert board.get_purchase_price(2) == 0   # Community Chest
        assert board.get_purchase_price(4) == 0   # Income Tax
        assert board.get_purchase_price(7) == 0   # Chance
        assert board.get_purchase_price(10) == 0  # Jail
        assert board.get_purchase_price(20) == 0  # Free Parking
        assert board.get_purchase_price(30) == 0  # Go To Jail
        assert board.get_purchase_price(38) == 0  # Luxury Tax

    @pytest.mark.parametrize(
        "position, expected_price",
        [
            (1, 60), (3, 60),
            (6, 100), (8, 100), (9, 120),
            (11, 140), (13, 140), (14, 160),
            (16, 180), (18, 180), (19, 200),
            (21, 220), (23, 220), (24, 240),
            (26, 260), (27, 260), (29, 280),
            (31, 300), (32, 300), (34, 320),
            (37, 350), (39, 400),
        ],
    )
    def test_all_property_purchase_prices(self, board, position, expected_price):
        assert board.get_purchase_price(position) == expected_price


# ===========================================================================
# 16. Board data helper methods
# ===========================================================================

class TestBoardDataHelpers:
    """get_property_data, get_railroad_data, get_utility_data edge cases."""

    def test_get_property_data_returns_none_for_non_property(self, board):
        assert board.get_property_data(0) is None
        assert board.get_property_data(5) is None
        assert board.get_property_data(12) is None
        assert board.get_property_data(7) is None

    def test_get_railroad_data_returns_none_for_non_railroad(self, board):
        assert board.get_railroad_data(0) is None
        assert board.get_railroad_data(1) is None
        assert board.get_railroad_data(12) is None

    def test_get_utility_data_returns_none_for_non_utility(self, board):
        assert board.get_utility_data(0) is None
        assert board.get_utility_data(1) is None
        assert board.get_utility_data(5) is None

    def test_get_property_data_returns_correct_data(self, board):
        prop = board.get_property_data(39)
        assert prop is not None
        assert prop.name == "Boardwalk"
        assert prop.price == 400
        assert prop.color_group == ColorGroup.DARK_BLUE

    def test_get_railroad_data_returns_correct_data(self, board):
        rr = board.get_railroad_data(25)
        assert rr is not None
        assert rr.name == "B&O Railroad"

    def test_get_utility_data_returns_correct_data(self, board):
        util = board.get_utility_data(28)
        assert util is not None
        assert util.name == "Water Works"


# ===========================================================================
# 17. Board completeness and consistency
# ===========================================================================

class TestBoardCompleteness:
    """Verify the board is internally consistent and complete."""

    def test_every_position_has_a_name(self, board):
        for pos in range(40):
            space = board.get_space(pos)
            assert space.name, f"Position {pos} has no name"

    def test_every_position_has_a_space_type(self, board):
        for pos in range(40):
            space = board.get_space(pos)
            assert isinstance(space.space_type, SpaceType)

    def test_space_types_cover_all_positions(self, board):
        """Ensure every position 0-39 has a valid SpaceType."""
        for pos in range(40):
            space = board.get_space(pos)
            assert space.space_type in SpaceType

    def test_no_duplicate_property_names(self, board):
        property_names = [p.name for p in PROPERTIES.values()]
        assert len(property_names) == len(set(property_names))

    def test_house_costs_increase_by_color_group(self, board):
        """House costs should be 50 for brown/light_blue, 100 for pink/orange,
        150 for red/yellow, 200 for green/dark_blue."""
        expected_house_costs = {
            ColorGroup.BROWN: 50,
            ColorGroup.LIGHT_BLUE: 50,
            ColorGroup.PINK: 100,
            ColorGroup.ORANGE: 100,
            ColorGroup.RED: 150,
            ColorGroup.YELLOW: 150,
            ColorGroup.GREEN: 200,
            ColorGroup.DARK_BLUE: 200,
        }
        for color_group, expected_cost in expected_house_costs.items():
            for pos in board.get_color_group(color_group):
                prop = board.get_property_data(pos)
                assert prop is not None
                assert prop.house_cost == expected_cost, (
                    f"{prop.name} has house_cost {prop.house_cost}, "
                    f"expected {expected_cost}"
                )

    def test_rent_values_are_ascending(self, board):
        """For every property, rent should increase with more houses."""
        for pos, prop in PROPERTIES.items():
            for i in range(len(prop.rent) - 1):
                assert prop.rent[i] < prop.rent[i + 1], (
                    f"{prop.name}: rent[{i}]={prop.rent[i]} >= "
                    f"rent[{i+1}]={prop.rent[i+1]}"
                )
