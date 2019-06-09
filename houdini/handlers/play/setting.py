from houdini import handlers
from houdini.handlers import XTPacket

from houdini.converters import ItemConverter

# TODO: handle if the object item is None check better?

@handlers.handler(XTPacket('s', 'upc'))
@handlers.cooldown(1)
async def handle_send_update_player_colour(p, item: ItemConverter):
    if item.id in p.data.inventory and item.is_color():
        await p.data.update(color=item.id).apply()
        await p.room.send_xt('upc', p.data.id, item.id)

@handlers.handler(XTPacket('s', 'uph'))
@handlers.cooldown(1)
async def handle_send_update_player_head(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_head():
        await p.data.update(head=item.id).apply()
        await p.room.send_xt('uph', p.data.id, item.id)
    else:
        await p.data.update(head=None).apply()
        await p.room.send_xt('uph', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upf'))
@handlers.cooldown(1)
async def handle_send_update_player_face(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_face():
        await p.data.update(face=item.id).apply()
        await p.room.send_xt('upf', p.data.id, item.id)
    else:
        await p.data.update(face=None).apply()
        await p.room.send_xt('upf', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upn'))
@handlers.cooldown(1)
async def handle_send_update_player_neck(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_neck():
        await p.data.update(neck=item.id).apply()
        await p.room.send_xt('upn', p.data.id, item.id)
    else:
        await p.data.update(neck=None).apply()
        await p.room.send_xt('upn', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upb'))
@handlers.cooldown(1)
async def handle_send_update_player_body(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_body():
        await p.data.update(body=item.id).apply()
        await p.room.send_xt('upb', p.data.id, item.id)
    else:
        await p.data.update(body=None).apply()
        await p.room.send_xt('upb', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upa'))
@handlers.cooldown(1)
async def handle_send_update_player_hand(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_hand():
        await p.data.update(hand=item.id).apply()
        await p.room.send_xt('upa', p.data.id, item.id)
    else:
        await p.data.update(hand=None).apply()
        await p.room.send_xt('upa', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upe'))
@handlers.cooldown(1)
async def handle_send_update_player_feet(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_feet():
        await p.data.update(feet=item.id).apply()
        await p.room.send_xt('upe', p.data.id, item.id)
    else:
        await p.data.update(feet=None).apply()
        await p.room.send_xt('upe', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upl'))
@handlers.cooldown(1)
async def handle_send_update_player_flag(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_flag():
        await p.data.update(flag=item.id).apply()
        await p.room.send_xt('upl', p.data.id, item.id)
    else:
        await p.data.update(flag=None).apply()
        await p.room.send_xt('upl', p.data.id, 0)

@handlers.handler(XTPacket('s', 'upp'))
@handlers.cooldown(1)
async def handle_send_update_player_photo(p, item: ItemConverter):
    if item is not None and item.id in p.data.inventory and item.is_photo():
        await p.data.update(photo=item.id).apply()
        await p.room.send_xt('upp', p.data.id, item.id)
    else:
        await p.data.update(photo=None).apply()
        await p.room.send_xt('upp', p.data.id, 0)
