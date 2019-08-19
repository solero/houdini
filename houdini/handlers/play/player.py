from houdini import handlers, ClientType
from houdini.handlers import XTPacket
from houdini.data.penguin import Penguin

from aiocache import cached


def get_player_string_key(_, p, player_id):
    return 'player.{}'.format(player_id)


def get_mascot_string_key(_, p, mascot_id):
    return 'mascot.{}'.format(mascot_id)


@cached(alias='default', key_builder=get_player_string_key)
async def get_player_string(p, penguin_id):
    if penguin_id in p.server.penguins_by_id:
        return await p.server.penguins_by_id[penguin_id].string
    else:
        player_data = await Penguin.get(penguin_id)
        string = await p.server.anonymous_penguin_string_compiler.compile(player_data)
        return string


@cached(alias='default', key_builder=get_mascot_string_key)
async def get_mascot_string(p, mascot_id):
    if mascot_id in p.server.penguins_by_character_id:
        return await p.server.penguins_by_character_id[mascot_id].string
    else:
        player_data = await Penguin.query.where(Penguin.character == mascot_id).gino.first()
        string = await p.server.anonymous_penguin_string_compiler.compile(player_data)
        return string


@handlers.handler(XTPacket('u', 'h'))
@handlers.cooldown(59)
async def handle_heartbeat(p):
    await p.send_xt('h')


@handlers.handler(XTPacket('u', 'gp'))
@handlers.cooldown(1)
async def handle_get_player(p, penguin_id: int):
    await p.send_xt('gp', await get_player_string(p, penguin_id))


@handlers.handler(XTPacket('u', 'gmo'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_mascot(p, mascot_id: int):
    await p.send_xt('gmo', await get_mascot_string(p, mascot_id))


@handlers.handler(XTPacket('u', 'pbi'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_by_id(p, penguin_id: int):
    await p.send_xt('pbi', penguin_id)


@handlers.handler(XTPacket('u', 'pbs'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_by_swid(p, penguin_id: int):
    if penguin_id in p.server.penguins_by_id:
        nickname = p.server.penguins_by_id[penguin_id].data.nickname
    else:
        nickname = await Penguin.select('nickname').where(Penguin.id == penguin_id).gino.scalar()
    await p.send_xt('pbs', penguin_id, penguin_id, nickname)


@handlers.handler(XTPacket('u', 'pbn'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_by_name(p, player_name: str):
    player_name = player_name.lower()
    if player_name in p.server.penguins_by_username:
        player = p.server.penguins_by_username[player_name]
        await p.send_xt('pbn', player.data.id, player.data.id, player.data.nickname)
    else:
        player_id, nickname = await Penguin.select('id', 'nickname').where(
            Penguin.username == player_name).gino.first()
        if player_id is not None:
            await p.send_xt('pbn', player_id, player_id, nickname)
        else:
            await p.send_xt('pbn')


@handlers.handler(XTPacket('u', 'pbsms'), client=ClientType.Vanilla)
async def handle_pbsm_start(p):
    await p.send_xt('pbsms')


@handlers.handler(XTPacket('u', 'pbsm'), client=ClientType.Vanilla)
async def handle_get_player_ids(p, ids: str):
    await p.send_xt('pbsm', ids)


@handlers.handler(XTPacket('u', 'pbsmf'), client=ClientType.Vanilla)
async def handle_pbsm_finish(p):
    await p.send_xt('pbsmf')


@handlers.handler(XTPacket('u', 'sp'))
async def handle_set_player_position(p, x: int, y: int):
    p.x, p.y = x, y
    p.frame = 1
    p.toy = None
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
