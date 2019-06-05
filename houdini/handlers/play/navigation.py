from houdini import handlers
from houdini.handlers import XTPacket

import random, time


@handlers.handler(XTPacket('j', 'js'), pre_login=True)
@handlers.allow_once()
async def handle_join_server(p, penguin_id: int, login_key: str, lang: str):
    if penguin_id != p.data.id:
        return await p.close()

    if login_key != p.login_key:
        return await p.close()

    await p.send_xt('activefeatures')
    await p.send_xt('js', int(p.data.agent_status), int(0),
                    int(p.data.moderator), int(p.data.book_modified))

    #handleGetMyPlayerPuffles()

    current_time = int(time.time())
    penguin_standard_time = current_time * 1000
    server_time_offset = 7

    await p.send_xt('lp', await p.server.penguin_string_compiler.compile(p), p.data.coins, 0, 1440,
                penguin_standard_time, p.age, 0, p.data.minutes_played, None, server_time_offset, 1, 0, 211843)

    spawn = random.choice(p.server.spawn_rooms)
    await spawn.add_penguin(p)

    await p.load()
    p.joined_world = True

    p.server.penguins_by_id[p.data.id] = p
