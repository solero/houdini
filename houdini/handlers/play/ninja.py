from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.penguin import Penguin
from houdini.handlers.games.ninja.card import get_threshold_for_rank, get_exp_difference_to_next_rank
from houdini.handlers.games.ninja.fire import get_fire_rank_threshold
from houdini.handlers.games.ninja.water import get_water_rank_threshold

# rank doesn't need to be known, but requiring it since it is always known and is simpler/faster to compute
def get_percentage_to_next_belt(xp: int, rank: int) -> int:
    return int(((xp - get_threshold_for_rank(rank)) / get_exp_difference_to_next_rank(rank)) * 100)

def get_percentage_to_next_fire_item(xp: int, rank: int) -> int:
    if rank >= 4:
        return 0
    cur_threshold = get_fire_rank_threshold(rank)
    return int((xp - cur_threshold) / (get_fire_rank_threshold(rank + 1) - cur_threshold) * 100)

def get_percentage_to_next_water_item(exp: float, rank: int) -> int:
    """Get the percentage to the next water item"""
    if rank >= 4:
        return 0
    cur_threshold = get_water_rank_threshold(rank)
    next_threshold = get_water_rank_threshold(rank + 1)
    return int((exp - cur_threshold) / (next_threshold - cur_threshold) * 100)

@handlers.handler(XTPacket('ni', 'gnr'))
@handlers.cooldown(2)
async def handle_get_ninja_ranks(p, penguin_id: int):
    ninja_rank, fire_ninja_rank, water_ninja_rank, snow_ninja_rank = await Penguin.select(
        'ninja_rank', 'fire_ninja_rank', 'water_ninja_rank', 'snow_ninja_rank'
    ).where(Penguin.id == penguin_id).gino.first()
    await p.send_xt('gnr', p.id, ninja_rank, fire_ninja_rank, water_ninja_rank, snow_ninja_rank)

@handlers.handler(XTPacket('ni', 'gnl'))
async def handle_get_ninja_level(p):
    await p.send_xt('gnl', p.ninja_rank, get_percentage_to_next_belt(p.ninja_progress, p.ninja_rank), 10)


@handlers.handler(XTPacket('ni', 'gfl'))
async def handle_get_fire_level(p):
    await p.send_xt('gfl', p.fire_ninja_rank, get_percentage_to_next_fire_item(p.fire_ninja_progress, p.fire_ninja_rank), 5)


@handlers.handler(XTPacket('ni', 'gwl'))
async def handle_get_water_level(p):
    await p.send_xt('gwl', p.water_ninja_rank, get_percentage_to_next_water_item(p.water_ninja_progress, p.water_ninja_rank), 5)


@handlers.handler(XTPacket('ni', 'gsl'))
@handlers.cooldown(1)
async def handle_get_snow_level(p):
    # Snow ninja data should be taken from the database, not memory
    snow_ninja_rank, snow_ninja_progress = await Penguin.select(
        'snow_ninja_rank', 'snow_ninja_progress'
    ).where(Penguin.id == p.id).gino.first()
    await p.send_xt('gsl', snow_ninja_rank, snow_ninja_progress, 24)


@handlers.handler(XTPacket('ni', 'gcd'))
async def handle_get_card_data(p):
    await p.send_xt('gcd', '|'.join(f'{card.card_id},{card.quantity+card.member_quantity}'
                                    for card in p.cards.values()))
