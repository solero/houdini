from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.room import Room

import random
import time


@handlers.handler(XTPacket('j', 'js'), pre_login=True)
@handlers.allow_once
async def handle_join_server(p, penguin_id: int, login_key: str):
    if penguin_id != p.data.id:
        return await p.close()

    if login_key != p.login_key:
        return await p.close()

    await p.send_xt('activefeatures')
    await p.send_xt('js', int(p.data.agent_status), int(0),
                    int(p.data.moderator), int(p.data.book_modified))

    current_time = int(time.time())
    penguin_standard_time = current_time * 1000
    server_time_offset = 7

    await p.send_xt('lp', await p.string, p.data.coins, int(p.data.safe_chat), 1440,
                    penguin_standard_time, p.data.age, 0, p.data.minutes_played,
                    "membership_days", server_time_offset, int(p.data.opened_playercard),
                    p.data.map_category, p.data.status_field)

    spawn = random.choice(p.server.spawn_rooms)
    await p.join_room(spawn)

    await p.data.load_inventories()

    p.server.penguins_by_id[p.data.id] = p
    p.server.penguins_by_username[p.data.username] = p

    if p.data.character is not None:
        p.server.penguins_by_character_id[p.data.character] = p

    p.joined_world = True

    await p.server.redis.hincrby('population', p.server.server_config['Id'], 1)


@handlers.handler(XTPacket('j', 'jr'))
@handlers.cooldown(1)
async def handle_join_room(p, room: Room, x: int, y: int):
    p.x, p.y = x, y
    await p.join_room(room)
