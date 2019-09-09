import config

from houdini import handlers
from houdini.handlers import XMLPacket, login
from houdini.converters import WorldCredentials, Credentials
from houdini.data.penguin import Penguin
from houdini.data.moderator import Ban
from houdini.crypto import Crypto
from houdini.constants import ClientType

from datetime import datetime

handle_version_check = login.handle_version_check
handle_random_key = login.handle_random_key


@handlers.handler(XMLPacket('login'), client=ClientType.Vanilla)
@handlers.allow_once
@handlers.depends_on_packet(XMLPacket('verChk'), XMLPacket('rndK'))
async def handle_login(p, credentials: WorldCredentials):
    if len(p.server.penguins_by_id) >= p.server.server_config['Capacity']:
        return await p.send_error_and_disconnect(103)

    tr = p.server.redis.multi_exec()
    tr.get('{}.lkey'.format(credentials.username))
    tr.get('{}.ckey'.format(credentials.username))
    tr.delete('{}.lkey'.format(credentials.username), '{}.ckey'.format(credentials.username))
    login_key, confirmation_hash, _ = await tr.execute()

    if login_key is None or confirmation_hash is None:
        return await p.close()

    login_key = login_key.decode()
    login_hash = Crypto.encrypt_password(login_key + config.client['AuthStaticKey']) + login_key

    if credentials.client_key != login_hash:
        return await p.close()

    if login_key != credentials.login_key or confirmation_hash.decode() != credentials.confirmation_hash:
        return await p.close()

    data = await Penguin.get(credentials.id)

    if data is None:
        return await p.send_error_and_disconnect(100)

    if not data.active:
        return await p.close()

    if data.permaban:
        return await p.close()

    active_ban = await Ban.query.where((Ban.penguin_id == data.id) & (Ban.expires >= datetime.now())).gino.scalar()
    if active_ban is not None:
        return await p.close()

    if data.id in p.server.penguins_by_id:
        await p.server.penguins_by_id[data.id].close()

    p.logger.info('{} logged in successfully'.format(data.username))

    p.data = data
    p.login_key = login_key
    await p.send_xt('l')


@handlers.handler(XMLPacket('login'), client=ClientType.Legacy)
@handlers.allow_once
@handlers.depends_on_packet(XMLPacket('verChk'), XMLPacket('rndK'))
async def handle_legacy_login(p, credentials: Credentials):
    if len(p.server.penguins_by_id) >= p.server.server_config['Capacity']:
        return await p.send_error_and_disconnect(103)

    tr = p.server.redis.multi_exec()
    tr.get('{}.lkey'.format(credentials.username))
    tr.delete('{}.lkey'.format(credentials.username), '{}.ckey'.format(credentials.username))
    login_key,  _ = await tr.execute()

    login_key = login_key.decode()
    login_hash = Crypto.encrypt_password(login_key + config.client['AuthStaticKey']) + login_key

    if login_key is None or login_hash != credentials.password:
        return await p.close()

    data = await Penguin.query.where(Penguin.username == credentials.username).gino.first()

    if data is None:
        return await p.send_error_and_disconnect(100)

    if not data.active:
        return await p.close()

    if data.permaban:
        return await p.close()

    active_ban = await Ban.query.where((Ban.penguin_id == data.id) & (Ban.expires >= datetime.now())).gino.scalar()
    if active_ban is not None:
        return await p.close()

    if data.id in p.server.penguins_by_id:
        await p.server.penguins_by_id[data.id].close()

    p.logger.info('{} logged in successfully'.format(data.username))

    p.data = data
    p.login_key = login_key
    await p.send_xt('l')
