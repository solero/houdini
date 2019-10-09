import config

from houdini import handlers
from houdini.handlers import XMLPacket
from houdini.converters import VersionChkConverter
from houdini.constants import ClientType

from houdini.data.buddy import BuddyList


@handlers.handler(XMLPacket('verChk'))
@handlers.allow_once
async def handle_version_check(p, version: VersionChkConverter):
    if config.client['MultiClientSupport']:
        if config.client['LegacyVersionChk'] == version:
            p.client_type = ClientType.Legacy
        elif config.client['VanillaVersionChk'] == version:
            p.client_type = ClientType.Vanilla
    elif config.client['DefaultVersionChk'] == version:
        p.client_type = config.client['DefaultClientType']

    if p.client_type is None:
        await p.send_xml({'body': {'action': 'apiKO', 'r': '0'}})
        await p.close()
    else:
        await p.send_xml({'body': {'action': 'apiOK', 'r': '0'}})


@handlers.handler(XMLPacket('rndK'))
@handlers.allow_once
async def handle_random_key(p, data):
    await p.send_xml({'body': {'action': 'rndK', 'r': '-1'}, 'k': config.client['AuthStaticKey']})


async def get_server_presence(p, pid):
    buddy_worlds = []
    world_populations = []

    for server_name, server_config in config.servers.items():
        if server_config['World']:
            server_population = await p.server.redis.hget('houdini.population', server_config['Id'])
            server_population = (7 if int(server_population) == server_config['Capacity']
                                 else int(server_population) // (server_config['Capacity'] // 6)) \
                if server_population else 0

            world_populations.append('{},{}'.format(server_config['Id'], server_population))

            server_key = f'houdini.players.{server_config["Id"]}'
            if await p.server.redis.scard(server_key):
                async with p.server.db.transaction():
                    buddies = BuddyList.select('buddy_id').where(BuddyList.penguin_id == pid).gino.iterate()
                    tr = p.server.redis.multi_exec()
                    async for buddy_id, in buddies:
                        tr.sismember(server_key, buddy_id)
                    online_buddies = await tr.execute()
                    if any(online_buddies):
                        buddy_worlds.append(server_config['Id'])

    return '|'.join(world_populations), '|'.join(buddy_worlds)
