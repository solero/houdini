from houdini import handlers
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('gw', ext='z'))
async def handle_get_waddle_population(p):
    await p.send_xt('gw', '%'.join(f'{waddle.id}|{",".join(penguin.safe_name for penguin in waddle.penguins)}'
                                   for waddle in p.room.waddles.values()))


@handlers.handler(XTPacket('jw', ext='z'))
async def handle_join_waddle(p, waddle_id: int):
    try:
        waddle = p.room.waddles[waddle_id]
        await waddle.add(p)
    except KeyError:
        pass


@handlers.handler(XTPacket('lw', ext='z'))
async def handle_leave_waddle(p):
    if p.waddle:
        await p.waddle.remove(p)
