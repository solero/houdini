from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_player_room, handle_join_room


@handlers.handler(XTPacket('a', 'gt'))
async def handle_get_waddle_population(p):
    await p.send_xt('gt', '%'.join(f'{table.id}|{",".join(penguin.safe_name for penguin in table.penguins)}'
                                   for table in p.room.tables.values()))


@handlers.handler(XTPacket('a', 'jt'))
async def handle_join_table(p, table_id: int):
    try:
        table = p.room.tables[table_id]
        await table.add_penguin(p)
    except KeyError:
        p.logger.warn(f'{p.username} tried to join a table that doesn\'t exist')


@handlers.handler(XTPacket('a', 'lt'))
async def handle_leave_table(p):
    if p.table:
        await p.table.remove_penguin(p)


@handlers.handler(XTPacket('j', 'jr'), after=handle_join_room)
async def handle_join_room_table(p):
    if p.table:
        await p.table.remove_penguin(p)


@handlers.handler(XTPacket('j', 'jp'), after=handle_join_player_room)
async def handle_join_player_room_table(p):
    if p.table:
        await p.table.remove_penguin(p)


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_table(p):
    if p.table:
        await p.table.remove_penguin(p)
