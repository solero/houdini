from houdini.data import db, BaseCrumbsCollection
from houdini.constants import ClientType


class Room(db.Model):
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
        super().__init__(*args, **kwargs)
        self.penguins_by_id = {}
        self.penguins_by_username = {}
        self.penguins_by_character_id = {}

        self.igloo = False

        self.tables = {}
        self.waddles = {}

    async def add_penguin(self, p):
        if p.room:
            await p.room.remove_penguin(p)
        self.penguins_by_id[p.data.id] = p
        self.penguins_by_username[p.data.username] = p

        if p.data.character:
            self.penguins_by_character_id[p.data.character] = p

        p.room = self
        if p.client_type == ClientType.Vanilla:
            if p.data.stealth_moderator:
                await p.send_xt('jr', self.id, (await self.get_string(p) + await p.string))
                await p.send_xt('ap', await p.string)
            else:
                await p.send_xt('jr', self.id, await self.get_string(p))
                await self.send_xt('ap', await p.string)
        else:
            await p.send_xt('jr', self.id, await self.get_string(p))
            await self.send_xt('ap', await p.string)

        if self.game:
            await p.send_xt('jg', self.id)
        else:
            await p.send_xt('jr', self.id, await self.get_string())
            await self.send_xt('ap', await p.string)

    async def remove_penguin(self, p):
        if p.client_type == ClientType.Vanilla:
            if not p.data.stealth_moderator:
                await self.send_xt('rp', p.data.id)
        else:
            await self.send_xt('rp', p.data.id)

        del self.penguins_by_id[p.data.id]
        del self.penguins_by_username[p.data.username]

        if p.data.character:
            del self.penguins_by_character_id[p.data.character]

        p.room = None
        p.frame = 1
        p.toy = None

    async def refresh(self, p):
        if p.client_type == ClientType.Vanilla:
            return await p.send_xt('grs', self.id, (await self.get_string(p) + await p.string))
        await p.send_xt('grs', self.id, await self.get_string(p))

    async def get_string(self):
        return '%'.join([await p.string for p in self.penguins_by_id.values()])

    async def send_xt(self, *data):
        for penguin in self.penguins_by_id.values():
            await penguin.send_xt(*data)


class PenguinIglooRoom(db.Model):
    __tablename__ = 'penguin_igloo_room'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_igloo_room_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    type = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    flooring = db.Column(db.ForeignKey('flooring.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    music = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    location = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    locked = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))


class RoomTable(db.Model):
    __tablename__ = 'room_table'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_id = db.Column(db.ForeignKey('room.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                        nullable=False)
    game = db.Column(db.String(20), nullable=False)

    GameClassMapping = {

    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.penguins = []
        self.room = None

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
        await p.room.send_xt("ut", self.id, len(self.penguins))
        p.table = None

    async def reset(self):
        for penguin in self.penguins:
            penguin.table = None

        self.penguins = []
        await self.room.send_xt("ut", self.id, 0)

    def get_seat_id(self, p):
        return self.penguins.index(p)

    def get_string(self):
        if len(self.penguins) == 0:
            return str()
        elif len(self.penguins) == 1:
            player_one, = self.penguins
            return "%".join([player_one.nickname, str(), self.game.get_string()])
        player_one, player_two = self.penguins[:2]
        if len(self.penguins) == 2:
            return "%".join([player_one.nickname, player_two.nickname, self.game.get_string()])
        return "%".join([player_one.nickname, player_two.nickname, self.game.get_string(), "1"])

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
            self.penguins = [None] * self.Seats

        seat_id = self.penguins.index(None)
        self.penguins[seat_id] = p
        await p.send_xt("jw", seat_id)
        await p.room.send_xt("uw", self.id, seat_id, p.Nickname)

        p.waddle = self

        if self.penguins.count(None) == 0:
            await self.reset()

    async def remove(self, p):
        seat_id = self.get_seat_id(p)
        self.penguins[seat_id] = None
        await self.room.send_xt("uw", self.id, seat_id)

        p.waddle = None

    async def reset(self):
        for seat_id, penguin in enumerate(self.penguins):
            if penguin:
                self.penguins[seat_id] = None
                await penguin.room.send_xt("uw", self.id, seat_id)

    def get_seat_id(self, p):
        return self.penguins.index(p)


class RoomCrumbsCollection(BaseCrumbsCollection):

    def __init__(self):
        super().__init__(model=Room,
                         key='id')

    @property
    def spawn_rooms(self):
        return [room for room in self.values() if room.spawn]

    async def setup_tables(self):
        async with self._db.transaction():
            async for table in RoomTable.query.gino.iterate():
                self[table.room_id].tables[table.id] = table

    async def setup_waddles(self):
        async with self._db.transaction():
            async for waddle in RoomWaddle.query.gino.iterate():
                self[waddle.room_id].waddles[waddle.id] = waddle
