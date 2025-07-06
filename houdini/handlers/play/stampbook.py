from houdini import handlers
from houdini.data.penguin import Penguin
from houdini.data.stamp import CoverItem, CoverStamp, PenguinStampCollection, Stamp, StampCollection
from houdini.handlers import Priority, XMLPacket, XTPacket
from houdini.handlers.play.navigation import handle_join_room, handle_join_server


async def get_book_cover_string(p, player_id):
    if player_id in p.server.penguins_by_id:
        player = p.server.penguins_by_id[player_id]
        cover_details = [player.book_color, player.book_highlight, player.book_pattern,
                         player.book_icon]
    else:
        cover_details = list(await Penguin.select('book_color', 'book_highlight', 'book_pattern', 'book_icon')
                             .where(Penguin.id == player_id).gino.first())

    cover_stamps = CoverStamp.query.where(CoverStamp.penguin_id == player_id)
    cover_items = CoverItem.query.where(CoverItem.penguin_id == player_id)

    async with p.server.db.transaction():
        async for stamp in cover_stamps.gino.iterate():
            cover_details.append(f'0|{stamp.stamp_id}|{stamp.x}|{stamp.y}|{stamp.rotation}|{stamp.depth}')
        async for item in cover_items.gino.iterate():
            item_type = 2 if p.server.items[item.item_id].is_award() else 1
            cover_details.append(f'{item_type}|{item.item_id}|{item.x}|{item.y}|{item.rotation}|{item.depth}')

    return '%'.join(map(str, cover_details))


async def get_player_stamps_string(p, player_id):
    if player_id in p.server.penguins_by_id:
        stamp_inventory = p.server.penguins_by_id[player_id].stamps
    else:
        stamp_inventory = await PenguinStampCollection.get_collection(player_id)
    return '|'.join(map(str, stamp_inventory.keys()))


@handlers.boot
async def stamps_load(server):
    server.stamps = await StampCollection.get_collection()
    server.logger.info(f'Loaded {len(server.stamps)} stamps')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_stamp_inventory(p):
    p.stamps = await PenguinStampCollection.get_collection(p.id)


@handlers.handler(XTPacket('j', 'js'), after=handle_join_server)
@handlers.allow_once
async def handle_get_stamps(p):
    await p.send_xt('gps', p.id, await get_player_stamps_string(p, p.id))


@handlers.handler(XTPacket('j', 'jr'), after=handle_join_room)
async def handle_add_mascot_stamp(p):
    if p.character is not None:
        character = p.server.characters[p.character]
        stamp = p.server.stamps[character.stamp_id]
        for penguin in p.room.penguins_by_id.values():
            await penguin.add_stamp(stamp)

    for penguin in p.room.penguins_by_id.values():
        if penguin.character is not None:
            character = p.server.characters[penguin.character]
            stamp = p.server.stamps[character.stamp_id]
            await p.add_stamp(stamp)


@handlers.handler(XTPacket('st', 'gps'))
@handlers.cooldown(1)
async def handle_get_player_stamps(p, player_id: int):
    stamps_string = p.server.cache.get(f'stamps.{player_id}')
    stamps_string = await get_player_stamps_string(p, player_id) if stamps_string is None else stamps_string
    p.server.cache.set(f'stamps.{player_id}', stamps_string)
    await p.send_xt('gps', player_id, stamps_string)


@handlers.handler(XTPacket('st', 'gmres'))
@handlers.cooldown(1)
async def handle_get_recent_stamps(p):
    recent_stamps = []
    for stamp in p.stamps.values():
        if stamp.recent:
            recent_stamps.append(stamp.stamp_id)
            await stamp.update(recent=False).apply()
    await p.send_xt('gmres', '|'.join(map(str, recent_stamps)))


@handlers.handler(XTPacket('st', 'sse'))
async def handle_stamp_add(p, stamp: Stamp):
    await p.add_stamp(stamp)


@handlers.handler(XTPacket('st', 'gsbcd'))
@handlers.cooldown()
async def handle_get_book_cover(p, player_id: int):
    book_string = p.server.cache.get(f'book.{player_id}')
    book_string = await get_book_cover_string(p, player_id) if book_string is None else book_string
    p.server.cache.set(f'book.{player_id}', book_string)
    await p.send_xt('gsbcd', book_string)


@handlers.handler(XTPacket('st', 'ssbcd'))
@handlers.cooldown()
async def handle_update_book_cover(p, color: int, highlight: int, pattern: int, icon: int, *cover):
    if not(1 <= int(color) <= 6 and 1 <= int(highlight) <= 18 and 0 <= int(pattern) <= 6 and 1 <= int(icon) <= 6
           and len(cover) <= 10):
        return

    await CoverItem.delete.where(CoverItem.penguin_id == p.id).gino.status()
    await CoverStamp.delete.where(CoverStamp.penguin_id == p.id).gino.status()

    stamp_tracker = set()
    inventory_tracker = set()

    cover_items = []
    cover_stamps = []
    for stamp in cover:
        stamp_array = stamp.split('|', 5)

        stamp_type, stamp_id, pos_x, pos_y, rotation, depth = map(int, stamp_array)

        if not (0 <= stamp_type <= 2 and 0 <= pos_x <= 600 and 0 <= pos_y <= 600 and
                0 <= rotation <= 360 and 0 <= depth <= 100):
            return

        if stamp_type == 0:
            if stamp_id in stamp_tracker or stamp_id not in p.stamps:
                return
            stamp_tracker.add(stamp_id)
            cover_stamps.append({'penguin_id': p.id, 'stamp_id': stamp_id, 'x': pos_x, 'y': pos_y,
                                 'rotation': rotation, 'depth': depth})
        elif stamp_type == 1 or stamp_type == 2:
            cover_item = p.server.items[stamp_id]
            if stamp_id in inventory_tracker or stamp_id not in p.inventory or \
                    (stamp_type == 1 and not cover_item.is_flag()) or \
                    (stamp_type == 2 and not cover_item.is_award()):
                return
            inventory_tracker.add(stamp_id)
            cover_items.append({'penguin_id': p.id, 'item_id': stamp_id, 'x': pos_x, 'y': pos_y,
                               'rotation': rotation, 'depth': depth})

    if cover_items:
        await CoverItem.insert().values(cover_items).gino.status()
    if cover_stamps:
        await CoverStamp.insert().values(cover_stamps).gino.status()

    await p.update(book_color=color,
                   book_highlight=highlight,
                   book_pattern=pattern,
                   book_icon=icon,
                   book_modified=1).apply()

    stringified_cover = '%'.join(cover)
    p.server.cache.set(f'book.{p.id}', f'{color}%{highlight}%{pattern}%{icon}%{stringified_cover}')
