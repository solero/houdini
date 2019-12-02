from houdini import handlers
from houdini.handlers import XTPacket

from houdini.data.item import Item


@handlers.handler(XTPacket('s', 'upc'))
@handlers.cooldown(1)
async def handle_send_update_player_colour(p, item: Item):
    if item.id in p.inventory and item.is_color():
        await p.set_color(item)


@handlers.handler(XTPacket('s', 'uph'))
@handlers.cooldown(1)
async def handle_send_update_player_head(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_head()):
        await p.set_head(item)


@handlers.handler(XTPacket('s', 'upf'))
@handlers.cooldown(1)
async def handle_send_update_player_face(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_face()):
        await p.set_face(item)


@handlers.handler(XTPacket('s', 'upn'))
@handlers.cooldown(1)
async def handle_send_update_player_neck(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_neck()):
        await p.set_neck(item)


@handlers.handler(XTPacket('s', 'upb'))
@handlers.cooldown(1)
async def handle_send_update_player_body(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_body()):
        await p.set_body(item)


@handlers.handler(XTPacket('s', 'upa'))
@handlers.cooldown(1)
async def handle_send_update_player_hand(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_hand()):
        await p.set_hand(item)


@handlers.handler(XTPacket('s', 'upe'))
@handlers.cooldown(1)
async def handle_send_update_player_feet(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_feet()):
        await p.set_feet(item)


@handlers.handler(XTPacket('s', 'upl'))
@handlers.cooldown(1)
async def handle_send_update_player_flag(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_flag()):
        await p.set_flag(item)


@handlers.handler(XTPacket('s', 'upp'))
@handlers.cooldown(1)
async def handle_send_update_player_photo(p, item: Item):
    if item is None or (item.id in p.inventory and item.is_photo()):
        await p.set_photo(item)
