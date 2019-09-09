from houdini import handlers
from houdini.handlers import XTPacket
from houdini.constants import ClientType


@handlers.handler(XTPacket('t', 'at'))
async def handle_open_book(p, toy_id: int):
    p.toy = toy_id
    await p.room.send_xt('at', p.data.id, toy_id)


@handlers.handler(XTPacket('t', 'rt'))
async def handle_close_book(p):
    p.toy = None
    await p.room.send_xt('rt', p.data.id)


@handlers.handler(XTPacket('j', 'jr'), client=ClientType.Legacy)
async def handle_join_room_toy(p):
    for penguin in p.room.penguins_by_id.values():
        if penguin.toy is not None:
            await p.send_xt('at', penguin.data.id, penguin.toy)


@handlers.handler(XTPacket('j', 'crl'), client=ClientType.Vanilla)
@handlers.depends_on_packet(XTPacket('j', 'jr'))
async def handle_client_room_loaded_toy(p):
    for penguin in p.room.penguins_by_id.values():
        if penguin.toy is not None:
            await p.send_xt('at', penguin.data.id, penguin.toy)
