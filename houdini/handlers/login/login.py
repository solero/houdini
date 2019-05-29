from houdini import handlers
from houdini.handlers import XMLPacket, login
from houdini.converters import Credentials
from houdini.data.penguin import Penguin
from houdini.data.buddy import BuddyList
from houdini.data.moderator import Ban
from houdini.crypto import Crypto

import asyncio
import bcrypt
import time
import os
import config

from datetime import datetime


@handlers.handler(XMLPacket('login'))
@handlers.allow_once()
async def handle_login(p, credentials: Credentials):
    loop = asyncio.get_event_loop()

    login_timestamp = time.time()
    username, password = credentials.username, credentials.password
    p.logger.info('{} is logging in!'.format(username))

    data = await Penguin.query.where(Penguin.username == username).gino.first()

    if data is None:
        p.logger.info('{} failed to login: penguin does not exist')
        await p.send_error_and_disconnect(100)

    password_correct = await loop.run_in_executor(None, bcrypt.checkpw,
                                                  password.encode('utf-8'), data.password.encode('utf-8'))

    ip_addr = p.peer_name[0]

    if not password_correct:
        p.logger.info('{} failed to login: incorrect password'.format(username))

        if ip_addr in p.server.login_attempts:
            last_failed_attempt, failure_count = p.server.login_attempts[ip_addr]

            failure_count = 1 if login_timestamp - last_failed_attempt >= p.server.server_config['LoginFailureTimer'] \
                else failure_count + 1

            p.server.login_attempts[ip_addr] = [login_timestamp, failure_count]

            if failure_count >= p.server.server_config['LoginFailureLimit']:
                return await p.send_error_and_disconnect(150)
        else:
            p.server.login_attempts[ip_addr] = [login_timestamp, 1]

        return await p.send_error_and_disconnect(101)

    if ip_addr in p.server.login_attempts:
        previous_attempt, failure_count = p.server.login_attempts[ip_addr]

        max_attempts_exceeded = failure_count >= p.server.server_config['LoginFailureLimit']
        timer_surpassed = (login_timestamp - previous_attempt) > p.server.server_config['LoginFailureTimer']

        if max_attempts_exceeded and not timer_surpassed:
            return await p.send_error_and_disconnect(150)
        else:
            del p.server.login_attempts[ip_addr]

    if not data.active:
        return await p.send_error_and_disconnect(900)

    if data.permaban:
        return await p.send_error_and_disconnect(603)

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
    tr.setex('{}.lkey'.format(data.id), p.server.server_config['KeyTTL'], login_key)
    tr.setex('{}.ckey'.format(data.id), p.server.server_config['KeyTTL'], confirmation_hash)
    await tr.execute()

    buddy_worlds = []
    world_populations = []

    servers_config = config.servers

    for server_name, server_config in servers_config.items():
        if server_config['World']:
            server_population = await p.server.redis.get('{}.population'.format(server_name))
            server_population = (7 if int(server_population) == server_config['Capacity']
                                 else int(server_population) / (server_config['Capacity'] / 6)) \
                if server_population else 0

            server_players = await p.server.redis.smembers('{}.players'.format(server_name))

            world_populations.append('{},{}'.format(server_config['Id'], server_population))

            if not len(server_players) > 0:
                p.logger.debug('Skipping buddy iteration for {}'.format(server_name))
                continue

            buddies = await BuddyList.select('BuddyID').where(BuddyList.PenguinID == data.ID).gino.all()
            for buddy_id in buddies:
                if str(buddy_id) in server_players:
                    buddy_worlds.append(server_config['Id'])
                    break

    raw_login_data = '|'.join([str(data.id), str(data.id), data.username, login_key, str(data.approval),
                               str(data.rejection)])
    await p.send_xt('l', raw_login_data, confirmation_hash, '', '|'.join(world_populations), '|'.join(buddy_worlds),
                    data.email)

handle_version_check = login.handle_version_check
handle_random_key = login.handle_random_key
