from houdini.games import ITable

import random


class TreasureHuntLogic(ITable):

    def __init__(self):
        self.map_width = 10
        self.map_height = 10
        self.coins_hidden = 0
        self.gems_hidden = 0
        self.turns = 12
        self.gem_value = 25
        self.coin_value = 1
        self.gem_locations = []
        self.treasure_map = []
        self.coins_found = 0
        self.gems_found = 0
        self.emerald_found = 0
        self.dig_record_names = []
        self.dig_record_directions = []
        self.dig_record_numbers = []
        self.emerald = 0
        self.current_player = 1
        self.generate_map()

    def make_move(self, movie, direction, spade):
        if direction == 'right':
            row = self.treasure_map[spade]
            for column, tiles in enumerate(row):
                self.dig(spade, column)
        elif direction == 'down':
            for row, columns in enumerate(self.treasure_map):
                self.dig(row, spade)
        self.turns -= 1
        self.dig_record_names.append(movie)
        self.dig_record_directions.append(direction)
        self.dig_record_numbers.append(spade)

    def is_valid_move(self, movie, direction, spade):
        test_movie = direction + 'button' + str(spade) + '_mc'
        if test_movie == movie and direction in ['down', 'right'] and 0 <= spade <= 9:
            if direction == 'right':
                row = self.treasure_map[spade]
                for column, tiles in enumerate(row):
                    treasure, digs = self.treasure_map[spade][column]
                    if digs == 2:
                        return False
            elif direction == 'down':
                for row, columns in enumerate(self.treasure_map):
                    treasure, digs = self.treasure_map[row][spade]
                    if digs == 2:
                        return False
            return True
        return False

    def get_string(self):
        treasure_map = ','.join(str(item) for row in self.treasure_map for item, digs in row)
        gem_locations = ','.join(self.gem_locations)
        game_array = [self.map_width, self.map_height, self.coins_hidden, self.gems_hidden, self.turns,
                      self.gem_value, self.coin_value, gem_locations, treasure_map]
        if self.dig_record_numbers:
            game_array += [self.coins_found, self.gems_found, self.emerald_found]
            game_array += [','.join(self.dig_record_names), ','.join(self.dig_record_directions),
                           ','.join(map(str, self.dig_record_numbers))]
        return '%'.join(map(str, game_array))

    def generate_map(self):
        for row in range(self.map_height):
            self.treasure_map.append([])
            for column in range(self.map_width):
                self.treasure_map[row].append([self.generate_treasure(row, column), 0])

    def generate_treasure(self, row, column):
        treasure_type = [('None', 0), ('Coin', 1), ('Gem', 2), ('Emerald', 4)]
        if self.get_gem_by_piece(row, column):
            return 3
        if row + 1 == self.map_height or column + 1 == self.map_width:
            treasure_type = treasure_type[:2]
        name, value = random.choices(treasure_type, weights=[60, 40, 1, 0.5][:len(treasure_type)])[0]
        self.coins_hidden += 1 if value == 1 else self.coins_hidden
        if value > 1:
            self.gems_hidden += 1
            self.gem_locations.append(str(row) + ',' + str(column))
        if self.emerald:
            return 2
        if value == 4 and not self.emerald:
            self.emerald = 1
        return value

    def get_gem_by_piece(self, row, column):
        for delta_row, delta_col in [(0, -1), (-1, -1), (-1, 0)]:
            if row > 0 and column > 0:
                treasure, digs = self.treasure_map[row + delta_row][column + delta_col]
                if treasure == 2 or treasure == 4:
                    return row + delta_row, column + delta_col
        return False

    def is_gem_uncovered(self, row, column):
        for delta_row, delta_col in [(0, 1), (1, 1), (1, 0)]:
            treasure, digs = self.treasure_map[row + delta_row][column + delta_col]
            if digs != 2:
                return False
        return True

    def dig(self, row, column):
        self.treasure_map[row][column][1] += 1
        treasure, digs = self.treasure_map[row][column]
        if digs == 2:
            if treasure == 1:
                self.coins_found += 1
            elif treasure == 2 or treasure == 4:
                if not self.is_gem_uncovered(row, column):
                    return
                self.gems_found += 1
            elif treasure == 3:
                treasure_row, treasure_col = self.get_gem_by_piece(row, column)
                if not self.is_gem_uncovered(treasure_row, treasure_col):
                    return
                self.gems_found += 1
                if treasure == 4:
                    self.emerald_found = 1

    def determine_winnings(self):
        total = self.coins_found * self.coin_value
        total += self.gems_found * self.gem_value
        total += self.emerald_found * self.gem_value * 3
        return total
