/**
 * Monopoly board data - shared across components
 * Property rent arrays: [base, 1 house, 2 houses, 3 houses, 4 houses, hotel]
 */

export const BOARD_SPACES = [
  { position: 0, name: "GO", space_type: "GO" },
  { position: 1, name: "Mediterranean Avenue", space_type: "PROPERTY", color_group: "BROWN", price: 60, rent: [2, 10, 30, 90, 160, 250], house_cost: 50, mortgage: 30 },
  { position: 2, name: "Community Chest", space_type: "COMMUNITY_CHEST" },
  { position: 3, name: "Baltic Avenue", space_type: "PROPERTY", color_group: "BROWN", price: 60, rent: [4, 20, 60, 180, 320, 450], house_cost: 50, mortgage: 30 },
  { position: 4, name: "Income Tax", space_type: "TAX", price: 200 },
  { position: 5, name: "Reading Railroad", space_type: "RAILROAD", price: 200, rent: [25, 50, 100, 200], mortgage: 100 },
  { position: 6, name: "Oriental Avenue", space_type: "PROPERTY", color_group: "LIGHT_BLUE", price: 100, rent: [6, 30, 90, 270, 400, 550], house_cost: 50, mortgage: 50 },
  { position: 7, name: "Chance", space_type: "CHANCE" },
  { position: 8, name: "Vermont Avenue", space_type: "PROPERTY", color_group: "LIGHT_BLUE", price: 100, rent: [6, 30, 90, 270, 400, 550], house_cost: 50, mortgage: 50 },
  { position: 9, name: "Connecticut Avenue", space_type: "PROPERTY", color_group: "LIGHT_BLUE", price: 120, rent: [8, 40, 100, 300, 450, 600], house_cost: 50, mortgage: 60 },
  { position: 10, name: "Jail", space_type: "JAIL" },
  { position: 11, name: "St. Charles Place", space_type: "PROPERTY", color_group: "PINK", price: 140, rent: [10, 50, 150, 450, 625, 750], house_cost: 100, mortgage: 70 },
  { position: 12, name: "Electric Company", space_type: "UTILITY", price: 150, mortgage: 75 },
  { position: 13, name: "States Avenue", space_type: "PROPERTY", color_group: "PINK", price: 140, rent: [10, 50, 150, 450, 625, 750], house_cost: 100, mortgage: 70 },
  { position: 14, name: "Virginia Avenue", space_type: "PROPERTY", color_group: "PINK", price: 160, rent: [12, 60, 180, 500, 700, 900], house_cost: 100, mortgage: 80 },
  { position: 15, name: "Pennsylvania Railroad", space_type: "RAILROAD", price: 200, rent: [25, 50, 100, 200], mortgage: 100 },
  { position: 16, name: "St. James Place", space_type: "PROPERTY", color_group: "ORANGE", price: 180, rent: [14, 70, 200, 550, 750, 950], house_cost: 100, mortgage: 90 },
  { position: 17, name: "Community Chest", space_type: "COMMUNITY_CHEST" },
  { position: 18, name: "Tennessee Avenue", space_type: "PROPERTY", color_group: "ORANGE", price: 180, rent: [14, 70, 200, 550, 750, 950], house_cost: 100, mortgage: 90 },
  { position: 19, name: "New York Avenue", space_type: "PROPERTY", color_group: "ORANGE", price: 200, rent: [16, 80, 220, 600, 800, 1000], house_cost: 100, mortgage: 100 },
  { position: 20, name: "Free Parking", space_type: "FREE_PARKING" },
  { position: 21, name: "Kentucky Avenue", space_type: "PROPERTY", color_group: "RED", price: 220, rent: [18, 90, 250, 700, 875, 1050], house_cost: 150, mortgage: 110 },
  { position: 22, name: "Chance", space_type: "CHANCE" },
  { position: 23, name: "Indiana Avenue", space_type: "PROPERTY", color_group: "RED", price: 220, rent: [18, 90, 250, 700, 875, 1050], house_cost: 150, mortgage: 110 },
  { position: 24, name: "Illinois Avenue", space_type: "PROPERTY", color_group: "RED", price: 240, rent: [20, 100, 300, 750, 925, 1100], house_cost: 150, mortgage: 120 },
  { position: 25, name: "B&O Railroad", space_type: "RAILROAD", price: 200, rent: [25, 50, 100, 200], mortgage: 100 },
  { position: 26, name: "Atlantic Avenue", space_type: "PROPERTY", color_group: "YELLOW", price: 260, rent: [22, 110, 330, 800, 975, 1150], house_cost: 150, mortgage: 130 },
  { position: 27, name: "Ventnor Avenue", space_type: "PROPERTY", color_group: "YELLOW", price: 260, rent: [22, 110, 330, 800, 975, 1150], house_cost: 150, mortgage: 130 },
  { position: 28, name: "Water Works", space_type: "UTILITY", price: 150, mortgage: 75 },
  { position: 29, name: "Marvin Gardens", space_type: "PROPERTY", color_group: "YELLOW", price: 280, rent: [24, 120, 360, 850, 1025, 1200], house_cost: 150, mortgage: 140 },
  { position: 30, name: "Go To Jail", space_type: "GO_TO_JAIL" },
  { position: 31, name: "Pacific Avenue", space_type: "PROPERTY", color_group: "GREEN", price: 300, rent: [26, 130, 390, 900, 1100, 1275], house_cost: 200, mortgage: 150 },
  { position: 32, name: "North Carolina Avenue", space_type: "PROPERTY", color_group: "GREEN", price: 300, rent: [26, 130, 390, 900, 1100, 1275], house_cost: 200, mortgage: 150 },
  { position: 33, name: "Community Chest", space_type: "COMMUNITY_CHEST" },
  { position: 34, name: "Pennsylvania Avenue", space_type: "PROPERTY", color_group: "GREEN", price: 320, rent: [28, 150, 450, 1000, 1200, 1400], house_cost: 200, mortgage: 160 },
  { position: 35, name: "Short Line Railroad", space_type: "RAILROAD", price: 200, rent: [25, 50, 100, 200], mortgage: 100 },
  { position: 36, name: "Chance", space_type: "CHANCE" },
  { position: 37, name: "Park Place", space_type: "PROPERTY", color_group: "DARK_BLUE", price: 350, rent: [35, 175, 500, 1100, 1300, 1500], house_cost: 200, mortgage: 175 },
  { position: 38, name: "Luxury Tax", space_type: "TAX", price: 100 },
  { position: 39, name: "Boardwalk", space_type: "PROPERTY", color_group: "DARK_BLUE", price: 400, rent: [50, 200, 600, 1400, 1700, 2000], house_cost: 200, mortgage: 200 },
];

export function getSpaceName(position: number): string {
  return BOARD_SPACES[position]?.name || `Position ${position}`;
}
