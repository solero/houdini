from houdini import handlers
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('i', 'gi'))
@handlers.allow_once
async def handle_get_inventory(p):
    await p.send_xt('gi', *p.data.inventory.keys())
