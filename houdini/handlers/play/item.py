from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.item import Item


@handlers.handler(XTPacket('i', 'gi'))
@handlers.allow_once
async def handle_get_inventory(p):
    await p.send_xt('gi', *p.data.inventory.keys())


@handlers.handler(XTPacket('i', 'ai'))
@handlers.depends_on_packet(XTPacket('i', 'gi'))
@handlers.cooldown(1)
async def handle_buy_inventory(p, item: Item):
    if item.id not in p.server.items:
        return await p.send_error(402)

    if item.id in p.data.inventory:
        return await p.send_error(400)

    if item.epf:
        return await p.add_inbox(p.server.postcards[126])

    if p.data.coins < item.cost:
        return await p.send_error(401)

    await p.add_inventory(item)
