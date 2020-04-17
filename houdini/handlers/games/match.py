import asyncio
import operator
from dataclasses import dataclass

from houdini import handlers
from houdini.data.room import RoomWaddle
from houdini.handlers import XTPacket
from houdini.handlers.games.ninja.card import SenseiLogic, CardJitsuLogic, CardJitsuMatLogic
from houdini.handlers.games.ninja.fire import FireSenseiLogic, CardJitsuFireLogic
from houdini.handlers.games.ninja.water import WaterSenseiLogic, CardJitsuWaterLogic
from houdini.penguin import Penguin


@dataclass
class MatchMaker:
    penguin: Penguin
    tick: int


class MatchMaking:
    SenseiRoom = 951
    SenseiFireRoom = 953
    SenseiWaterRoom = 954

    def __init__(self, server, on_tick, on_matched, match_by, max_players=2, match_every=10):
        self.server = server
        self._on_tick = on_tick
        self._on_matched = on_matched

        self._match_by = match_by
        self._max_players = max_players
        self._match_every = match_every

        self._penguins = []
        self._matched_penguins = {}

    async def start(self):
        while True:
            await self.tick()
            await asyncio.sleep(1)

    async def tick(self):
        for i in range(0, len(self._penguins) - len(self._penguins) % 2, self._max_players):
            matched = self._penguins[i:i+self._max_players]
            if any(mm.tick == 0 for mm in matched):
                matched_penguins = [mm.penguin for mm in matched]
                self._matched_penguins.update({
                    mm.penguin.id: matched_penguins
                    for mm in matched})
                self._penguins = [mm for mm in self._penguins if mm not in matched]

                await self._on_matched(matched)
            else:
                await self._on_tick(matched)
                for mm in matched:
                    mm.tick -= 1

    def add_penguin(self, p):
        mm = MatchMaker(penguin=p, tick=self._match_every)
        self._penguins.append(mm)
        self._penguins.sort(key=operator.attrgetter('penguin.' + self._match_by))

    def remove_penguin(self, p):
        self._penguins = [mm for mm in self._penguins if mm.penguin != p]
        if p.id in self._matched_penguins:
            matched = self._matched_penguins[p.id]
            matched.remove(p)

            del self._matched_penguins[p.id]
            self._penguins.sort(key=operator.attrgetter('penguin.' + self._match_by))

    def matched_with(self, p):
        if p.id in self._matched_penguins:
            return self._matched_penguins[p.id]

    def has_matched(self, p):
        return p.id in self._matched_penguins


async def card_tick(matched):
    nicknames = [mm.penguin.safe_name for mm in matched]
    for mm in matched:
        await mm.penguin.send_xt('tmm', mm.tick, *nicknames)


async def card_color_tick(matched):
    nicknames = [f'{mm.penguin.safe_name}|{mm.penguin.color}' for mm in matched]
    for mm in matched:
        await mm.penguin.send_xt('tmm', len(matched), mm.tick, *nicknames)


def card_match(waddle_game):
    async def match(matched):
        nicknames = [f'{mm.penguin.safe_name}|{mm.penguin.color}' for mm in matched]
        host = matched[0].penguin

        waddle_room = host.server.rooms[waddle_game.room_id]
        rw = RoomWaddle(id=host.id, room_id=waddle_room.id, seats=len(matched), game=waddle_game, temporary=True)
        rw.room = waddle_room
        rw.logic = waddle_game
        waddle_room.waddles[rw.id] = rw

        for mm in matched:
            await mm.penguin.send_xt('scard', waddle_room.id, rw.id, len(matched), mm.tick, *nicknames)
    return match


card_matched = card_match(CardJitsuLogic)
card_fire_matched = card_match(CardJitsuFireLogic)
card_water_matched = card_match(CardJitsuWaterLogic)


@handlers.boot
async def match_load(server):
    server.match_making = MatchMaking(server, card_tick, card_matched, match_by='ninja_rank')
    server.fire_match_making = MatchMaking(server, card_color_tick, card_fire_matched,
                                           match_by='fire_ninja_rank', max_players=4)
    server.water_match_making = MatchMaking(server, card_color_tick, card_water_matched,
                                            match_by='water_ninja_rank', max_players=4)

    asyncio.create_task(server.match_making.start())
    asyncio.create_task(server.fire_match_making.start())
    asyncio.create_task(server.water_match_making.start())


@handlers.handler(XTPacket('jmm', ext='z'))
@handlers.player_in_room(MatchMaking.SenseiRoom)
async def handle_join_match_making(p):
    p.server.match_making.add_penguin(p)
    await p.send_xt('jmm', p.safe_name)


@handlers.handler(XTPacket('jmm', ext='z'))
@handlers.player_in_room(MatchMaking.SenseiFireRoom)
async def handle_join_fire_match_making(p):
    p.server.fire_match_making.add_penguin(p)
    await p.send_xt('jmm', p.safe_name)


@handlers.handler(XTPacket('jmm', ext='z'))
@handlers.player_in_room(MatchMaking.SenseiWaterRoom)
async def handle_join_water_match_making(p):
    p.server.water_match_making.add_penguin(p)
    await p.send_xt('jmm', p.safe_name)


@handlers.handler(XTPacket('gwcj', ext='z'))
async def handle_get_card_jitsu_mat(p, waddle_id: int):
    waddle_id = max(200, min(300, waddle_id))
    if p.room.igloo and waddle_id not in p.room.waddles:
        rw = RoomWaddle(id=waddle_id, room_id=p.room.id, seats=2, game='card', temporary=True)
        rw.penguins = [None]*2
        rw.room = p.room
        rw.logic = CardJitsuMatLogic
        p.room.waddles[rw.id] = rw


@handlers.handler(XTPacket('jsen', ext='z'))
@handlers.player_in_room(MatchMaking.SenseiRoom)
async def handle_join_sensei_match(p):
    waddle_room = p.server.rooms[SenseiLogic.room_id]
    rw = RoomWaddle(id=p.id, room_id=waddle_room.id, seats=1, game='sensei', temporary=True)
    rw.penguins = [None]
    rw.room = waddle_room
    rw.logic = SenseiLogic
    waddle_room.waddles[rw.id] = rw

    await p.send_xt('scard', waddle_room.id, rw.id, 1, 0, f'{p.safe_name}|{p.color}')


@handlers.handler(XTPacket('jsen', ext='z'))
@handlers.player_in_room(MatchMaking.SenseiFireRoom)
async def handle_join_fire_sensei_match(p):
    waddle_room = p.server.rooms[FireSenseiLogic.room_id]
    rw = RoomWaddle(id=p.id, room_id=waddle_room.id, seats=1, game='firesensei', temporary=True)
    rw.penguins = [None]
    rw.room = waddle_room
    rw.logic = FireSenseiLogic
    waddle_room.waddles[rw.id] = rw

    await p.send_xt('scard', waddle_room.id, rw.id, 1, 0, f'{p.safe_name}|{p.color}')


@handlers.handler(XTPacket('jsen', ext='z'))
@handlers.player_in_room(MatchMaking.SenseiWaterRoom)
async def handle_join_water_sensei_match(p):
    waddle_room = p.server.rooms[WaterSenseiLogic.room_id]
    rw = RoomWaddle(id=p.id, room_id=waddle_room.id, seats=1, game='watersensei', temporary=True)
    rw.penguins = [None]
    rw.room = waddle_room
    rw.logic = WaterSenseiLogic
    waddle_room.waddles[rw.id] = rw

    await p.send_xt('scard', waddle_room.id, rw.id, 1, 0, f'{p.safe_name}|{p.color}')


@handlers.handler(XTPacket('lmm', ext='z'))
async def handle_leave_match_making(p):
    p.server.match_making.remove_penguin(p)
    p.server.water_match_making.remove_penguin(p)
    p.server.fire_match_making.remove_penguin(p)


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_match_making(p):
    p.server.match_making.remove_penguin(p)
    p.server.water_match_making.remove_penguin(p)
    p.server.fire_match_making.remove_penguin(p)
