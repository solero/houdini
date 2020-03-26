from houdini import handlers
from houdini.data.room import Room
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_player_room, handle_join_room


@handlers.handler(XTPacket('gw', ext='z'))
async def handle_get_waddle_population(p):
    await p.send_xt('gw', '%'.join(f'{waddle.id}|{",".join(penguin.safe_name if penguin else str() for penguin in waddle.penguins)}'
                                   for waddle in p.room.waddles.values()))


@handlers.handler(XTPacket('jw', ext='z'))
async def handle_join_waddle(p, waddle_id: int):
    try:
        waddle = p.room.waddles[waddle_id]
        await waddle.add_penguin(p)
    except KeyError:
        p.logger.warn(f'{p.username} tried to join a waddle that doesn\'t exist')


@handlers.handler(XTPacket('lw', ext='z'))
async def handle_leave_waddle(p):
    if p.waddle:
        await p.waddle.remove_penguin(p)


@handlers.handler(XTPacket('j', 'jr'), after=handle_join_room)
async def handle_join_room_waddle(p):
    if p.waddle:
        await p.waddle.remove_penguin(p)


@handlers.handler(XTPacket('j', 'jp'), after=handle_join_player_room)
async def handle_join_player_room_waddle(p):
    if p.waddle:
        await p.waddle.remove_penguin(p)


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_waddle(p):
    if p.waddle:
        await p.waddle.remove_penguin(p)
