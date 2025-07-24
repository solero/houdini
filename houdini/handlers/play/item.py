import operator
import calendar

from houdini import handlers
from houdini.data.item import Item, ItemCollection, PenguinItemCollection
from houdini.data.permission import PenguinPermissionCollection
from houdini.data.plugin import PenguinAttributeCollection
from houdini.handlers import Priority, XMLPacket, XTPacket


async def get_pin_string(p, player_id):
    if player_id in p.server.penguins_by_id:
        inventory = p.server.penguins_by_id[player_id].inventory
    else:
        inventory = await PenguinItemCollection.get_collection(player_id)

    def is_free_pin(pin):
        return p.server.items[pin].is_flag() and p.server.items[pin].cost == 0
    free_pins = (p.server.items[pin] for pin in inventory.keys() if is_free_pin(pin))
    pins = sorted(free_pins, key=operator.attrgetter('release_date'))

    def get_string(pin):
        unix = int(calendar.timegm(pin.release_date.timetuple())) - 86400
        return f'{pin.id}|{unix}|{int(pin.member)}'
    return '%'.join(get_string(pin) for pin in pins)


async def get_awards_string(p, player_id):
    if player_id in p.server.penguins_by_id:
        inventory = p.server.penguins_by_id[player_id].inventory
    else:
        inventory = await PenguinItemCollection.get_collection(player_id)

    awards = [str(award) for award in inventory.keys() if p.server.items[award].is_award()]
    return '|'.join(awards)


@handlers.boot
async def items_load(server):
    server.items = await ItemCollection.get_collection()
    server.logger.info(f'Loaded {len(server.items)} clothing items')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_inventory(p):
    p.inventory = await PenguinItemCollection.get_collection(p.id)
    p.permissions = await PenguinPermissionCollection.get_collection(p.id)
    p.attributes = await PenguinAttributeCollection.get_collection(p.id)

    if p.color is not None and p.color not in p.inventory:
        await p.inventory.insert(item_id=p.color)

    default_items = p.server.items.legacy_inventory if p.is_legacy_client else \
        p.server.items.vanilla_inventory
    for default_item in default_items:
        if default_item.id not in p.inventory:
            await p.inventory.insert(item_id=default_item.id)


@handlers.handler(XTPacket('i', 'gi'))
@handlers.allow_once
async def handle_get_inventory(p):
    await p.send_xt('gi', *p.inventory.keys())


@handlers.handler(XTPacket('i', 'ai'))
@handlers.depends_on_packet(XTPacket('i', 'gi'))
async def handle_buy_inventory(p, item: Item):
    if item is None:
        return await p.send_error(402)

    if item.id in p.inventory:
        return await p.send_error(400)

    if p.coins < item.cost:
        return await p.send_error(401)

    if item.tour:
        await p.add_inbox(p.server.postcards[126])

    await p.add_inventory(item)


@handlers.handler(XTPacket('i', 'qpp'))
@handlers.depends_on_packet(XTPacket('i', 'gi'))
@handlers.cooldown(1)
async def handle_query_player_pins(p, player_id: int):
    string = p.server.cache.get(f'pins.{player_id}')
    string = await get_pin_string(p, player_id) if string is None else string
    p.server.cache.set(f'pins.{player_id}', string)
    await p.send_xt('qpp', string)


@handlers.handler(XTPacket('i', 'qpa'))
@handlers.depends_on_packet(XTPacket('i', 'gi'))
@handlers.cooldown(1)
async def handle_query_player_awards(p, player_id: int):
    string = p.server.cache.get(f'awards.{player_id}')
    string = await get_awards_string(p, player_id) if string is None else string
    p.server.cache.set(f'awards.{player_id}', string)
    await p.send_xt('qpa', player_id, string)
