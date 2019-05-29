from houdini import handlers
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('u', 'h'))
@handlers.cooldown(59)
async def handle_heartbeat(p):
    await p.send_xt('h')
