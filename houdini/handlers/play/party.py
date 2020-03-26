import ujson

from houdini import handlers
from houdini.handlers import XTPacket

DefaultPartyCookie = {
    'msgViewedArray': [0] * 10,
    'communicatorMsgArray': [0] * 5,
    'questTaskStatus': [0] * 10
}


@handlers.handler(XTPacket('party', 'partycookie'))
async def handle_party_cookie(p):
    cookie = await p.server.redis.hget('partycookie', p.id)
    if cookie is None:
        cookie = ujson.dumps(DefaultPartyCookie)
        await p.server.redis.hset('partycookie', p.id, cookie)
    else:
        cookie = cookie.decode('utf-8')
    await p.send_xt('partycookie', cookie)


@handlers.handler(XTPacket('party', 'msgviewed'))
@handlers.depends_on_packet(XTPacket('party', 'partycookie'))
async def handle_party_message_viewed(p, message_index: int):
    cookie = await p.server.redis.hget('partycookie', p.id)
    cookie = ujson.loads(cookie)

    cookie['msgViewedArray'][message_index] = 1

    await p.server.redis.hset('partycookie', p.id, ujson.dumps(cookie))


@handlers.handler(XTPacket('party', 'qcmsgviewed'))
@handlers.depends_on_packet(XTPacket('party', 'partycookie'))
async def handle_party_communicator_message_viewed(p, message_index: int):
    cookie = await p.server.redis.hget('partycookie', p.id)
    cookie = ujson.loads(cookie)

    cookie['communicatorMsgArray'][message_index] = 1

    await p.server.redis.hset('partycookie', p.id, ujson.dumps(cookie))


@handlers.handler(XTPacket('party', 'qtaskcomplete'))
@handlers.depends_on_packet(XTPacket('party', 'partycookie'))
async def handle_party_task_complete(p, task_index: int):
    cookie = await p.server.redis.hget('partycookie', p.id)
    cookie = ujson.loads(cookie)

    cookie['questTaskStatus'][task_index] = 1

    await p.server.redis.hset('partycookie', p.id, ujson.dumps(cookie))


@handlers.handler(XTPacket('party', 'qtupdate'))
@handlers.depends_on_packet(XTPacket('party', 'partycookie'))
@handlers.cooldown(5)
async def handle_party_task_update(p, coins: int):
    coins = min(coins, 10)
    await p.update(coins=p.coins + coins).apply()
    await p.send_xt('qtupdate', p.coins)
