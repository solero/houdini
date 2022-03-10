from houdini.handlers import XTPacket
from houdini import handlers
from houdini.data.item import PenguinItemCollection
from houdini.data.stamp import PenguinStampCollection
from houdini.handlers.play.stampbook import get_player_stamps_string

@handlers.handler(XTPacket('i#ngi'))
@handlers.cooldown(5)
async def ninja_get_inventory(p):
    p.inventory = await PenguinItemCollection.get_collection(p.id)
    await p.send_xt('gi', *p.inventory.keys())

@handlers.handler(XTPacket('st#ngps'))
@handlers.cooldown(5)
async def ninja_get_penguin_stamps(p):
    p.stamps = await PenguinStampCollection.get_collection(p.id)
    await p.send_xt('gps', p.id, await get_player_stamps_string(p, p.id))
