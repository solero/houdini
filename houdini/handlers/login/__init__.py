from houdini import handlers
from houdini.handlers import XMLPacket
from houdini.converters import VersionChkConverter
from houdini.constants import ClientType

from houdini.data.buddy import BuddyList


@handlers.handler(XMLPacket('verChk'))
@handlers.allow_once
async def handle_version_check(p, version: VersionChkConverter):
    if not p.server.config.single_client_mode:
        if p.server.config.legacy_version == version:
            p.client_type = ClientType.Legacy
        elif p.server.config.vanilla_version == version:
            p.client_type = ClientType.Vanilla
    elif p.server.config.default_version == version:
        p.client_type = p.server.config.default_version

    if p.client_type is None:
        await p.send_xml({'body': {'action': 'apiKO', 'r': '0'}})
        await p.close()
    else:
        await p.send_xml({'body': {'action': 'apiOK', 'r': '0'}})


@handlers.handler(XMLPacket('rndK'))
@handlers.allow_once
async def handle_random_key(p, _):
    await p.send_xml({'body': {'action': 'rndK', 'r': '-1'}, 'k': p.server.config.auth_key})


async def get_server_presence(p, pdata):
    buddy_worlds = []
    world_populations = []

    pops = await p.server.redis.hgetall('houdini.population')
    for server_id, server_population in pops.items():
        server_population = 7 if int(server_population) == p.server.config.capacity \
            else int(server_population) // (p.server.config.capacity // 6)
        server_population = server_population if not pdata.moderator else 0

        world_populations.append(f'{int(server_id)},{int(server_population)}')

        server_key = f'houdini.players.{int(server_id)}'
        if await p.server.redis.scard(server_key):
            async with p.server.db.transaction():
                buddies = BuddyList.select('buddy_id').where(BuddyList.penguin_id == pdata.id).gino.iterate()
                tr = p.server.redis.multi_exec()
                async for buddy_id, in buddies:
                    tr.sismember(server_key, buddy_id)
                online_buddies = await tr.execute()
                if any(online_buddies):
                    buddy_worlds.append(str(int(server_id)))

    return '|'.join(world_populations), '|'.join(buddy_worlds)
