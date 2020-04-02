import asyncio
import random
import time
from datetime import datetime, timedelta

from houdini import handlers
from houdini.constants import ClientType
from houdini.converters import SeparatorConverter
from houdini.data import db
from houdini.data.mail import PenguinPostcard
from houdini.data.penguin import Penguin, PenguinMembership
from houdini.handlers import Priority, XMLPacket, XTPacket


async def get_player_string(p, penguin_id: int):
    if penguin_id in p.server.penguins_by_id:
        return await p.server.penguins_by_id[penguin_id].string
    else:
        player_data = await Penguin.get(penguin_id)
        string = await p.server.anonymous_penguin_string_compiler.compile(player_data)
        return string


async def get_mascot_string(p, mascot_id: int):
    if mascot_id in p.server.penguins_by_character_id:
        return await p.server.penguins_by_character_id[mascot_id].string
    else:
        player_data = await Penguin.query.where(Penguin.character == mascot_id).gino.first()
        string = await p.server.anonymous_penguin_string_compiler.compile(player_data)
        return string


async def server_heartbeat(server):
    while True:
        timer = time.time()
        await asyncio.sleep(61)
        for penguin in server.penguins_by_id.values():
            if penguin.heartbeat < timer:
                await penguin.close()


async def server_egg_timer(server):
    while True:
        await asyncio.sleep(60)
        for p in server.penguins_by_id.values():
            if p.timer_active:
                p.egg_timer_minutes -= 1
                if p.is_vanilla_client:
                    minutes_until_timer_end = datetime.combine(datetime.today(), p.timer_end) - datetime.now()
                    minutes_until_timer_end = minutes_until_timer_end.total_seconds() // 60

                    if minutes_until_timer_end <= p.egg_timer_minutes + 1:
                        if p.egg_timer_minutes == 7:
                            await p.send_error(915, p.egg_timer_minutes, p.timer_start, p.timer_end)
                        elif p.egg_timer_minutes == 5:
                            await p.send_error(915, p.egg_timer_minutes, p.timer_start, p.timer_end)
                    else:
                        if p.egg_timer_minutes == 7:
                            await p.send_error(914, p.egg_timer_minutes, p.timer_total)
                        elif p.egg_timer_minutes == 5:
                            await p.send_error(914, p.egg_timer_minutes, p.timer_total)

                    await p.send_xt('uet', max(0, p.egg_timer_minutes))
                    if p.egg_timer_minutes < 0:
                        await p.send_error_and_disconnect(916, p.timer_start, p.timer_end)
                else:
                    if p.egg_timer_minutes < 0:
                        await p.send_error_and_disconnect(910)


MemberWarningDaysToExpiry = 14
MemberWarningPostcardsVanilla = [122, 123]
MemberWarningPostcardsLegacy = [163]
MemberExpiredPostcard = 124
MemberStartPostcardVanilla = 121
MemberStartPostcardLegacy = 164
FullBadgeAge = 25 * 30


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def setup_membership(p):
    if not p.server.config.expire_membership or p.moderator or p.character:
        p.is_member = True
        p.membership_days_total = FullBadgeAge if p.moderator or p.character else p.age
        return

    membership_history = PenguinMembership.query.where(PenguinMembership.penguin_id == p.id)
    current_timestamp = datetime.now()
    postcards = []

    warning_postcards = MemberWarningPostcardsVanilla if p.is_vanilla_client else MemberWarningPostcardsLegacy
    start_postcard = MemberStartPostcardVanilla if p.is_vanilla_client else MemberStartPostcardLegacy

    async with db.transaction():
        async for membership_record in membership_history.gino.iterate():
            membership_recurring = membership_record.expires is None
            membership_active = membership_recurring or membership_record.expires >= current_timestamp

            if membership_record.start < current_timestamp:
                if membership_active:
                    p.is_member = True

                    if not membership_recurring:
                        days_to_expiry = (membership_record.expires.date() - datetime.now().date()).days
                        p.membership_days_remain = days_to_expiry

                        if days_to_expiry <= MemberWarningDaysToExpiry and not membership_record.expires_aware:
                            postcards.append(dict(
                                penguin_id=p.id,
                                postcard_id=random.choice(warning_postcards),
                                send_date=membership_record.expires - timedelta(days=MemberWarningDaysToExpiry)
                            ))
                            await membership_record.update(expires_aware=True).apply()
                else:
                    if p.membership_days_remain < 0:
                        days_since_expiry = (membership_record.expires.date() - datetime.now().date()).days
                        p.membership_days_remain = min(p.membership_days_remain, days_since_expiry)

                    if not membership_record.expired_aware:
                        if p.is_vanilla_client:
                            postcards.append(dict(
                                penguin_id=p.id,
                                postcard_id=MemberExpiredPostcard,
                                send_date=membership_record.expires
                            ))
                        await membership_record.update(expired_aware=True).apply()

                if not membership_record.start_aware:
                    postcards.append(dict(
                        penguin_id=p.id,
                        postcard_id=start_postcard,
                        send_date=membership_record.start
                    ))
                    await membership_record.update(start_aware=True).apply()

            membership_end_date = current_timestamp if membership_active else membership_record.expires
            p.membership_days_total += (membership_end_date - membership_record.start).days

    if postcards:
        await PenguinPostcard.insert().values(postcards).gino.status()


@handlers.handler(XTPacket('u', 'h'))
@handlers.cooldown(59)
async def handle_heartbeat(p):
    p.heartbeat = time.time()
    await p.send_xt('h')


@handlers.handler(XTPacket('u', 'gp'))
@handlers.cooldown(1)
async def handle_get_player(p, penguin_id: int):
    player_string = p.server.cache.get(f'player.{penguin_id}')
    player_string = await get_player_string(p, penguin_id) if player_string is None else player_string
    await p.send_xt('gp', player_string)


@handlers.handler(XTPacket('u', 'gmo'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_mascot(p, mascot_id: int):
    mascot_string = p.server.cache.get(f'mascot.{mascot_id}')
    mascot_string = await get_mascot_string(p, mascot_id) if mascot_string is None else mascot_string
    p.server.cache.set(f'mascot.{mascot_id}', mascot_string)
    await p.send_xt('gmo', mascot_string)


@handlers.handler(XTPacket('u', 'pbi'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_by_id(p, penguin_id: int):
    await p.send_xt('pbi', penguin_id)


@handlers.handler(XTPacket('u', 'pbs'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_by_swid(p, penguin_id: int):
    if penguin_id in p.server.penguins_by_id:
        nickname = p.server.penguins_by_id[penguin_id].safe_name
    else:
        nickname = await Penguin.select('nickname').where(Penguin.id == penguin_id).gino.scalar()
    await p.send_xt('pbs', penguin_id, penguin_id, nickname)


_id_converter = SeparatorConverter(separator=',', mapper=int)


@handlers.handler(XTPacket('u', 'pbsu'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_username_by_swid(p, ids: _id_converter):
    ids = list(ids)
    query = Penguin.select('id', 'nickname').where(Penguin.id.in_(ids))
    async with p.server.db.transaction():
        nicknames = {
            pid: nickname async for pid, nickname in query.gino.iterate()}

    await p.send_xt('pbsu', ','.join(nicknames[pid] for pid in ids))


@handlers.handler(XTPacket('u', 'gabcms'))
async def handle_get_ab_test_data(p):
    pass


@handlers.handler(XTPacket('u', 'rpfi'))
async def handle_send_refresh_player_friend_info(p):
    pass


@handlers.handler(XTPacket('u', 'pbn'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_player_by_name(p, player_name: str):
    player_name = player_name.lower()
    if player_name in p.server.penguins_by_username:
        player = p.server.penguins_by_username[player_name]
        await p.send_xt('pbn', player.id, player.id, player.safe_name)
    else:
        result = await Penguin.select('id', 'nickname').where(
            Penguin.username == player_name).gino.first()
        if result is not None:
            player_id, nickname = result
            await p.send_xt('pbn', player_id, player_id, nickname)
        else:
            await p.send_xt('pbn')


@handlers.handler(XTPacket('u', 'smi'), client=ClientType.Vanilla)
@handlers.cooldown(10)
async def handle_send_mascot_invite(p, num_invites: int, character_id: int):
    if character_id in p.server.characters and p.character is not None:
        players = random.sample(list(p.server.penguins_by_id.values()), min(num_invites, len(p.server.penguins_by_id)))
        for player in players:
            await player.send_xt('smi', character_id)


@handlers.handler(XTPacket('u', 'bf'), client=ClientType.Vanilla)
async def handle_find_player(p, player_id: int):
    if player_id in p.server.penguins_by_id:
        player = p.server.penguins_by_id[player_id]
        room_id = player.room.id
        room_type = 'backyard' if player.room.backyard else 'igloo' if player.room.igloo else 'invalid'
        room_owner = player.room.penguin_id if player.room.igloo else -1
    else:
        room_id, room_type, room_owner = -1, 'invalid', -1
    await p.send_xt('bf', room_id, room_type, room_owner)


@handlers.handler(XTPacket('u', 'gbffl'))
async def handle_get_best_friends(p):
    await p.send_xt('gbffl', ','.join((str(buddy.buddy_id) for buddy in p.buddies.values() if buddy.best_buddy)))


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
    await p.room.send_xt('sp', p.id, x, y)


@handlers.handler(XTPacket('u', 'sf'))
@handlers.cooldown(.5)
async def handle_set_player_frame(p, frame: int):
    p.frame = frame
    await p.room.send_xt('sf', p.id, frame)


@handlers.handler(XTPacket('u', 'sb'))
@handlers.cooldown(1)
async def handle_send_throw_ball(p, x: int, y: int):
    await p.room.send_xt('sb', p.id, x, y)


@handlers.handler(XTPacket('u', 'se'))
@handlers.cooldown(1)
async def handle_send_emote(p, emote: int):
    await p.room.send_xt('se', p.id, emote)


@handlers.handler(XTPacket('u', 'sa'))
@handlers.cooldown(1)
async def handle_send_action(p, action: int):
    await p.room.send_xt('sa', p.id, action)


@handlers.handler(XTPacket('u', 'followpath'))
@handlers.cooldown(1)
async def handle_follow_path(p, path: int):
    await p.room.send_xt('followpath', p.id, path)


@handlers.handler(XTPacket('u', 'ss'))
async def handle_send_safe_message(p, message_id: int):
    await p.room.send_xt('ss', p.id, message_id)


@handlers.handler(XTPacket('u', 'sma'))
async def handle_send_mascot_message(p, message_id: int):
    if p.character:
        await p.room.send_xt('sma', p.id, message_id)


@handlers.handler(XTPacket('u', 'glr'))
async def handle_get_last_revision(p):
    await p.send_xt('glr', 'houdini')
