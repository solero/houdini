from houdini import handlers
from houdini.handlers import XTPacket

import random


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

    spawn = random.choice(p.server.spawn_rooms)
    await spawn.add_penguin(p)

    await p.data.load_inventories()
    p.joined_world = True
