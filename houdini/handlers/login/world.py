from houdini import handlers
from houdini.handlers import XMLPacket, login
from houdini.converters import WorldCredentials
from houdini.data.penguin import Penguin
from houdini.data.moderator import Ban

from datetime import datetime

handle_version_check = login.handle_version_check
handle_random_key = login.handle_random_key


@handlers.handler(XMLPacket('login'))
@handlers.allow_once()
async def handle_login(p, credentials: WorldCredentials):
    tr = p.server.redis.multi_exec()
    tr.get('{}.lkey'.format(credentials.id))
    tr.get('{}.ckey'.format(credentials.id))
    tr.delete('{}.lkey'.format(credentials.id), '{}.ckey'.format(credentials.id))
    login_key, confirmation_hash, _ = await tr.execute()

    if login_key is None or confirmation_hash is None:
        return await p.close()

    if login_key.decode() != credentials.login_key or confirmation_hash.decode() != credentials.confirmation_hash:
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
    p.login_key = credentials.login_key
    await p.send_xt('l')

    p.age = (datetime.now() - p.data.registration_date).days
