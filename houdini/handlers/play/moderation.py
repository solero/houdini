from houdini import handlers
from houdini.data import db
from houdini.handlers import XTPacket
from houdini.data.moderator import Ban, Warning, Report

import datetime


@handlers.handler(XTPacket('o', 'k'))
async def handle_kick_player(p, penguin_id: int):
    if p.data.moderator:
        await moderator_kick(p, penguin_id)


@handlers.handler(XTPacket('o', 'b'))
async def handle_ban_player(p, penguin_id: int, message: str):
    if p.data.moderator:
        await moderator_ban(p, penguin_id, comment=message)


@handlers.handler(XTPacket('o', 'm'))
async def handle_mute_player(p, penguin_id: int):
    if p.data.moderator:
        if penguin_id in p.server.penguins_by_id:
            player = p.server.penguins_by_id[penguin_id]
            if not player.data.moderator:
                player.muted = True


@handlers.handler(XTPacket('o', 'initban'))
async def handle_init_ban(p, penguin_id: int, message: str):
    if penguin_id in p.server.penguins_by_id and p.data.moderator:
        player = p.server.penguins_by_id[penguin_id]

        if not player.data.moderator:
            number_bans = await db.select([db.func.count(Ban.penguin_id)]).where(
                Ban.penguin_id == player.data.id).gino.scalar()

            await p.send_xt('initban', penguin_id, 0, number_bans, message, player.data.username)


@handlers.handler(XTPacket('o', 'ban'))
async def handle_moderator_ban(p, penguin_id: int, ban_type: int, reason: int, duration: int, message: str, notes: str):
    if p.data.moderator:
        if penguin_id in p.server.penguins_by_id:
            player = p.server.penguins_by_id[penguin_id]
            if not player.data.moderator:
                date_issued = datetime.datetime.now()
                date_expires = date_issued + datetime.timedelta(hours=duration)

                if duration == 0:
                    await player.data.update(permaban=True).apply()

                await Ban.create(penguin_id=player.data.id, issued=date_issued, expires=date_expires,
                                 moderator_id=p.data.id, reason=reason, comment=notes)
                await player.send_xt('ban', ban_type, reason, duration, notes)
                await player.close()


@handlers.handler(XTPacket('m', 'r'))
async def handle_report(p, penguin_id: int, *reason):
    reason = int(reason[0]) if reason else 0
    date_now = datetime.datetime.now()
    server_id = p.server.server_config['Id']
    print(server_id)
    await Report.create(penguin_id=penguin_id, reporter_id=p.data.id, report_type=reason, date=date_now, server_id=server_id, room_id=p.room.id)


@handlers.handler(XTPacket('o', 'moderatormessage'))
async def handle_moderator_message(p, type: int, penguin_id: int):
    if p.data.moderator:
        if penguin_id in p.server.penguins_by_id:
            player = p.server.penguins_by_id[penguin_id]
            date_issued = datetime.datetime.now()
            date_expires = date_issued + datetime.timedelta(hours=48)
            warning_count = await db.select([db.func.count(Warning.expires)]).where(
                (Warning.penguin_id == player.data.id) & (Warning.expires >= date_issued)).gino.scalar()

            if warning_count >= 3:
                return await moderator_ban(p, player.data.id, comment='Exceeded warning limit')

            await player.send_xt('moderatormessage', type)
            await Warning.create(penguin_id=player.data.id, expires=date_expires)


async def moderator_kick(p, penguin_id):
    if penguin_id in p.server.penguins_by_id and p.data.moderator:
        player = p.server.penguins_by_id[penguin_id]
        if not player.data.moderator:
            for penguin in p.server.penguins_by_id.values():
                if penguin.data.moderator:
                    await penguin.send_xt('ma', 'k', penguin_id, player.data.username)
            await player.send_error_and_disconnect(5)


async def moderator_ban(p, penguin_id, hours=24, comment=''):
    if penguin_id in p.server.penguins_by_id and p.data.moderator:
        player = p.server.penguins_by_id[penguin_id]
        if not player.data.moderator:
            for penguin in p.server.penguins_by_id.values():
                if penguin.data.moderator:
                    await penguin.send_xt('ma', 'b', penguin_id, player.data.username)

            number_bans = await db.select([db.func.count(Ban.penguin_id)]).where(
                Ban.penguin_id == player.data.id).gino.scalar()

            date_issued = datetime.datetime.now()
            date_expires = date_issued + datetime.timedelta(hours=hours)

            if number_bans >= 3:
                await player.data.update(permaban=True).apply()

            await Ban.create(penguin_id=player.data.id, issued=date_issued, expires=date_expires,
                             moderator_id=p.data.id, reason=1, comment=comment)

            await player.send_error_and_disconnect(610, comment)
            await player.close()
