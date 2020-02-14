from houdini import handlers
from houdini.handlers import XMLPacket, XTPacket, Priority
from houdini.data.item import Item, ItemCollection, PenguinItemCollection
from houdini.data.permission import PenguinPermissionCollection

import time
from aiocache import cached
import operator


def get_pin_string_key(_, p, player_id):
    return f'pins.{player_id}'


def get_awards_string_key(_, p, player_id):
    return f'awards.{player_id}'


@cached(alias='default', key_builder=get_pin_string_key)
async def get_pin_string(p, player_id):
    if player_id in p.server.penguins_by_id:
        inventory = p.server.penguins_by_id[player_id].inventory
    else:
        inventory = await PenguinItemCollection.get_collection(player_id)

    def get_string(pin):
        unix = int(time.mktime(pin.release_date.timetuple()))
        return f'{pin.id}|{unix}|{int(pin.member)}'

    pins = sorted((p.server.items[pin] for pin in inventory.keys()
                   if (p.server.items[pin].is_flag() and p.server.items[pin].cost == 0)),
                  key=operator.attrgetter('release_date'))
    return '%'.join(get_string(pin) for pin in pins)


@cached(alias='default', key_builder=get_awards_string_key)
async def get_awards_string(p, player_id):
    if player_id in p.server.penguins_by_id:
        inventory = p.server.penguins_by_id[player_id].inventory
    else:
        inventory = await PenguinItemCollection.get_collection(player_id)

    awards = [str(award) for award in inventory.keys() if p.server.items[award].is_award()]
    return '%'.join(awards)


@handlers.boot
async def items_load(server):
    server.items = await ItemCollection.get_collection()
    server.logger.info(f'Loaded {len(server.items)} clothing items')

@handlers.allow_once
async def load_inventory(p):
    p.inventory = await PenguinItemCollection.get_collection(p.id)
    p.permissions = await PenguinPermissionCollection.get_collection(p.id)


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
    await p.send_xt('qpp', await get_pin_string(p, player_id))


@handlers.handler(XTPacket('i', 'qpa'))
@handlers.depends_on_packet(XTPacket('i', 'gi'))
@handlers.cooldown(1)
async def handle_query_player_awards(p, player_id: int):
    await p.send_xt('qpa', await get_awards_string(p, player_id))
