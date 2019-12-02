from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_room
from houdini.handlers.play.moderation import cheat_ban
from houdini.data.room import Room

import time


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
    if p.room.game:
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
    if p.room.game:
        coins_earned = determine_coins_earned(p, score)
        if await determine_coins_overdose(p, coins_earned):
            await cheat_ban(p, p.id, comment='Coins overdose')

        collected_stamps_string, total_collected_stamps, total_game_stamps, total_stamps = '', 0, 0, 0
        if p.room.stamp_group:
            game_stamps = [stamp for stamp in p.server.stamps.values() if stamp.group_id == p.room.stamp_group]
            collected_stamps = [stamp for stamp in game_stamps if stamp.id in p.stamps]

            total_stamps = len([stamp for stamp in p.stamps.values() if p.server.stamps[stamp.stamp_id].group_id])
            total_collected_stamps = len(collected_stamps)
            total_game_stamps = len(game_stamps)
            collected_stamps_string = '|'.join(str(stamp.id) for stamp in collected_stamps)

            if total_collected_stamps == total_game_stamps:
                coins_earned *= 2

        await p.update(coins=min(p.coins + coins_earned, p.server.config.max_coins)).apply()
        await p.send_xt('zo', p.coins,
                        collected_stamps_string,
                        total_collected_stamps,
                        total_game_stamps,
                        total_stamps)
