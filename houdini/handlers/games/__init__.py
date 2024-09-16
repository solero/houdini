import random
import time

from sqlalchemy.dialects.postgresql import insert

from houdini import handlers
from houdini.constants import ClientType
from houdini.converters import OptionalConverter
from houdini.data.game import PenguinGameData
from houdini.data.room import Room
from houdini.handlers import XTPacket
from houdini.handlers.play.moderation import cheat_ban
from houdini.handlers.play.navigation import handle_join_room

default_score_games = {904, 905, 906, 912, 916, 917, 918, 919, 950, 952}


def determine_coins_earned(p, score):
    return score if p.room.id in default_score_games else score // 10


async def determine_coins_overdose(p, coins):
    overdose_key = f'{p.id}.overdose'
    last_overdose = await p.server.redis.get(overdose_key)

    if last_overdose is None:
        return True

    minutes_since_last_dose = ((time.time() - float(last_overdose)) // 60) + 1
    max_game_coins = p.server.config.max_coins_per_min * minutes_since_last_dose

    if coins > max_game_coins:
        return True

    await p.server.redis.delete(overdose_key)
    return False


@handlers.handler(XTPacket('j', 'jr'), before=handle_join_room)
async def handle_overdose_key(p, room: Room):
    if p.room.game and not room.game:
        overdose_key = f'{p.id}.overdose'
        await p.server.redis.delete(overdose_key)
    elif room.game:
        overdose_key = f'{p.id}.overdose'
        await p.server.redis.set(overdose_key, time.time())


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def disconnect_overdose_key(p):
    if p.room is not None and p.room.game:
        overdose_key = f'{p.id}.overdose'
        await p.server.redis.delete(overdose_key)


async def game_over_cooling(p):
    await p.send_xt('zo', p.coins, '', 0, 0, 0)


@handlers.handler(XTPacket('m', ext='z'))
@handlers.player_in_room(802)
async def handle_send_move_puck(p, _, x: int, y: int, speed_x: int, speed_y: int):
    p.server.puck = (x, y)
    await p.room.send_xt('zm', p.id, x, y, speed_x, speed_y)


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.player_in_room(802)
async def handle_get_puck(p):
    await p.send_xt('gz', *p.server.puck)


@handlers.handler(XTPacket('zo', ext='z'))
@handlers.cooldown(10, callback=game_over_cooling)
async def handle_get_game_over(p, score: int):
    # If the room is Card Jitsu Snow, it this should do nothing
    if p.room.id == 996:
        return

    # card-jitsus except snow have special handling
    card_jitsu_rooms = [995, 998, 997]
    is_card_jitsu = p.room.id in card_jitsu_rooms

    # Waddle minigames don't normally need the end screen
    if p.waddle and not is_card_jitsu:
        return

    if p.room.game and not p.table:
        coins_earned = determine_coins_earned(p, score)

        if not is_card_jitsu:
            if await determine_coins_overdose(p, coins_earned):
                return await cheat_ban(p, p.id, comment="Coins overdose")

        stamp_info = "", 0, 0, 0

        if p.room.stamp_group:
            stamp_info = await p.get_game_end_stamps_info(True)
            # has all stamps in game
            if stamp_info[1] == stamp_info[2]:
                coins_earned *= 2

        if not is_card_jitsu:
            await p.update(
                coins=min(p.coins + coins_earned, p.server.config.max_coins)
            ).apply()
        await p.send_xt("zo", p.coins, *stamp_info)


@handlers.handler(XTPacket('ggd', ext='z'), client=ClientType.Vanilla)
async def handle_get_game_data(p, index: int = 0):
    game_data = await PenguinGameData.select('data').where((PenguinGameData.penguin_id == p.id) &
                                                           (PenguinGameData.room_id == p.room.id) &
                                                           (PenguinGameData.index == index)).gino.scalar()
    await p.send_xt('ggd', game_data or '')


@handlers.handler(XTPacket('sgd', ext='z'), client=ClientType.Vanilla)
@handlers.cooldown(5)
async def handle_set_game_data(p, index: OptionalConverter(int) = 0, *, game_data: str):
    if p.room.game:
        data_insert = insert(PenguinGameData).values(penguin_id=p.id, room_id=p.room.id, index=index, data=game_data)
        data_insert = data_insert.on_conflict_do_update(
            constraint='penguin_game_data_pkey',
            set_=dict(data=game_data),
            where=((PenguinGameData.penguin_id == p.id)
                   & (PenguinGameData.room_id == p.room.id)
                   & (PenguinGameData.index == index))
        )

        await data_insert.gino.scalar()


@handlers.handler(XTPacket('zr', ext='z'), client=ClientType.Vanilla)
@handlers.player_attribute(agent_status=True)
async def handle_get_game_again(p):
    games = list(range(1, 11))

    games_string = f'{games.pop(random.randrange(len(games)))},' \
                   f'{games.pop(random.randrange(len(games)))},' \
                   f'{games.pop(random.randrange(len(games)))}'
    await p.send_xt('zr', games_string, random.randint(1, 6))


@handlers.handler(XTPacket('zc', ext='z'), client=ClientType.Vanilla)
@handlers.player_attribute(agent_status=True)
@handlers.cooldown(5)
async def handle_game_complete(p, medals: int):
    medals = min(6, medals)
    await p.update(career_medals=p.career_medals + medals,
                   agent_medals=p.agent_medals + medals).apply()


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def clear_stamp_sessions(p):
    """When disconnected, clear stamps in case any were obtained and not properly handled"""
    await p.clear_stamps_session()
