from houdini import handlers
from houdini.handlers import XTPacket


async def get_player_info_by_id(p, id):
    if id in p.server.penguins_by_id:
        player = p.server.penguins_by_id[id]
        player_tuple = (player.data.nickname, player.data.id, player.data.nickname)
    else:
        player_tuple = await p.data.select('nickname', 'id', 'nickname').where(p.data.id == id).gino.first()

    if player_tuple is not None:
        player_data = [str(player_detail) for player_detail in player_tuple]
        return "|".join(player_data)

    return str()


@handlers.handler(XTPacket('u', 'h'))
@handlers.cooldown(59)
async def handle_heartbeat(p):
    await p.send_xt('h')


@handlers.handler(XTPacket('u', 'pbi'))
async def handle_get_player_info_by_id(p, penguin_id: int):
    await p.send_xt('pbi', await get_player_info_by_id(p, penguin_id))


@handlers.handler(XTPacket('u', 'sp'))
async def handle_set_player_position(p, x: int, y: int):
    p.x, p.y = x, y
    p.frame = 1
    await p.room.send_xt('sp', p.data.id, x, y)


@handlers.handler(XTPacket('u', 'sf'))
@handlers.cooldown(.5)
async def handle_set_player_frame(p, frame: int):
    p.frame = frame
    await p.room.send_xt('sf', p.data.id, frame)


@handlers.handler(XTPacket('u', 'sb'))
@handlers.cooldown(1)
async def handle_send_throw_ball(p, x: int, y: int):
    await p.room.send_xt('sb', p.data.id, x, y)


@handlers.handler(XTPacket('u', 'se'))
@handlers.cooldown(1)
async def handle_send_emote(p, emote: int):
    await p.room.send_xt('se', p.data.id, emote)


@handlers.handler(XTPacket('u', 'sa'))
@handlers.cooldown(1)
async def handle_send_action(p, action: int):
    await p.room.send_xt('sa', p.data.id, action)


@handlers.handler(XTPacket('u', 'followpath'))
@handlers.cooldown(1)
async def handle_follow_path(p, path: int):
    await p.room.send_xt('followpath', p.data.id, path)
