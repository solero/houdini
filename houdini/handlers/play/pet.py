from houdini import handlers
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('p', 'getdigcooldown'), pre_login=True)
async def handle_get_dig_cooldown(p):
    await p.send_xt('getdigcooldown', 1)
