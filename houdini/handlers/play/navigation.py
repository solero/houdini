from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.room import Room
from houdini.data.penguin import Login
from houdini.data.penguin import Penguin
from houdini.data.room import PenguinIglooRoom, PenguinBackyardRoom
from houdini.constants import ClientType

import random
import time
from datetime import datetime


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
    server_time_offset = 7

    if p.timer_active:
        minutes_until_timer_end = datetime.combine(datetime.today(), p.timer_end) - datetime.now()
        minutes_until_timer_end = minutes_until_timer_end.total_seconds() // 60

        minutes_played_today = await p.minutes_played_today
        minutes_left_today = (p.timer_total.total_seconds() // 60) - minutes_played_today
        p.egg_timer_minutes = int(min(minutes_until_timer_end, minutes_left_today))
    else:
        p.egg_timer_minutes = 24 * 60

    await p.send_xt('lp', await p.string, p.coins, int(p.safe_chat), p.egg_timer_minutes,
                    penguin_standard_time, p.age, 0, p.minutes_played,
                    "membership_days", server_time_offset, int(p.opened_playercard),
                    p.map_category, p.status_field)

    spawn = random.choice(p.server.spawn_rooms)
    await p.join_room(spawn)

    p.server.penguins_by_id[p.id] = p
    p.server.penguins_by_username[p.username] = p

    if p.character is not None:
        p.server.penguins_by_character_id[p.character] = p

    p.login_timestamp = datetime.now()
    p.joined_world = True

    server_key = f'houdini.players.{p.server.server_config["Id"]}'
    await p.server.redis.sadd(server_key, p.data.id)
    await p.server.redis.hincrby('houdini.population', p.server.server_config['Id'], 1)


@handlers.handler(XTPacket('j', 'jr'))
@handlers.cooldown(1)
async def handle_join_room(p, room: Room, x: int, y: int):
    p.x, p.y = x, y
    await p.join_room(room)


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
@handlers.cooldown(1)
async def handle_join_player_room(p, penguin_id: int, room_type: str):
    if room_type == 'backyard' and p.room.igloo and p.room.penguin_id == p.id:
        backyard = PenguinBackyardRoom()
        await p.send_xt('jp', backyard.id, backyard.id, room_type)
        await p.join_room(backyard)
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
    await p.room.remove_penguin(p)

    minutes_played = (datetime.now() - p.login_timestamp).total_seconds() / 60.0
    await Login.create(penguin_id=p.id,
                       date=p.login_timestamp,
                       ip_address=p.peer_name[0],
                       minutes_played=minutes_played)

    await p.update(minutes_played=p.minutes_played + minutes_played).apply()

    del p.server.penguins_by_id[p.id]
    del p.server.penguins_by_username[p.username]

    server_key = f'houdini.players.{p.server.server_config["Id"]}'
    await p.server.redis.srem(server_key, p.data.id)
    await p.server.redis.hincrby('houdini.population', p.server.server_config['Id'], -1)
