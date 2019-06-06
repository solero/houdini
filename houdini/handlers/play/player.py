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


