from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.penguin import Penguin


@handlers.handler(XTPacket('ni', 'gnr'))
async def handle_get_ninja_ranks(p, penguin_id: int):
    if penguin_id in p.server.penguins_by_id:
        penguin = p.server.penguins_by_id[penguin_id]
        ninja_rank, fire_ninja_rank, water_ninja_rank = \
            penguin.ninja_rank, penguin.fire_ninja_rank, penguin.water_ninja_rank
    else:
        ninja_rank, fire_ninja_rank, water_ninja_rank = await Penguin.select(
            'ninja_rank', 'fire_ninja_rank', 'water_ninja_rank'
        ).where(Penguin.id == penguin_id).gino.first()
    await p.send_xt('gnr', p.id, ninja_rank, fire_ninja_rank, water_ninja_rank, 0)


@handlers.handler(XTPacket('ni', 'gnl'))
async def handle_get_ninja_level(p):
    await p.send_xt('gnl', p.ninja_rank, p.ninja_progress, 10)


@handlers.handler(XTPacket('ni', 'gfl'))
async def handle_get_fire_level(p):
    await p.send_xt('gfl', p.fire_ninja_rank, p.fire_ninja_progress, 5)


@handlers.handler(XTPacket('ni', 'gwl'))
async def handle_get_water_level(p):
    await p.send_xt('gwl', p.water_ninja_rank, p.water_ninja_progress, 5)


@handlers.handler(XTPacket('ni', 'gsl'))
async def handle_get_snow_level(p):
    await p.send_xt('gsl', 0, 0, 24)


@handlers.handler(XTPacket('ni', 'gcd'))
async def handle_get_card_data(p):
    await p.send_xt('gcd', '|'.join(f'{card.card_id},{card.quantity+card.member_quantity}'
                                    for card in p.cards.values()))
