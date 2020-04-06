from houdini.data import AbstractDataCollection, db


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
        if len(self.penguins_by_id) >= self.max_users and not p.moderator:
            return await p.send_error(210)

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
        self.penguin = None

    async def add_penguin(self, p):
        self.penguin = p

        if p.room:
            await p.room.remove_penguin(p)
        p.room = self

        await p.send_xt('jr', self.id, await p.string)

    async def remove_penguin(self, p):
        p.room = None
        p.frame = 1
        p.toy = None

    async def send_xt(self, *data, f=None):
        await self.penguin.send_xt(*data)


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

        self.blackhole_penguins = {}

    async def add_penguin(self, p):
        if self.blackhole and p.is_vanilla_client:
            self.blackhole_penguins[p.id] = p.room
            p.room = self
            return await p.send_xt('jnbhg', self.id)

        await RoomMixin.add_penguin(self, p)

        if self.game:
            await p.send_xt('jg', self.id)
        elif p.is_vanilla_client and p.stealth_moderator:
            await p.send_xt('jr', self.id, await self.get_string(f=stealth_mod_filter(p.id)))
        else:
            await p.send_xt('jr', self.id, await self.get_string())
            await self.send_xt('ap', await p.string)

    async def remove_penguin(self, p):
        await RoomMixin.remove_penguin(self, p)

    async def leave_blackhole(self, p):
        if p.id in self.blackhole_penguins and p.is_vanilla_client:
            p.room = self.blackhole_penguins.pop(p.id)


class PenguinIglooRoom(db.Model, RoomMixin):
    __tablename__ = 'penguin_igloo_room'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.text("nextval('\"penguin_igloo_room_id_seq\"'::regclass)"))
    penguin_id = db.Column(db.ForeignKey('penguin.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    type = db.Column(db.ForeignKey('igloo.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    flooring = db.Column(db.ForeignKey('flooring.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    music = db.Column(db.SmallInteger, nullable=False, server_default=db.text("0"))
    location = db.Column(db.ForeignKey('location.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    locked = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))
    competition = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.penguins = []
        self.room = None
        self.logic = None

    async def add_penguin(self, p):
        self.penguins.append(p)

        seat_id = len(self.penguins) - 1

        await p.send_xt('jt', self.id, seat_id + 1)
        await p.room.send_xt('ut', self.id, len(self.penguins))
        p.table = self

        return seat_id

    async def remove_penguin(self, p):
        seat_id = self.get_seat_id(p)
        is_player = seat_id < 2
        game_ready = len(self.penguins) > 1
        if is_player and game_ready:
            await self.send_xt('cz', p.safe_name)
            await self.reset()
        else:
            self.penguins.remove(p)

            await p.send_xt('lt')
            await self.room.send_xt('ut', self.id, len(self.penguins))
            p.table = None

    async def reset(self):
        for penguin in self.penguins:
            penguin.table = None

        self.logic = type(self.logic)()
        self.penguins = []
        await self.room.send_xt('ut', self.id, 0)

    def get_seat_id(self, p):
        return self.penguins.index(p)

    def get_string(self):
        if len(self.penguins) == 0:
            return str()
        elif len(self.penguins) == 1:
            player_one, = self.penguins
            return '%'.join([player_one.safe_name, str(), self.logic.get_string()])
        player_one, player_two = self.penguins[:2]
        if len(self.penguins) == 2:
            return '%'.join([player_one.safe_name, player_two.safe_name, self.logic.get_string()])
        return '%'.join([player_one.safe_name, player_two.safe_name, self.logic.get_string(), '1'])

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

    def __init__(self, *args, **kwargs):
        self.temporary = kwargs.pop('temporary', False)
        self.penguins = []
        self.logic = None
        self.room = None

        super().__init__(*args, **kwargs)

    async def add_penguin(self, p):
        seat_id = self.penguins.index(None)
        self.penguins[seat_id] = p
        await p.send_xt('jw', seat_id)
        await p.room.send_xt('uw', self.id, seat_id, p.safe_name)

        p.waddle = self

        if self.penguins.count(None) == 0:
            game_instance = self.logic(self)

            await game_instance.start()

            await self.reset()

            if self.temporary:
                del self.room.waddles[self.id]

    async def remove_penguin(self, p):
        seat_id = self.get_seat_id(p)
        self.penguins[seat_id] = None
        await p.room.send_xt('uw', self.id, seat_id)

        p.waddle = None

        if self.temporary and self.penguins.count(None) == self.seats:
            del self.room.waddles[self.id]

    async def reset(self):
        for seat_id, penguin in enumerate(self.penguins):
            if penguin:
                self.penguins[seat_id] = None
                await penguin.room.send_xt('uw', self.id, seat_id)

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
