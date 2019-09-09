from houdini import handlers
from houdini.handlers import XMLPacket
from houdini.handlers.login import get_server_presence
from houdini.converters import Credentials
from houdini.data.penguin import Penguin
from houdini.data.moderator import Ban
from houdini.crypto import Crypto
from houdini.constants import ClientType

import asyncio
import bcrypt
import os

from datetime import datetime


@handlers.handler(XMLPacket('login'))
@handlers.allow_once
@handlers.depends_on_packet(XMLPacket('verChk'), XMLPacket('rndK'))
async def handle_login(p, credentials: Credentials):
    loop = asyncio.get_event_loop()

    username, password = credentials.username, credentials.password
    p.logger.info('{} is logging in!'.format(username))

    data = await Penguin.query.where(Penguin.username == username).gino.first()

    if data is None:
        p.logger.info('{} failed to login: penguin does not exist'.format(username))
        return await p.send_error_and_disconnect(100)

    password_correct = await loop.run_in_executor(None, bcrypt.checkpw,
                                                  password.encode('utf-8'), data.password.encode('utf-8'))

    ip_addr = p.peer_name[0]
    flood_key = '{}.flood'.format(ip_addr)

    if not password_correct:
        p.logger.info('{} failed to login: incorrect password'.format(username))

        if await p.server.redis.exists(flood_key):
            tr = p.server.redis.multi_exec()
            tr.incr(flood_key)
            tr.expire(flood_key, p.server.server_config['LoginFailureTimer'])
            failure_count, _ = await tr.execute()

            if failure_count >= p.server.server_config['LoginFailureLimit']:
                return await p.send_error_and_disconnect(150)
        else:
            await p.server.redis.setex(flood_key, p.server.server_config['LoginFailureTimer'], 1)

        return await p.send_error_and_disconnect(101)

    failure_count = await p.server.redis.get(flood_key)
    if failure_count:
        max_attempts_exceeded = int(failure_count) >= p.server.server_config['LoginFailureLimit']

        if max_attempts_exceeded:
            return await p.send_error_and_disconnect(150)
        else:
            await p.server.redis.delete(flood_key)

    preactivation_hours = 0
    if not data.active:
        preactivation_expiry = data.registration_date + timedelta(days=7)
        preactivation_expiry = preactivation_expiry - datetime.now()
        preactivation_hours = preactivation_expiry.total_seconds() // 3600
        if preactivation_hours <= 0 or p.client_type == ClientType.Legacy:
            return await p.send_error_and_disconnect(900)

    if data.permaban:
        return await p.send_error_and_disconnect(603)

    if data.grounded:
        return await p.send_error_and_disconnect(913)
    active_ban = await Ban.query.where(Ban.penguin_id == data.id and Ban.expires >= datetime.now()).gino.first()

    if active_ban is not None:
        hours_left = round((active_ban.expires - datetime.now()).total_seconds() / 60 / 60)

        if hours_left == 0:
            return await p.send_error_and_disconnect(602)
        else:
            await p.send_error_and_disconnect(601, hours_left)

    p.logger.info('{} has logged in successfully'.format(username))

    random_key = Crypto.generate_random_key()
    login_key = Crypto.hash(random_key[::-1])
    confirmation_hash = Crypto.hash(os.urandom(24))

    tr = p.server.redis.multi_exec()
    tr.setex('{}.lkey'.format(data.username), p.server.server_config['KeyTTL'], login_key)
    tr.setex('{}.ckey'.format(data.username), p.server.server_config['KeyTTL'], confirmation_hash)
    await tr.execute()

    world_populations, buddy_presence = await get_server_presence(p, data.id)

    if p.client_type == ClientType.Vanilla:
        raw_login_data = '|'.join([str(data.id), str(data.id), data.username, login_key, str(data.approval),
                                   str(data.rejection)])
        if not data.active:
            await p.send_xt('l', raw_login_data, confirmation_hash, '', world_populations, buddy_presence,
                            data.email, int(preactivation_hours))
        else:
            await p.send_xt('l', raw_login_data, confirmation_hash, '', world_populations, buddy_presence, data.email)
    else:
        await p.send_xt('l', data.id, login_key, world_populations, buddy_presence)
