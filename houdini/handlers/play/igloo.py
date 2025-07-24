import itertools
import time
from datetime import datetime, timedelta

import ujson
from sqlalchemy.dialects.postgresql import insert

from houdini import handlers
from houdini.constants import ClientType, StatusField
from houdini.converters import SeparatorConverter
from houdini.data import db
from houdini.data.game import PenguinGameData
from houdini.data.igloo import Flooring, FlooringCollection, Furniture, FurnitureCollection, Igloo, IglooCollection, \
    IglooFurniture, IglooLike, Location, LocationCollection, PenguinFlooringCollection, PenguinFurnitureCollection, \
    PenguinIglooCollection, PenguinLocationCollection
from houdini.data.penguin import Penguin
from houdini.data.room import PenguinIglooRoom, PenguinIglooRoomCollection
from houdini.handlers import Priority, XMLPacket, XTPacket
from houdini.handlers.play.navigation import handle_join_server


async def get_layout_furniture(p, igloo_id):
    igloo_furniture = IglooFurniture.query.where(IglooFurniture.igloo_id == igloo_id).gino
    async with p.server.db.transaction():
        furniture_string = ','.join([f'{furniture.furniture_id}|{furniture.x}|{furniture.y}|'
                                    f'{furniture.rotation}|{furniture.frame}'
                                     async for furniture in igloo_furniture.iterate()])
    return furniture_string


async def get_igloo(penguin_id):
    return await PenguinIglooRoom.load(parent=Penguin.on(Penguin.igloo == PenguinIglooRoom.id))\
        .where(PenguinIglooRoom.penguin_id == penguin_id).gino.first()


async def get_active_igloo_string(p, penguin_id):
    igloo = await get_igloo(penguin_id)
    furniture_string = p.server.cache.get(f'layout_furniture.{igloo.id}')
    furniture_string = await get_layout_furniture(p, igloo.id) if furniture_string is None else furniture_string
    like_count = p.server.cache.get(f'layout_like_count.{igloo.id}')
    like_count = await get_layout_like_count(igloo.id) if like_count is None else like_count

    p.server.cache.set(f'layout_furniture.{igloo.id}', furniture_string)
    p.server.cache.set(f'layout_like_count.{igloo.id}', like_count)
    return f'{igloo.id}:1:0:{int(igloo.locked)}:{igloo.music}:{igloo.flooring}:' \
           f'{igloo.location}:{igloo.type}:{like_count}:{furniture_string}'


async def get_legacy_igloo_string(p, penguin_id):
    igloo = await get_igloo(penguin_id)
    furniture_string = p.server.cache.get(f'layout_furniture.{igloo.id}')
    furniture_string = await get_layout_furniture(p, igloo.id) if furniture_string is None else furniture_string
    p.server.cache.set(f'layout_furniture.{igloo.id}', furniture_string)
    return f'{igloo.type}%{igloo.music}%{igloo.flooring}%{furniture_string}'


async def get_all_igloo_layouts(p):
    layout_details = []
    for slot, igloo in enumerate(p.igloo_rooms.values()):
        furniture_string = p.server.cache.get(f'layout_furniture.{igloo.id}')
        furniture_string = await get_layout_furniture(p, igloo.id) if furniture_string is None else furniture_string
        like_count = p.server.cache.get(f'layout_like_count.{igloo.id}')
        like_count = await get_layout_like_count(igloo.id) if like_count is None else like_count

        p.server.cache.set(f'layout_furniture.{igloo.id}', furniture_string)
        p.server.cache.set(f'layout_like_count.{igloo.id}', like_count)
        igloo_details = f'{igloo.id}:{slot}:0:{int(igloo.locked)}:{igloo.music}:{igloo.flooring}' \
                        f':{igloo.location}:{igloo.type}:{like_count}:{furniture_string}'
        layout_details.append(igloo_details)
    return '%'.join(layout_details)


async def get_layout_like_count(igloo_id):
    layout_like_count = await db.select([db.func.sum(IglooLike.count)])\
        .where(IglooLike.igloo_id == igloo_id).gino.scalar()
    return layout_like_count or 0


async def create_first_igloo(p, penguin_id):
    igloo = await PenguinIglooRoom.query.where(PenguinIglooRoom.penguin_id == penguin_id).gino.scalar()
    if igloo is None:
        if penguin_id in p.server.penguins_by_id:
            penguin = p.server.penguins_by_id[penguin_id]
            igloo = await penguin.igloo_rooms.insert(penguin_id=penguin_id, type=1, flooring=0, location=1)
            await penguin.update(igloo=igloo.id).apply()
        else:
            igloo = await PenguinIglooRoom.create(penguin_id=penguin_id, type=1, flooring=0, location=1)
            await Penguin.update.values(igloo=igloo.id)\
                .where(Penguin.id == penguin_id).gino.status()


async def save_igloo_furniture(p, furniture_list=None):
    await IglooFurniture.delete.where(IglooFurniture.igloo_id == p.igloo).gino.status()

    if furniture_list:
        furniture_tracker = {}
        furniture = []
        for furniture_string in itertools.islice(furniture_list, 0, 100):
            furniture_id, x, y, rotation, frame = map(int, furniture_string.split('|'))

            if furniture_id not in p.furniture:
                return False

            furniture_tracker[furniture_id] = furniture_tracker.get(furniture_id, 0) + 1

            if furniture_tracker[furniture_id] > p.furniture[furniture_id].quantity:
                return False

            furniture.append({
                'igloo_id': p.igloo,
                'furniture_id': furniture_id,
                'x': x, 'y': y,
                'frame': frame,
                'rotation': rotation
            })

        await IglooFurniture.insert().values(furniture).gino.status()
    return True


@handlers.boot
async def igloos_load(server):
    server.igloos = await IglooCollection.get_collection()
    server.furniture = await FurnitureCollection.get_collection()
    server.locations = await LocationCollection.get_collection()
    server.flooring = await FlooringCollection.get_collection()

    server.logger.info(f'Loaded {len(server.igloos)} igloos')
    server.logger.info(f'Loaded {len(server.furniture)} furniture items')
    server.logger.info(f'Loaded {len(server.locations)} igloo locations')
    server.logger.info(f'Loaded {len(server.flooring)} igloo flooring')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_igloo_inventory(p):
    p.igloos = await PenguinIglooCollection.get_collection(p.id)
    p.igloo_rooms = await PenguinIglooRoomCollection.get_collection(p.id)
    p.furniture = await PenguinFurnitureCollection.get_collection(p.id)
    p.flooring = await PenguinFlooringCollection.get_collection(p.id)
    p.locations = await PenguinLocationCollection.get_collection(p.id)

    default_igloos = p.server.igloos.legacy_inventory if p.is_legacy_client else \
        p.server.igloos.vanilla_inventory
    for default_item in default_igloos:
        if default_item.id not in p.igloos:
            await p.igloos.insert(igloo_id=default_item.id)

    default_locations = p.server.locations.legacy_inventory if p.is_legacy_client else \
        p.server.locations.vanilla_inventory
    for default_item in default_locations:
        if default_item.id not in p.locations:
            await p.locations.insert(location_id=default_item.id)

    default_flooring = p.server.flooring.legacy_inventory if p.is_legacy_client else \
        p.server.flooring.vanilla_inventory
    for default_item in default_flooring:
        if default_item.id not in p.flooring:
            await p.flooring.insert(flooring_id=default_item.id)

    default_furniture = p.server.furniture.legacy_inventory if p.is_legacy_client else \
        p.server.furniture.vanilla_inventory
    for default_item in default_furniture:
        if default_item.id not in p.furniture:
            await p.furniture.insert(furniture_id=default_item.id)


@handlers.handler(XTPacket('g', 'gm'))
@handlers.cooldown(1)
async def handle_get_igloo_details(p, penguin_id: int):
    await create_first_igloo(p, penguin_id)
    cache_key = f'active_igloo.{penguin_id}' if p.is_vanilla_client else f'legacy_igloo.{penguin_id}'
    igloo_string_method = get_active_igloo_string if p.is_vanilla_client else get_legacy_igloo_string
    igloo_string = p.server.cache.get(cache_key)
    igloo_string = await igloo_string_method(p, penguin_id) if igloo_string is None else igloo_string
    p.server.cache.set(cache_key, igloo_string)
    await p.send_xt('gm', penguin_id, igloo_string)


@handlers.handler(XTPacket('g', 'gail'), client=ClientType.Vanilla)
async def handle_get_all_igloo_layouts(p):
    await p.status_field_set(StatusField.OpenedIglooViewer)
    layouts_string = p.server.cache.get(f'igloo_layouts.{p.id}')
    layouts_string = await get_all_igloo_layouts(p) if layouts_string is None else layouts_string
    p.server.cache.set(f'igloo_layouts.{p.id}', layouts_string)
    await p.send_xt('gail', p.id, 0, layouts_string)


@handlers.handler(XTPacket('g', 'gail'), client=ClientType.Vanilla, after=handle_get_all_igloo_layouts)
async def handle_get_all_igloo_likes(p):
    total = 0
    like_strings = []
    for igloo in p.igloo_rooms.values():
        like_count = p.server.cache.get(f'layout_like_count.{igloo.id}')
        like_count = await get_layout_like_count(igloo.id) if like_count is None else like_count
        p.server.cache.set(f'layout_like_count.{igloo.id}', like_count)
        total += like_count
        like_strings.append(f'{igloo.id}|{like_count}')
    await p.send_xt('gaili', total, ','.join(like_strings))


@handlers.handler(XTPacket('g', 'ag'))
async def handle_buy_flooring(p, flooring: Flooring):
    if flooring is None:
        return await p.send_error(402)

    if p.is_vanilla_client:
        if flooring.id in p.flooring:
            return await p.send_error(501)

        if p.coins < flooring.cost:
            return await p.send_error(401)

        await p.add_flooring(flooring)
    else:
        igloo = p.igloo_rooms[p.igloo]

        await igloo.update(flooring=flooring.id).apply()
        await p.update(coins=p.coins - flooring.cost).apply()

        await p.send_xt('ag', flooring.id, p.coins)

        p.server.cache.delete(f'active_igloo.{p.id}')
        p.server.cache.delete(f'legacy_igloo.{p.id}')
        p.server.cache.delete(f'igloo_layouts.{p.id}')


@handlers.handler(XTPacket('g', 'aloc'), client=ClientType.Vanilla)
async def handle_buy_igloo_location(p, location: Location):
    if location is None:
        return await p.send_error(402)

    if location.id in p.locations:
        return await p.send_error(502)

    if p.coins < location.cost:
        return await p.send_error(401)

    await p.add_location(location)


@handlers.handler(XTPacket('g', 'au'))
async def handle_buy_igloo_type(p, igloo: Igloo):
    if igloo is None:
        return await p.send_error(402)

    if igloo.id in p.igloos:
        return await p.send_error(500)

    if p.coins < igloo.cost:
        return await p.send_error(401)

    await p.add_igloo(igloo)


@handlers.handler(XTPacket('g', 'af'))
async def handle_buy_furniture(p, furniture: Furniture):
    if furniture is None:
        return await p.send_error(402)

    if p.coins < furniture.cost:
        return await p.send_error(401)
    
    if furniture.id in p.furniture:
            penguin_furniture = p.furniture[furniture.id]
            if penguin_furniture.quantity >= furniture.max_quantity:
                return await p.send_error(403)

    await p.add_furniture(furniture)


@handlers.handler(XTPacket('g', 'uic'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_update_igloo_configuration(p, igloo_id: int, igloo_type_id: int, flooring_id: int, location_id: int,
                                            music_id: int, furniture_data):
    if p.room.igloo and p.room.penguin_id == p.id and igloo_id in p.igloo_rooms:
        igloo = p.igloo_rooms[igloo_id]

        await p.update(igloo=igloo_id).apply()
        p.server.igloos_by_penguin_id[p.id] = igloo

        furniture_list = furniture_data.split(',') if furniture_data else None
        save_res = await save_igloo_furniture(p, furniture_list)

        if save_res:
            if not igloo_type_id or igloo_type_id in p.igloos\
                    and not flooring_id or flooring_id in p.flooring\
                    and not location_id or location_id in p.locations:
                await igloo.update(
                    type=igloo_type_id,
                    flooring=flooring_id,
                    location=location_id,
                    music=music_id
                ).apply()

            like_count = p.server.cache.get(f'layout_like_count.{igloo.id}')
            like_count = await get_layout_like_count(igloo.id) if like_count is None else like_count
            p.server.cache.set(f'layout_like_count.{igloo.id}', like_count)
            active_igloo_string = f'{igloo.id}:1:0:{int(igloo.locked)}:{igloo.music}:{igloo.flooring}:' \
                                  f'{igloo.location}:{igloo.type}:{like_count}:{furniture_data}'
            await p.room.send_xt('uvi', p.id, active_igloo_string)

            p.server.cache.set(f'layout_furniture.{igloo.id}', furniture_data)
            p.server.cache.set(f'active_igloo.{p.id}', active_igloo_string)
            p.server.cache.delete(f'legacy_igloo.{p.id}')
            p.server.cache.delete(f'igloo_layouts.{p.id}')

            if len(furniture_list) >= 99:
                await p.add_stamp(p.server.stamps[23])


@handlers.handler(XTPacket('g', 'ur'), client=ClientType.Legacy)
@handlers.cooldown(1)
async def handle_save_igloo_furniture(p, *furniture_data):
    save_res = await save_igloo_furniture(p, furniture_data)

    if save_res:
        p.server.cache.set(f'layout_furniture.{p.igloo}', ','.join(furniture_data))
        p.server.cache.delete(f'legacy_igloo.{p.id}')


_slot_converter = SeparatorConverter(separator=',', mapper=str)


@handlers.handler(XTPacket('g', 'uiss'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_update_igloo_slot_summary(p, igloo_id: int, slot_summary: _slot_converter):
    if p.room.igloo and p.room.penguin_id == p.id and igloo_id in p.igloo_rooms:
        igloo = p.igloo_rooms[igloo_id]

        if p.id in p.server.open_igloos_by_penguin_id:
            del p.server.open_igloos_by_penguin_id[p.id]

        if igloo_id != p.room.id:
            await p.update(igloo=igloo_id).apply()
            p.server.igloos_by_penguin_id[p.id] = igloo

            igloo.penguins_by_id = p.room.penguins_by_id
            igloo.penguins_by_username = p.room.penguins_by_username
            igloo.penguins_by_character_id = p.room.penguins_by_character_id
            p.room.penguins_by_id = {}
            p.room.penguins_by_username = {}
            p.room.penguins_by_character_id = {}

            for penguin in igloo.penguins_by_id.values():
                penguin.room = igloo

        for slot in slot_summary:
            igloo_id, locked = map(int, slot.split('|'))
            igloo = p.igloo_rooms[igloo_id]

            if igloo_id == p.igloo:
                if not locked:
                    await p.status_field_set(StatusField.ActiveIglooLayoutOpenFlag)
                    p.server.open_igloos_by_penguin_id[p.id] = igloo

                if igloo.locked != bool(locked):
                    await igloo.update(locked=bool(locked)).apply()

        p.server.cache.delete(f'active_igloo.{p.id}')
        p.server.cache.delete(f'legacy_igloo.{p.id}')
        p.server.cache.delete(f'igloo_layouts.{p.id}')

        active_igloo_string = await get_active_igloo_string(p, p.id)
        await p.room.send_xt('uvi', p.id, active_igloo_string)


@handlers.handler(XTPacket('j', 'js'), after=handle_join_server, client=ClientType.Vanilla)
async def handle_add_igloo_map(p):
    if p.igloo is not None:
        igloo = p.igloo_rooms[p.igloo]

        if not igloo.locked:
            p.server.open_igloos_by_penguin_id[p.id] = igloo


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_remove_igloo_map(p):
    if p.id in p.server.open_igloos_by_penguin_id:
        del p.server.open_igloos_by_penguin_id[p.id]


@handlers.handler(XTPacket('g', 'pio'), client=ClientType.Vanilla)
async def handle_is_player_igloo_open(p, penguin_id: int):
    await p.send_xt('pio', int(penguin_id in p.server.open_igloos_by_penguin_id or p.moderator))


@handlers.handler(XTPacket('g', 'al'), client=ClientType.Vanilla)
async def handle_add_igloo_layout(p):
    if len(p.igloo_rooms) < 4:
        igloo = await p.igloo_rooms.insert(penguin_id=p.id, type=1, flooring=0, location=1)
        slot_id = len(p.igloo_rooms)

        await p.send_xt('al', p.id, f'{igloo.id}:{slot_id}:0:{int(igloo.locked)}:{igloo.music}:{igloo.flooring}:'
                                    f'{igloo.location}:{igloo.type}:0:')


@handlers.handler(XTPacket('g', 'gili'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_get_igloo_like_by(p, pagination_start: int, pagination_end: int):
    if p.room.igloo:
        like_count = p.server.cache.get(f'layout_like_count.{p.room.id}')
        like_count = await get_layout_like_count(p.room.id) if like_count is None else like_count
        p.server.cache.set(f'layout_like_count.{p.room.id}', like_count)

        liked_by = IglooLike.query.where(IglooLike.igloo_id == p.room.id). \
            limit(pagination_end - pagination_start).offset(pagination_start).gino

        async with p.server.db.transaction():
            like_collection = {
                'likedby': {
                    'counts': {
                        'count': like_count,
                        'maxCount': like_count,
                        'accumCount': like_count
                    },
                    'IDs': [
                        {
                            'id': like.player_id,
                            'time': int(time.mktime(like.date.timetuple())),
                            'count': like.count,
                            'isFriend': like.player_id in p.buddies
                        } async for like in liked_by.iterate()
                    ]
                },
            }

        await p.send_xt('gili', p.room.id, 200, ujson.dumps(like_collection))


@handlers.handler(XTPacket('g', 'cli'), client=ClientType.Vanilla)
async def handle_can_like_igloo(p):
    last_like = await db.select([IglooLike.date]).where((IglooLike.igloo_id == p.room.id)
                                                        & (IglooLike.player_id == p.id)).gino.scalar()

    time_elapsed = datetime.now()
    if last_like is not None:
        time_elapsed = datetime.now() - last_like

    can_like = ujson.dumps({'canLike': True, 'periodicity': 'ScheduleDaily', 'nextLike_msecs': 0})

    if last_like is None or time_elapsed > timedelta(1):
        await p.send_xt('cli', p.room.id, 200, can_like)
    else:
        next_like = int((timedelta(1) - time_elapsed).total_seconds() * 1000)
        await p.send_xt('cli', p.room.id, 200, ujson.dumps({'canLike': False, 'periodicity': 'ScheduleDaily',
                                                            'nextLike_msecs': next_like}))


@handlers.handler(XTPacket('g', 'gr'), client=ClientType.Vanilla)
async def handle_get_open_igloo_list(p):
    async def get_igloo_string(igloo):
        owner_name = p.server.penguins_by_id[igloo.penguin_id].safe_name
        like_count = p.server.cache.get(f'layout_like_count.{igloo.id}')
        like_count = await get_layout_like_count(igloo.id) if like_count is None else like_count
        p.server.cache.set(f'layout_like_count.{igloo.id}', like_count)
        igloo_population = len(igloo.penguins_by_id)
        return f'{igloo.penguin_id}|{owner_name}|{like_count}|{igloo_population}|{int(igloo.locked)}'

    open_igloos = [await get_igloo_string(igloo) for igloo in p.server.open_igloos_by_penguin_id.values()]
    local_room_population = 0

    own_layout_like_count = p.server.cache.get(f'layout_like_count.{p.igloo}')
    own_layout_like_count = 0 if p.igloo is None else await get_layout_like_count(p.igloo) \
        if own_layout_like_count is None else own_layout_like_count
    p.server.cache.set(f'layout_like_count.{p.igloo}', own_layout_like_count)

    own_layout_like_count = 0 if p.igloo is None else await get_layout_like_count(p.igloo)
    await p.send_xt('gr', own_layout_like_count, local_room_population, *open_igloos)


@handlers.handler(XTPacket('g', 'gr'), client=ClientType.Legacy)
async def handle_get_open_igloo_list_legacy(p):
    if not p.server.open_igloos_by_penguin_id:
        return await p.send_line('%xt%gr%-1%')

    async def get_igloo_string(igloo):
        owner_name = p.server.penguins_by_id[igloo.penguin_id].safe_name
        return f'{igloo.penguin_id}|{owner_name}'

    open_igloos = [await get_igloo_string(igloo) for igloo in p.server.open_igloos_by_penguin_id.values()]
    await p.send_xt('gr', *open_igloos)


@handlers.handler(XTPacket('g', 'or'), client=ClientType.Legacy)
async def handle_unlock_igloo(p):
    igloo = p.igloo_rooms[p.igloo]
    p.server.open_igloos_by_penguin_id[p.id] = igloo


@handlers.handler(XTPacket('g', 'cr'), client=ClientType.Legacy)
async def handle_lock_igloo(p):
    del p.server.open_igloos_by_penguin_id[p.id]


@handlers.handler(XTPacket('g', 'go'), client=ClientType.Legacy)
async def handle_get_owned_igloos(p):
    await p.send_xt('go', '|'.join(str(igloo_id) for igloo_id in p.igloos.keys()))


@handlers.handler(XTPacket('g', 'gf'), client=ClientType.Legacy)
async def handle_get_furniture(p):
    furniture_string = '%'.join(f'{furniture.furniture_id}|{furniture.quantity}'
                                for furniture in p.furniture.values())
    await p.send_xt('gf', furniture_string)


@handlers.handler(XTPacket('g', 'um'), client=ClientType.Legacy)
async def handle_update_igloo_music(p, music_id: int):
    if p.room.igloo and p.room.penguin_id == p.id and p.room.music != music_id:
        await p.room.update(music=music_id).apply()

        p.server.cache.delete(f'active_igloo.{p.id}')
        p.server.cache.delete(f'legacy_igloo.{p.id}')
        p.server.cache.delete(f'igloo_layouts.{p.id}')


@handlers.handler(XTPacket('g', 'ao'), client=ClientType.Legacy)
async def handle_activate_igloo_type(p, igloo_type_id: int):
    if p.room.igloo and p.room.penguin_id == p.id and p.room.type != igloo_type_id \
            and igloo_type_id in p.igloos:
        await p.room.update(type=igloo_type_id, flooring=0).apply()

        p.server.cache.delete(f'active_igloo.{p.id}')
        p.server.cache.delete(f'legacy_igloo.{p.id}')
        p.server.cache.delete(f'igloo_layouts.{p.id}')


@handlers.handler(XTPacket('g', 'grf'), client=ClientType.Vanilla)
async def handle_get_friends_igloo_list(p):
    async def get_friend_igloo_string(penguin):
        like_count = p.server.cache.get(f'layout_like_count.{penguin.igloo}')
        like_count = 0 if penguin.igloo is None else await get_layout_like_count(penguin.igloo) \
            if like_count is None else like_count
        p.server.cache.set(f'layout_like_count.{penguin.igloo}', like_count)
        return f'{penguin.id}|{like_count}'

    friend_igloos = [await get_friend_igloo_string(penguin) for penguin in p.server.penguins_by_id.values()
                     if penguin.id in p.buddies]

    await p.send_xt('grf', *friend_igloos)


@handlers.handler(XTPacket('g', 'li'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_like_igloo(p):
    if p.room.igloo:
        like_insert = insert(IglooLike).returning(IglooLike.count).values(igloo_id=p.room.id, player_id=p.id)
        like_insert = like_insert.on_conflict_do_update(
            constraint='igloo_like_pkey',
            set_=dict(count=IglooLike.count + 1, date=datetime.now()),
            where=IglooLike.date < datetime.combine(datetime.today(), datetime.min.time())
        )
        like_count = await like_insert.gino.scalar()

        await p.room.send_xt('lue', p.id, like_count, f=lambda penguin: penguin.id != p.id)
        p.server.cache.delete(f'layout_like_count.{p.room.id}')


@handlers.handler(XTPacket('g', 'gii'), client=ClientType.Vanilla)
async def handle_get_furniture_inventory(p):
    furniture = ','.join(f'{furniture_id}|0000000000|{furniture_item.quantity}'
                         for furniture_id, furniture_item in p.furniture.items())
    flooring = ','.join(f'{flooring_id}|0000000000' for flooring_id in p.flooring.keys())
    igloos = ','.join(f'{igloo_id}|0000000000' for igloo_id in p.igloos.keys())
    locations = ','.join(f'{location_id}|0000000000' for location_id in p.locations.keys())

    await p.send_xt('gii', furniture, flooring, igloos, locations)


@handlers.handler(XTPacket('g', 'ggd'), client=ClientType.Vanilla)
async def handle_get_dj3k_track(p, penguin_id: str, game_index: str):
    pid = int(penguin_id) if penguin_id.isdigit() else p.id
    room_id, index = game_index.split('|')
    game_data = await PenguinGameData.select('data').where((PenguinGameData.penguin_id == pid) &
                                                           (PenguinGameData.room_id == int(room_id)) &
                                                           (PenguinGameData.index == int(index))).gino.scalar()
    await p.send_xt('ggd', game_data or '')
