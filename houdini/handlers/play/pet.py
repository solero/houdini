from houdini import handlers
from houdini.handlers import XTPacket
from houdini.constants import ClientType


@handlers.handler(XTPacket('p', 'getdigcooldown'), pre_login=True)
async def handle_get_dig_cooldown(p):
    await p.send_xt('getdigcooldown', 1)


@handlers.handler(XTPacket('p', 'checkpufflename'))
async def handle_check_puffle_name_with_response(p, puffle_name):
    name_ok = puffle_name.isalnum()
    await p.send_xt('checkpufflename', puffle_name, int(name_ok))


@handlers.handler(XTPacket('p', 'pg'), client=ClientType.Vanilla)
async def handle_get_player_puffles(p, penguin_id: int, room_type: str):
    await p.send_xt('pg')


@handlers.handler(XTPacket('p', 'pg'), client=ClientType.Legacy)
async def handle_get_player_puffles_legacy(p, penguin_id: int):
    await p.send_xt('pg')
