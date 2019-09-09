from houdini import handlers
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('p', 'getdigcooldown'), pre_login=True)
async def handle_get_dig_cooldown(p):
    await p.send_xt('getdigcooldown', 1)


@handlers.handler(XTPacket('p', 'checkpufflename'))
async def handle_check_puffle_name_with_response(p, puffle_name):
    name_ok = puffle_name.isalnum()
    await p.send_xt('checkpufflename', puffle_name, int(name_ok))
