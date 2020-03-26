from houdini import handlers
from houdini.handlers import XTPacket


@handlers.boot
async def cards_load(server):
    server.cards = await CardCollection.get_collection()
    server.logger.info(f'Loaded {len(server.cards)} ninja cards')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_ninja_inventory(p):
    p.cards = await PenguinCardCollection.get_collection(p.id)


@handlers.handler(XTPacket('ni', 'gnr'))
async def handle_get_ninja_ranks(p):
    await p.send_xt('gnr', p.id, p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank, 0)


@handlers.handler(XTPacket('ni', 'gnl'))
async def handle_get_ninja_level(p):
    await p.send_xt('gnl', p.ninja_rank, p.ninja_progress)


@handlers.handler(XTPacket('ni', 'gfl'))
async def handle_get_fire_level(p):
    await p.send_xt('gfl', p.fire_ninja_rank, p.fire_ninja_progress)


@handlers.handler(XTPacket('ni', 'gwl'))
async def handle_get_water_level(p):
    await p.send_xt('gwl', p.water_ninja_rank, p.water_ninja_progress)


@handlers.handler(XTPacket('ni', 'gsl'))
async def handle_get_snow_level(p):
    await p.send_xt('gsl', 0, 0)


@handlers.handler(XTPacket('cd', 'gcd'))
async def handle_get_card_data(p):
    await p.send_xt('gcd', '|'.join(f'{card.card_id},{card.quantity},{card.member_quantity}'
                                    for card in p.cards.values()))
