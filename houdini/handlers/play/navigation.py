import hashlib
import random
import time
from datetime import date, datetime

import pytz

from houdini import handlers
from houdini.constants import ClientType, StatusField
from houdini.data import db
from houdini.data.penguin import Login, Penguin
from houdini.data.room import PenguinBackyardRoom, PenguinIglooRoom, Room, RoomCollection, RoomTable, RoomWaddle
from houdini.handlers import XTPacket
from houdini.handlers.games.four import ConnectFourLogic
from houdini.handlers.games.mancala import MancalaLogic
from houdini.handlers.games.ninja.card import CardJitsuLogic, CardJitsuMatLogic, SenseiLogic
from houdini.handlers.games.ninja.fire import CardJitsuFireLogic, FireMatLogic, FireSenseiLogic
from houdini.handlers.games.ninja.water import CardJitsuWaterLogic, WaterSenseiLogic
from houdini.handlers.games.sled import SledRacingLogic
from houdini.handlers.games.treasure import TreasureHuntLogic

TableLogicMapping = {
    'four': ConnectFourLogic,
    'mancala': MancalaLogic,
    'treasure': TreasureHuntLogic
}


WaddleLogicMapping = {
    'sled': SledRacingLogic,

    'card': CardJitsuMatLogic,
    'match': CardJitsuLogic,
    'sensei': SenseiLogic,

    'water': CardJitsuWaterLogic,
    'watersensei': WaterSenseiLogic,

    'fire': FireMatLogic,
    'firematch': CardJitsuFireLogic,
    'firesensei': FireSenseiLogic
}


async def setup_tables(room_collection):
    async with db.transaction():
        async for table in RoomTable.query.gino.iterate():
            room_collection[table.room_id].tables[table.id] = table
            table.room = room_collection[table.room_id]
            table.logic = TableLogicMapping[table.game]()


async def setup_waddles(room_collection):
    async with db.transaction():
        async for waddle in RoomWaddle.query.gino.iterate():
            room_collection[waddle.room_id].waddles[waddle.id] = waddle
            waddle.room = room_collection[waddle.room_id]
            waddle.logic = WaddleLogicMapping[waddle.game]
            waddle.penguins = [None] * waddle.seats


@handlers.boot
async def rooms_load(server):
    server.rooms = await RoomCollection.get_collection()
    await setup_tables(server.rooms)
    await setup_waddles(server.rooms)
    server.logger.info(f'Loaded {len(server.rooms)} rooms ({len(server.rooms.spawn_rooms)} spawn)')


@handlers.handler(XTPacket('j', 'js'), pre_login=True)
@handlers.allow_once
async def handle_join_server(p, penguin_id: int, login_key: str):
    if penguin_id != p.id:
        return await p.close()

    if login_key != p.login_key:
        return await p.close()

    await p.send_xt('activefeatures')

    moderator_status = 3 if p.character else 2 if p.stealth_moderator else 1 if p.moderator else 0

    await p.send_xt('js', int(p.agent_status), int(0),
                    moderator_status, int(p.book_modified))

    current_time = int(time.time())
    penguin_standard_time = current_time * 1000

    pst = pytz.timezone(p.server.config.timezone)
    dt = datetime.fromtimestamp(current_time, pst)
    server_time_offset = abs(int(dt.strftime('%z')) // 100)

    if p.timer_active:
        minutes_until_timer_end = datetime.combine(datetime.today(), p.timer_end) - datetime.now()
        minutes_until_timer_end = minutes_until_timer_end.total_seconds() // 60

        minutes_played_today = await get_minutes_played_today(p)
        minutes_left_today = (p.timer_total.total_seconds() // 60) - minutes_played_today
        p.egg_timer_minutes = int(min(minutes_until_timer_end, minutes_left_today))
    else:
        p.egg_timer_minutes = 24 * 60

    await p.send_xt('lp', await p.string, p.coins, int(p.safe_chat), p.egg_timer_minutes,
                    penguin_standard_time, p.age, 0, p.minutes_played,
                    p.membership_days_remain, server_time_offset, int(p.opened_playercard),
                    p.map_category, p.status_field)

    spawn = random.choice(p.server.rooms.spawn_rooms)
    await p.join_room(spawn)

    p.server.penguins_by_id[p.id] = p
    p.server.penguins_by_username[p.username] = p

    if p.character is not None:
        p.server.penguins_by_character_id[p.character] = p

    p.login_timestamp = datetime.now()
    p.joined_world = True

    server_key = f'houdini.players.{p.server.config.id}'
    await p.server.redis.sadd(server_key, p.id)
    await p.server.redis.hset('houdini.population', p.server.config.id, len(p.server.penguins_by_id))


async def room_cooling(p):
    return await p.send_error(210)


@handlers.handler(XTPacket('j', 'jr'))
@handlers.cooldown(0.5, callback=room_cooling)
async def handle_join_room(p, room: Room, x: int, y: int):
    if p.is_legacy_client and room.tables:
        await p.send_xt('jr', room.id)
    p.x, p.y = x, y
    await p.join_room(room)


async def get_minutes_played_today(p):
    yesterday = datetime.combine(date.today(), datetime.min.time())
    minutes_played_today = await db.select([db.func.sum(Login.minutes_played)]) \
        .where((Login.penguin_id == p.id) & (Login.date > yesterday)).gino.scalar()
    return minutes_played_today or 0


async def create_temporary_room(p, penguin_id):
    igloo = None
    if penguin_id in p.server.penguins_by_id:
        igloo_owner = p.server.penguins_by_id[penguin_id]
        igloo = igloo_owner.igloo_rooms[igloo_owner.igloo]
        p.server.igloos_by_penguin_id[penguin_id] = igloo
    elif penguin_id not in p.server.igloos_by_penguin_id:
        igloo = await PenguinIglooRoom.load(parent=Penguin.on(Penguin.igloo == PenguinIglooRoom.id)) \
            .where(PenguinIglooRoom.penguin_id == penguin_id).gino.first()
        if igloo is not None:
            p.server.igloos_by_penguin_id[penguin_id] = igloo
    return igloo


@handlers.handler(XTPacket('j', 'jp'), client=ClientType.Vanilla)
@handlers.cooldown(1, callback=room_cooling)
async def handle_join_player_room(p, penguin_id: int, room_type: str):
    if room_type == 'backyard' and p.room.igloo and p.room.penguin_id == p.id:
        backyard = PenguinBackyardRoom()
        await p.send_xt('jp', backyard.id, backyard.id, room_type)
        await p.join_room(backyard)
        await p.status_field_set(StatusField.VisitBackyardFirstTime)
    elif room_type == 'igloo':
        igloo = await create_temporary_room(p, penguin_id)
        await p.send_xt('jp', igloo.external_id, igloo.external_id, room_type)

        await p.join_room(igloo)


@handlers.handler(XTPacket('j', 'jp'), client=ClientType.Legacy)
@handlers.cooldown(1)
async def handle_join_player_room_legacy(p, penguin_id: int):
    penguin_id -= 1000
    igloo = await create_temporary_room(p, penguin_id)
    await p.join_room(igloo)


@handlers.handler(XTPacket('j', 'grs'))
async def handle_refresh_room(p):
    await p.room.refresh(p)


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_room(p):
    if p.room.blackhole:
        await p.room.leave_blackhole(p)
    await p.room.remove_penguin(p)

    minutes_played = (datetime.now() - p.login_timestamp).total_seconds() / 60.0

    ip = p.peer_name[0] + p.server.config.auth_key
    hashed_ip = hashlib.sha3_512(ip.encode()).hexdigest()
    await Login.create(penguin_id=p.id,
                       date=p.login_timestamp,
                       ip_hash=hashed_ip,
                       minutes_played=minutes_played)

    await p.update(minutes_played=p.minutes_played + minutes_played).apply()

    del p.server.penguins_by_id[p.id]
    del p.server.penguins_by_username[p.username]

    server_key = f'houdini.players.{p.server.config.id}'
    await p.server.redis.srem(server_key, p.id)
    await p.server.redis.hset('houdini.population', p.server.config.id, len(p.server.penguins_by_id))
