import random

from houdini import ITable, handlers
from houdini.handlers import XTPacket


class TreasureHuntLogic(ITable):

    def __init__(self):
        self.map_width = 10
        self.map_height = 10
        self.coins_hidden = 0
        self.gems_hidden = 0
        self.turns = 12
        self.emerald_value = 100
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
        name, value = random.choices(treasure_type, weights=[80, 20, 1, 5][:len(treasure_type)])[0]
        if value == 1:
            self.coins_hidden += 1
        if value > 1:
            self.gems_hidden += 1
            self.gem_locations.append(f'{row},{column}')
            if self.emerald:
                return 2
        if value == 4 and not self.emerald:
            self.emerald = 1
        return value

    def get_gem_by_piece(self, row, column):
        if row > 0:
            treasure, digs = self.treasure_map[row - 1][column]
            if treasure == 2 or treasure == 4:
                return row - 1, column
        if column > 0:
            treasure, digs = self.treasure_map[row][column - 1]
            if treasure == 2 or treasure == 4:
                return row, column - 1
        if row > 0 and column > 0:
            treasure, digs = self.treasure_map[row - 1][column - 1]
            if treasure == 2 or treasure == 4:
                return row - 1, column - 1
        return None

    def is_gem_uncovered(self, row, column):
        if row == self.map_width - 1 or column == self.map_height - 1:
            return False
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
            elif treasure == 2:
                if self.is_gem_uncovered(row, column):
                    self.gems_found += 1
            elif treasure == 4:
                if self.is_gem_uncovered(row, column):
                    self.emerald_found = 1
            elif treasure == 3:
                treasure_row, treasure_col = self.get_gem_by_piece(row, column)
                treasure, digs = self.treasure_map[treasure_row][treasure_col]
                if self.is_gem_uncovered(treasure_row, treasure_col):
                    if treasure == 2:
                        self.gems_found += 1
                    elif treasure == 4:
                        self.emerald_found = 1

    def determine_winnings(self):
        total = self.coins_found * self.coin_value
        total += self.gems_found * self.gem_value
        total += self.emerald_found * self.emerald_value
        return total


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.table(TreasureHuntLogic)
async def handle_get_game(p):
    if len(p.table.penguins) == 2:
        player_one = p.table.penguins[0]
        await p.send_xt('gz', player_one.safe_name, str())
    else:
        await p.send_xt('gz', p.table.get_string())


@handlers.handler(XTPacket('jz',  ext='z'))
@handlers.table(TreasureHuntLogic)
async def handle_join_game(p):
    game_full = len(p.table.penguins) > 2
    if not game_full:
        seat_id = p.table.get_seat_id(p)
        await p.send_xt('jz', seat_id)
        await p.table.send_xt('uz', seat_id, p.safe_name)
        if len(p.table.penguins) == 2:
            await p.table.send_xt('sz', p.table.get_string())


@handlers.handler(XTPacket('zm', ext='z'))
@handlers.table(TreasureHuntLogic)
async def handle_send_move(p, movie: str, direction: str, spade: int):
    try:
        seat_id = p.table.get_seat_id(p)
        is_player = seat_id < 2
        game_ready = len(p.table.penguins) > 1
        if is_player and game_ready:
            current_player = p.table.penguins[p.table.logic.current_player - 1]
            if current_player != p:
                return
            if not p.table.logic.is_valid_move(movie, direction, spade):
                return
            p.table.logic.make_move(movie, direction, spade)
            await p.table.send_xt('zm', movie, direction, spade)
            opponent = p.table.penguins[1 if p.table.logic.current_player == 1 else 0]
            if p.table.logic.turns >= 6 and p.table.logic.gems_found > 0:
                await p.add_stamp(p.server.stamps[420])
                await opponent.add_stamp(p.server.stamps[420])
            if p.table.logic.turns >= 5 and p.table.logic.gems_found >= 2:
                await p.add_stamp(p.server.stamps[422])
                await opponent.add_stamp(p.server.stamps[422])
            if p.table.logic.gems_found >= 2:
                await p.add_stamp(p.server.stamps[414])
                await opponent.add_stamp(p.server.stamps[414])
            if p.table.logic.coins_found >= 8:
                await p.add_stamp(p.server.stamps[416])
                await opponent.add_stamp(p.server.stamps[416])
            if p.table.logic.emerald_found:
                await p.add_stamp(p.server.stamps[418])
                await opponent.add_stamp(p.server.stamps[418])
            if p.table.logic.turns == 0:
                winnings = p.table.logic.determine_winnings()
                await p.add_coins(winnings)
                await opponent.add_coins(winnings)
                await p.table.reset()
                return
            p.table.logic.current_player = 2 if p.table.logic.current_player == 1 else 1
    except (KeyError, ValueError):
        p.logger.warn(f'Invalid treasure hunt move made by {p}')
