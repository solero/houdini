from random import uniform

from houdini.data import db, AbstractDataCollection


class ConnectFourLogic:

    def __init__(self):
        self.current_player = 1
        self.board = [[0 for _ in range(6)] for _ in range(7)]

    def place_chip(self, col, row):
        self.board[col][row] = self.current_player

    def is_position_win(self, col, row):
        for delta_row, delta_col in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            streak = 1
            for delta in (1, -1):
                delta_row *= delta
                delta_col *= delta
                next_row = row + delta_row
                next_col = col + delta_col
                while 0 <= next_row < 6 and 0 <= next_col < 7:
                    if self.board[next_col][next_row] == self.current_player:
                        streak += 1
                    else:
                        break
                    if streak == 4:
                        return True
                    next_row += delta_row
                    next_col += delta_col
        return False

    def is_valid_move(self, col, row):
        if 0 <= row <= 5 and 0 <= col <= 6:
            if row == 5 or (self.board[col][row] == 0 and self.board[col][row + 1]):
                return True
        return False

    def is_board_full(self):
        for col in self.board:
            if not col[0]:
                return False
        return True

    def get_string(self):
        return ','.join(str(item) for row in self.board for item in row)


class MancalaLogic:

    def __init__(self):
        self.current_player = 1
        self.board = [4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0]

    def place_stone(self, hollow):
        capture = False
        hand = self.board[hollow]
        self.board[hollow] = 0

        while hand > 0:
            hollow += 1 if hollow + 1 < len(self.board) else 0
            myMancala, opponentMancala = (6, 13) if self.current_player == 1 else (13, 6)

            if hollow == opponentMancala: continue
            oppositeHollow = 12 - hollow

            if hand == 1 and self.board[hollow] == 0:
                if (self.current_player == 1 and hollow in range(0, 6)) or (self.current_player == 2 and hollow in range(7, 13)):
                    self.board[myMancala] += self.board[oppositeHollow] + 1
                    self.board[oppositeHollow] = 0
                    capture = True
                    break

            self.board[hollow] += 1
            hand -= 1

            if (self.current_player == 1 and hollow != 6) or (self.current_player == 2 and hollow != 13):
                return 'c' if capture else str()
            else:
                self.current_player = 2 if self.current_player == 1 else 1
                return 'f'

    def is_position_win(self):
        if sum(self.board[0:6]) == 0 or sum(self.board[7:-1]) == 0:
            if sum(self.board[0:6]) > sum(self.board[7:-1]):
                return self.current_player == 1
            return self.current_player == 2
        return False

    def is_position_tie(self):
        if sum(self.board[0:6]) == 0 or sum(self.board[7:-1]) == 0:
            if sum(self.board[0:6]) == sum(self.board[7:-1]):
                return True
        return False

    def is_valid_move(self, hollow):
        if self.current_player == 1 and hollow not in range(0, 6):
            return False
        elif self.current_player == 2 and hollow not in range(7, 13):
            return False
        return True

    def get_string(self):
        return ','.join(map(str, self.board))


class TreasureHuntLogic:

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

    def generate_map(self):
        for row in range(self.map_height):
            self.treasure_map.append([])
            for column in range(self.map_width):
                self.treasure_map[row].append([self.generate_treasure(row, column), 0])

    def generate_treasure(self, row, column):
        treasure_type = [
            ('None', 0, 60), ('Coin', 1, 40), ('Gem', 2, 1), ('Emerald', 4, 0.5)
        ]
        if self.get_gem_by_piece(row, column):
            return 3
        if row + 1 == self.map_height or column + 1 == self.map_width:
            treasure_type = treasure_type[:2]
        total = sum(weight for name, value, weight in treasure_type)
        r, i = uniform(0, total), 0
        for name, value, weight in treasure_type:
            if i + weight >= r:
                self.coins_hidden += 1 if value == 1 else self.coins_hidden
                if value > 1:
                    self.gems_hidden += 1
                    self.gem_locations.append(str(row) + ',' + str(column))
                if self.emerald:
                    return 2
                if value == 4 and not self.emerald:
                    self.emerald = 1
                return value
            i += weight

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


def stealth_mod_filter(stealth_mod_id):
    def f(p):
        return not p.stealth_moderator or p.id == stealth_mod_id
    return f


class RoomMixin:

    def __init__(self, *args, **kwargs):
        self.penguins_by_id = {}
        self.penguins_by_username = {}
        self.penguins_by_character_id = {}

        self.igloo = isinstance(self, PenguinIglooRoom)
        self.backyard = isinstance(self, PenguinBackyardRoom)

        self.tables = {}
        self.waddles = {}

    async def add_penguin(self, p):
        if p.room:
            await p.room.remove_penguin(p)
        self.penguins_by_id[p.id] = p
        self.penguins_by_username[p.username] = p

        if p.character:
            self.penguins_by_character_id[p.character] = p

        p.room = self

    async def remove_penguin(self, p):
        if not (p.is_vanilla_client and p.stealth_moderator):
            await self.send_xt('rp', p.id, f=lambda penguin: penguin.id != p.id)

        del self.penguins_by_id[p.id]
        del self.penguins_by_username[p.username]

        if p.character:
            del self.penguins_by_character_id[p.character]

        p.room = None
        p.frame = 1
        p.toy = None

    async def refresh(self, p):
        if p.is_vanilla_client and p.stealth_moderator:
            return await p.send_xt('grs', self.id, await self.get_string(f=stealth_mod_filter(p.id)))
        await p.send_xt('grs', self.id, await self.get_string())

    async def get_string(self, f=None):
        return '%'.join([await p.string for p in filter(f, self.penguins_by_id.values())])

    async def send_xt(self, *data, f=None):
        for penguin in filter(f, self.penguins_by_id.values()):
            await penguin.send_xt(*data)


class PenguinBackyardRoom(RoomMixin):

    def __init__(self):
        super().__init__()

        self.id = 1000
        self.name = 'Backyard'
        self.member = False
        self.max_users = 1
        self.required_item = None
        self.game = False
        self.blackhole = False
        self.spawn = False
        self.stamp_group = None

    async def add_penguin(self, p):
        if p.room:
            await p.room.remove_penguin(p)
        p.room = self

        await p.send_xt('jr', self.id, await p.string)

    async def remove_penguin(self, p):
        p.room = None
        p.frame = 1
        p.toy = None


class Room(db.Model, RoomMixin):
    __tablename__ = 'room'

    id = db.Column(db.Integer, primary_key=True)
    internal_id = db.Column(db.Integer, nullable=False, unique=True,
                            server_default=db.text("nextval('\"room_internal_id_seq\"'::regclass)"))
    name = db.Column(db.String(50), nullable=False)
    member = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    max_users = db.Column(db.SmallInteger, nullable=False, server_default=db.text("80"))
    required_item = db.Column(db.ForeignKey('item.id', ondelete='CASCADE', onupdate='CASCADE'))
    game = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    blackhole = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    spawn = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    stamp_group = db.Column(db.ForeignKey('stamp_group.id', ondelete='CASCADE', onupdate='CASCADE'))

    def __init__(self, *args, **kwargs):
        RoomMixin.__init__(self, *args, **kwargs)
        super().__init__(*args, **kwargs)

    async def add_penguin(self, p):
        await RoomMixin.add_penguin(self, p)

        if self.game:
            await p.send_xt('jg', self.id)
        elif p.is_vanilla_client and p.stealth_moderator:
            await p.send_xt('jr', self.id, await self.get_string(f=stealth_mod_filter(p.id)))
        else:
            await p.send_xt('jr', self.id, await self.get_string())
            await self.send_xt('ap', await p.string)


class PenguinIglooRoom(db.Model, RoomMixin):
    __tablename__ = 'penguin_igloo_room'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_igloo_room_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    type = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    flooring = db.Column(db.ForeignKey('flooring.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    music = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    location = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    locked = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))

    internal_id = 2000
    name = 'Igloo'
    member = False
    max_users = 80
    required_item = None
    game = False
    blackhole = False
    spawn = False
    stamp_group = None

    def __init__(self, *args, **kwargs):
        RoomMixin.__init__(self, *args, **kwargs)
        super().__init__(*args, **kwargs)

    @property
    def external_id(self):
        return self.penguin_id + PenguinIglooRoom.internal_id

    async def add_penguin(self, p):
        await RoomMixin.add_penguin(self, p)

        if p.is_vanilla_client and p.stealth_moderator:
            await p.send_xt('jr', self.external_id, await self.get_string(f=stealth_mod_filter(p.id)))
        else:
            await p.send_xt('jr', self.external_id, await self.get_string())
            await self.send_xt('ap', await p.string)

    async def remove_penguin(self, p):
        await RoomMixin.remove_penguin(self, p)

        if not self.penguins_by_id:
            del p.server.igloos_by_penguin_id[self.penguin_id]


class RoomTable(db.Model):
    __tablename__ = 'room_table'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_id = db.Column(db.ForeignKey('room.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    game = db.Column(db.String(20), nullable=False)

    GameClassMapping = {
        'four': ConnectFourLogic,
        'mancala': MancalaLogic,
        'treasure': TreasureHuntLogic
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.penguins = []
        self.room = None
        self.logic = None

    async def add(self, p):
        self.penguins.append(p)

        seat_id = len(self.penguins) - 1

        await p.send_xt("jt", self.id, seat_id + 1)
        await p.room.send_xt("ut", self.id, len(self.penguins))
        p.table = self

        return seat_id

    async def remove(self, p):
        self.penguins.remove(p)

        await p.send_xt("lt")
        await self.room.send_xt("ut", self.id, len(self.penguins))
        p.table = None

    async def reset(self):
        for penguin in self.penguins:
            penguin.table = None

        self.logic = type(self.logic)()
        self.penguins = []
        await self.room.send_xt("ut", self.id, 0)

    def get_seat_id(self, p):
        return self.penguins.index(p)

    def get_string(self):
        if len(self.penguins) == 0:
            return str()
        elif len(self.penguins) == 1:
            player_one, = self.penguins
            return "%".join([player_one.safe_name, str(), self.logic.get_string()])
        player_one, player_two = self.penguins[:2]
        if len(self.penguins) == 2:
            return "%".join([player_one.safe_name, player_two.safe_name, self.logic.get_string()])
        return "%".join([player_one.safe_name, player_two.safe_name, self.logic.get_string(), "1"])

    async def send_xt(self, *data):
        for penguin in self.penguins:
            await penguin.send_xt(*data)


class RoomWaddle(db.Model):
    __tablename__ = 'room_waddle'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_id = db.Column(db.ForeignKey('room.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    seats = db.Column(db.SmallInteger, nullable=False, server_default=db.text("2"))
    game = db.Column(db.String(20), nullable=False)

    GameClassMapping = {

    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.penguins = []

    async def add(self, p):
        if not self.penguins:
            self.penguins = [None] * self.seats

        seat_id = self.penguins.index(None)
        self.penguins[seat_id] = p
        await p.send_xt("jw", seat_id)
        await p.room.send_xt("uw", self.id, seat_id, p.safe_name)

        p.waddle = self

        if self.penguins.count(None) == 0:
            await self.reset()

    async def remove(self, p):
        seat_id = self.get_seat_id(p)
        self.penguins[seat_id] = None
        await p.room.send_xt("uw", self.id, seat_id)

        p.waddle = None

    async def reset(self):
        for seat_id, penguin in enumerate(self.penguins):
            if penguin:
                self.penguins[seat_id] = None
                await penguin.room.send_xt("uw", self.id, seat_id)

    def get_seat_id(self, p):
        return self.penguins.index(p)


class PenguinIglooRoomCollection(AbstractDataCollection):
    __model__ = PenguinIglooRoom
    __indexby__ = 'id'
    __filterby__ = 'penguin_id'


class RoomCollection(AbstractDataCollection):
    __model__ = Room
    __indexby__ = 'id'
    __filterby__ = 'id'

    @property
    def spawn_rooms(self):
        return [room for room in self.values() if room.spawn]

    async def setup_tables(self):
        async with db.transaction():
            async for table in RoomTable.query.gino.iterate():
                self[table.room_id].tables[table.id] = table
                table.room = self[table.room_id]
                table.logic = RoomTable.GameClassMapping[table.game]()

    async def setup_waddles(self):
        async with db.transaction():
            async for waddle in RoomWaddle.query.gino.iterate():
                self[waddle.room_id].waddles[waddle.id] = waddle
                waddle.room = self[waddle.room_id]
