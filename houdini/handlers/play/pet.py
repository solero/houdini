from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_server
from houdini.constants import ClientType

from houdini.data.pet import PenguinPuffleCollection, PenguinPuffleItemCollection


@handlers.handler(XTPacket('j', 'js'), after=handle_join_server)
@handlers.player_attribute(joined_world=True)
@handlers.allow_once
async def load_pet_inventory(p):
    p.puffles = await PenguinPuffleCollection.get_collection(p.id)
    p.puffle_items = await PenguinPuffleItemCollection.get_collection(p.id)


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
