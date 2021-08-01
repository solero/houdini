import asyncio
import os
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import func

from houdini import handlers
from houdini.constants import ClientType
from houdini.converters import Credentials
from houdini.crypto import Crypto
from houdini.data.moderator import Ban
from houdini.data.penguin import Penguin
from houdini.handlers import XMLPacket
from houdini.handlers.login import get_server_presence
from houdini.handlers.play.navigation import get_minutes_played_today


@handlers.handler(XMLPacket('login'))
@handlers.allow_once
@handlers.depends_on_packet(XMLPacket('verChk'), XMLPacket('rndK'))
async def handle_login(p, credentials: Credentials):
    loop = asyncio.get_event_loop()

    username, password = credentials.username, credentials.password
    p.logger.info(f'{username} is logging in!')

    data = await Penguin.query.where(func.lower(Penguin.username) == username).gino.first()

    if data is None:
        p.logger.info(f'{username} failed to login: penguin does not exist')
        return await p.send_error_and_disconnect(100)

    password_correct = await loop.run_in_executor(None, bcrypt.checkpw,
                                                  password.encode('utf-8'), data.password.encode('utf-8'))

    ip_addr = p.peer_name[0]
    flood_key = f'{ip_addr}.flood'

    if not password_correct:
        p.logger.info(f'{username} failed to login: incorrect password')

        if await p.server.redis.exists(flood_key):
            async with p.server.redis.pipeline(transaction=True) as tr:
                tr.incr(flood_key)
                tr.expire(flood_key, p.server.config.login_failure_timer)
                failure_count, _ = await tr.execute()

            if failure_count >= p.server.config.login_failure_limit:
                return await p.send_error_and_disconnect(150)
        else:
            await p.server.redis.setex(flood_key, p.server.config.login_failure_timer, 1)

        return await p.send_error_and_disconnect(101)

    failure_count = await p.server.redis.get(flood_key)
    if failure_count:
        max_attempts_exceeded = int(failure_count) >= p.server.config.login_failure_limit

        if max_attempts_exceeded:
            return await p.send_error_and_disconnect(150)
        else:
            await p.server.redis.delete(flood_key)

    preactivation_hours = 0
    if not data.active:
        preactivation_expiry = data.registration_date + timedelta(days=p.server.config.preactivation_days)
        preactivation_expiry = preactivation_expiry - datetime.now()
        preactivation_hours = preactivation_expiry.total_seconds() // 3600
        if preactivation_hours <= 0 or p.client_type == ClientType.Legacy:
            return await p.send_error_and_disconnect(900)

    if data.permaban:
        return await p.send_error_and_disconnect(603)

    if data.grounded:
        return await p.send_error_and_disconnect(913)

    if data.timer_active:
        if not data.timer_start < datetime.now().time() < data.timer_end:
            return await p.send_error_and_disconnect(911, data.timer_start, data.timer_end)

        minutes_played_today = await get_minutes_played_today(p)
        if minutes_played_today >= data.timer_total.total_seconds() // 60:
            return await p.send_error_and_disconnect(910, data.timer_total)

    active_ban = await Ban.query.where((Ban.penguin_id == data.id) & (Ban.expires >= datetime.now())).gino.first()

    if active_ban is not None:
        hours_left = round((active_ban.expires - datetime.now()).total_seconds() / 60 / 60)

        if hours_left == 0:
            return await p.send_error_and_disconnect(602)
        else:
            return await p.send_error_and_disconnect(601, hours_left)

    p.logger.info(f'{username} has logged in successfully')

    random_key = Crypto.generate_random_key()
    login_key = Crypto.hash(random_key[::-1])
    confirmation_hash = Crypto.hash(os.urandom(24))


    async with p.server.redis.pipeline(transaction=True) as tr:
        tr.setex(f'{data.username}.lkey', p.server.config.auth_ttl, login_key)
        tr.setex(f'{data.username}.ckey', p.server.config.auth_ttl, confirmation_hash)
        await tr.execute()

    world_populations, buddy_presence = await get_server_presence(p, data)

    if p.client_type == ClientType.Vanilla:
        raw_login_data = f'{data.id}|{data.id}|{data.username}|{login_key}|houdini|{data.approval}|{data.rejection}'
        if not data.active:
            await p.send_xt('l', raw_login_data, confirmation_hash, '', world_populations, buddy_presence,
                            data.email, int(preactivation_hours))
        else:
            await p.send_xt('l', raw_login_data, confirmation_hash, '', world_populations, buddy_presence, data.email)
    else:
        await p.send_xt('l', data.id, login_key, buddy_presence, world_populations)
