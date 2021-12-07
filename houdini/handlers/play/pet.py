import asyncio
import operator
import random
import time
from datetime import datetime, timedelta

from houdini import handlers
from houdini.constants import ClientType, StatusField
from houdini.data.mail import PenguinPostcard
from houdini.data.pet import PenguinPuffle, PenguinPuffleCollection, PenguinPuffleItemCollection, PuffleCollection, \
    PuffleItemCollection, PuffleTreasureFurniture, PuffleTreasureItem, PuffleTreasurePuffleItem
from houdini.data.room import PenguinBackyardRoom, PenguinIglooRoom
from houdini.handlers import Priority, XMLPacket, XTPacket

PuffleKillerInterval = 1800
LegacyPuffleIds = [0, 1, 2, 3, 4, 5, 6, 7, 8]

BrushCareItemId = 1
BathCareItemId = 8
SleepCareItemId = 37
BasicCareInventory = [BrushCareItemId, BathCareItemId, SleepCareItemId]


async def decrease_stats(server):
    while True:
        await asyncio.sleep(PuffleKillerInterval)
        for penguin in server.penguins_by_id.values():
            if type(penguin.room) != PenguinIglooRoom or penguin.room.penguin_id != penguin.id:
                for puffle_id in list(penguin.puffles.keys()):
                    puffle = penguin.puffles[puffle_id]
                    puffle_crumbs = server.puffles[puffle.puffle_id]
                    is_legacy_puffle = penguin.is_legacy_client and puffle.puffle_id in LegacyPuffleIds
                    is_vanilla_puffle = penguin.is_vanilla_client and not puffle.backyard
                    if is_vanilla_puffle or is_legacy_puffle:
                        if puffle.id == penguin.walking:
                            await puffle.update(
                                food=max(10, puffle.food - 8),
                                rest=max(10, puffle.rest - 8),
                                clean=max(10, puffle.clean - 8)
                            ).apply()
                        else:
                            await puffle.update(
                                food=max(0, puffle.food - 4),
                                play=max(0, puffle.play - 4),
                                rest=max(0, puffle.rest - 4),
                                clean=max(0, puffle.clean - 4)
                            ).apply()
                    if is_legacy_puffle and puffle.food == puffle.rest == puffle.clean == 0:
                        await penguin.add_inbox(server.postcards[puffle_crumbs.runaway_postcard], details=puffle.name)
                        await penguin.puffles.delete(puffle.id)
                    elif is_legacy_puffle and puffle.food < 10:
                        notification_aware = await PenguinPostcard.query.where(
                            (PenguinPostcard.penguin_id == penguin.id)
                            & (PenguinPostcard.postcard_id == 110)
                            & (PenguinPostcard.details == puffle.name)).gino.scalar()
                        if not notification_aware:
                            await penguin.add_inbox(server.postcards[110], details=puffle.name)


async def dig(p, on_command=False):
    if p.walking is not None:
        treasure_types = {0: 'coins', 1: 'food', 2: 'furniture', 3: 'clothing', None: None}
        walking_puffle = p.puffles[p.walking]

        treasure_quantity, item_id = 1, 0

        if p.can_dig_gold:
            treasure_types = {0: 'coins', 4: 'golden', None: None}

        puffle_age = (datetime.now() - walking_puffle.adoption_date).days
        puffle_health = walking_puffle.food + walking_puffle.play + walking_puffle.rest + walking_puffle.clean
        age_percent = puffle_age / 365
        health_percent = puffle_health / 400
        overall_percent = (age_percent + health_percent * 2) / 3

        if overall_percent > random.random() and p.is_member:
            treasure_type_id = random.choice(list(treasure_types))
            treasure_type = treasure_types[treasure_type_id]
        else:
            treasure_type_id = random.choice([0, None])
            treasure_type = treasure_types[treasure_type_id]

        if not on_command and treasure_type is None:
            return await p.room.send_xt('nodig', p.id, 1)
        elif treasure_type == 'food':
            diggable_food_ids = [t.puffle_item_id for t in p.server.puffle_food_treasure
                                 if t.puffle_id == walking_puffle.puffle_id
                                 and t.puffle_item_id not in p.puffle_items]
            if diggable_food_ids:
                item_id = random.choice(diggable_food_ids)
                await p.add_puffle_item(p.server.puffle_items[item_id], notify=False, cost=0)
                if item_id == p.server.puffles[walking_puffle.puffle_id].favourite_food:
                    await p.add_stamp(p.server.stamps[495])
        elif treasure_type == 'furniture':
            diggable_furniture_ids = [t.furniture_id for t in p.server.puffle_furniture_treasure
                                      if t.puffle_id == walking_puffle.puffle_id
                                      and t.furniture_id not in p.furniture]
            if diggable_furniture_ids:
                item_id = random.choice(diggable_furniture_ids)
                await p.add_furniture(p.server.furniture[item_id], notify=False, cost=0)
                await p.add_stamp(p.server.stamps[494])
        elif treasure_type == 'clothing':
            diggable_clothing_ids = [t.item_id for t in p.server.puffle_clothing_treasure
                                     if t.puffle_id == walking_puffle.puffle_id
                                     and t.item_id not in p.inventory]
            if diggable_clothing_ids:
                item_id = random.choice(diggable_clothing_ids)
                await p.add_inventory(p.server.items[item_id], notify=False, cost=0)
                await p.add_stamp(p.server.stamps[494])
        elif treasure_type == 'golden':
            item_id = 1
            treasure_quantity = random.randrange(1, 4)

            await p.update(nuggets=p.nuggets + treasure_quantity).apply()
            await p.send_xt('currencies', f'1|{p.nuggets}')

        if not item_id:
            treasure_type_id, treasure_type = 0, 'coins'

        if (on_command and treasure_type is None) or treasure_type == 'coins':
            treasure_quantity = random.randrange(10, 250)
            await p.update(coins=p.coins + treasure_quantity).apply()
            if treasure_quantity >= 50:
                await p.add_stamp(p.server.stamps[493])

        if not p.has_dug:
            await p.add_stamp(p.server.stamps[489])
            for player in p.room.penguins_by_id.values():
                if player.id != p.id:
                    await player.add_stamp(p.server.stamps[490])

        await p.room.send_xt('puffledig', p.id, p.walking, treasure_type_id, item_id,
                             treasure_quantity, int(not p.has_dug))
        await p.update(has_dug=True).apply()
        await walking_puffle.update(has_dug=True).apply()

        color_dig_count = len({puffle.puffle_id for puffle in p.puffles.values() if puffle.has_dug})
        if color_dig_count >= 11:
            await p.add_stamp(p.server.stamps[491])

        await p.server.redis.setex(f'houdini.last_dig.{p.id}', 120, int(time.time()))
        dig_count = await p.server.redis.incr(f'houdini.dig_count.{p.id}')

        if dig_count == 1:
            await p.server.redis.expireat(f'houdini.dig_count.{p.id}',
                                          (datetime.now() + timedelta(days=1)).timestamp())
        if dig_count == 5:
            await p.add_stamp(p.server.stamps[492])

        await p.status_field_set(StatusField.PuffleTreasureInfographic)


async def deliver(p, care_item, puffle):
    if care_item.cost != 0 and care_item.id not in p.puffle_items:
        await p.add_puffle_item(care_item)

    if care_item.cost == 0 or care_item.id in p.puffle_items:
        if care_item.type == 'food':
            quantity_owned = p.puffle_items[care_item.id].quantity
            if quantity_owned > 1:
                await p.puffle_items[care_item.id].update(quantity=quantity_owned - 1).apply()
            elif quantity_owned == 1:
                await p.puffle_items.delete(care_item.id)

        if care_item.id == p.server.puffles[puffle.puffle_id].favourite_food:
            await puffle.update(food=100, play=100, rest=100, clean=100).apply()
        else:
            await puffle.update(
                food=max(0, min(puffle.food + care_item.food_effect, 100)),
                play=max(0, min(puffle.play + care_item.play_effect, 100)),
                rest=max(0, min(puffle.rest + care_item.rest_effect, 100)),
                clean=max(0, min(puffle.clean + care_item.clean_effect, 100)),
            ).apply()

        celebration = puffle.food == puffle.play == puffle.rest == puffle.clean == 100

        care_item_delivery = f'{puffle.id}|{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}|{int(celebration)}'
        await p.room.send_xt('pcid', p.id, care_item_delivery)

        if care_item.id == 126:
            p.can_dig_gold = True
            await p.room.send_xt('oberry', p.id, p.walking)
            await p.send_xt('currencies', f'1|{p.nuggets}')


def get_client_puffle_id(p, puffle_id):
    parent_id = p.server.puffles[puffle_id].parent_id
    return (parent_id, puffle_id) if parent_id is not None else (puffle_id, '')


def get_client_puffle_id_string(p, puffle_id):
    parent_id, puffle_id = get_client_puffle_id(p, puffle_id)
    return f'{parent_id}|{puffle_id}'


def get_my_player_puffles(p):
    if p.is_vanilla_client:
        return [f'{puffle.id}|{get_client_puffle_id_string(p, puffle.puffle_id)}|'
                f'{puffle.name}|{int(time.mktime(puffle.adoption_date.timetuple()))}|{puffle.food}|{puffle.play}|'
                f'{puffle.rest}|{puffle.clean}|{puffle.hat or 0}|0' for puffle in p.puffles.values()]
    else:
        return [f'{puffle.id}|{puffle.name}|{puffle.puffle_id}|{puffle.clean}|'
                f'{puffle.food}|{puffle.rest}|100|100|100' for puffle in p.puffles.values()
                if puffle.puffle_id in LegacyPuffleIds]


def get_my_player_walking_puffle(p):
    if p.walking is not None and p.is_vanilla_client:
        puffle = p.puffles[p.walking]
        parent_id, puffle_id = get_client_puffle_id(p, puffle.puffle_id)
        return f'{puffle.id}|{parent_id}|{puffle_id}|{puffle.hat or 0}|0'
    return '||||'


def check_name(p, puffle_name):
    tokens = puffle_name.lower().split()
    clean = not any(word in tokens for word in p.server.chat_filter_words.keys())
    length_ok = 1 <= len(puffle_name) <= 12
    characters_ok = puffle_name.isalpha()
    return characters_ok and length_ok and clean


@handlers.boot
async def puffles_load(server):
    server.puffles = await PuffleCollection.get_collection()
    server.puffle_items = await PuffleItemCollection.get_collection()
    server.logger.info(f'Loaded {len(server.puffle_items)} puffle care items')
    server.logger.info(f'Loaded {len(server.puffles)} puffles')

    server.puffle_food_treasure = await PuffleTreasurePuffleItem.query.gino.all()
    server.puffle_furniture_treasure = await PuffleTreasureFurniture.query.gino.all()
    server.puffle_clothing_treasure = await PuffleTreasureItem.query.gino.all()

    server.puffle_killer = asyncio.create_task(decrease_stats(server))


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_pet_inventory(p):
    p.puffles = await PenguinPuffleCollection.get_collection(p.id)
    p.puffle_items = await PenguinPuffleItemCollection.get_collection(p.id)

    await p.send_xt('pgu', *get_my_player_puffles(p))


@handlers.handler(XTPacket('p', 'getdigcooldown'), pre_login=True)
async def handle_get_dig_cooldown(p):
    last_dig = await p.server.redis.get(f'houdini.last_dig.{p.id}')

    if last_dig is not None:
        cooldown_remaining = max(0, 120 - (int(time.time()) - int(last_dig)))
        return await p.send_xt('getdigcooldown', cooldown_remaining)
    await p.send_xt('getdigcooldown', 0)


@handlers.handler(XTPacket('p', 'checkpufflename'))
async def handle_check_puffle_name_with_response(p, puffle_name):
    name_ok = check_name(p, puffle_name)
    await p.send_xt('checkpufflename', puffle_name, int(name_ok))


@handlers.handler(XTPacket('p', 'pcn'))
async def handle_check_puffle_name(p, puffle_name):
    name_ok = check_name(p, puffle_name)
    await p.send_xt('pcn', puffle_name, int(name_ok))


@handlers.handler(XTPacket('p', 'pg'), client=ClientType.Vanilla)
async def handle_get_player_puffles_vanilla(p, penguin_id: int, room_type: str):
    is_backyard = room_type == 'backyard'
    owned_puffles = await PenguinPuffle.query.where((PenguinPuffle.penguin_id == penguin_id)
                                                    & (PenguinPuffle.backyard == is_backyard)).gino.all()
    walking = p.server.penguins_by_id[penguin_id].walking if penguin_id in p.server.penguins_by_id else None

    player_puffles = [f'{puffle.id}|{get_client_puffle_id_string(p, puffle.puffle_id)}|'
                      f'{puffle.name}||{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}|'
                      f'{puffle.hat or 0}|0|0|{int(puffle.id == walking)}' for puffle in owned_puffles]
    await p.send_xt('pg', len(owned_puffles), *player_puffles)
    if len(owned_puffles) >= 10:
        await p.status_field_set(StatusField.MoreThanTenPufflesBackyardMessage)


@handlers.handler(XTPacket('p', 'pg'), client=ClientType.Legacy)
async def handle_get_player_puffles_legacy(p, penguin_id: int):
    owned_puffles = await PenguinPuffle.query.where((PenguinPuffle.penguin_id == penguin_id)).gino.all()

    walking = p.server.penguins_by_id[penguin_id].walking if penguin_id in p.server.penguins_by_id else None

    player_puffles = [f'{puffle.id}|{puffle.name}|{puffle.puffle_id}|'
                      f'{puffle.clean}|{puffle.food}|{puffle.rest}|100|100|100|0|0|0|{int(puffle.id == walking)}'
                      for puffle in owned_puffles if puffle.puffle_id in LegacyPuffleIds]
    await p.send_xt('pg', *player_puffles)


@handlers.handler(XTPacket('p', 'pgu'))
async def handle_get_my_player_puffles(p):
    await p.send_xt('pgu', *get_my_player_puffles(p))


@handlers.handler(XTPacket('p', 'pn'), client=ClientType.Vanilla)
async def handle_adopt_puffle_vanilla(p, type_id: int, name: str, subtype_id: int):
    if type_id not in p.server.puffles or not check_name(p, name):
        return await p.send_error(441)

    name = name.title()
    cost = p.server.puffles[type_id].cost

    if p.coins < cost:
        return await p.send_error(401)

    if len(p.puffles) >= 75:
        return await p.send_error(440)

    puffle_id = subtype_id if bool(subtype_id) else type_id

    if type_id == 10:
        if not p.rainbow_adoptability:
            return await p.send_error(441)
        await p.update(rainbow_adoptability=False).apply()
    elif type_id == 11:
        await p.update(nuggets=p.nuggets - 15).apply()
        p.can_dig_gold = False
    elif subtype_id == 0:
        await p.add_puffle_item(p.server.puffle_items[3], quantity=5, cost=0)
        await p.add_puffle_item(p.server.puffle_items[79], cost=0)
        await p.add_puffle_item(p.server.puffle_items[p.server.puffles[puffle_id].favourite_toy])

    await p.update(coins=p.coins - cost).apply()

    puffle = await p.puffles.insert(puffle_id=puffle_id, name=name)

    parent_id, puffle_id = get_client_puffle_id(p, puffle.puffle_id)
    puffle_string = f'{puffle.id}|{parent_id}|{puffle_id}|{puffle.name}|{int(time.time())}' \
                    f'|100|100|100|100|0|0'

    await p.send_xt('pn', p.coins, puffle_string)

    await p.add_inbox(p.server.postcards[111], details=puffle.name)

    igloo_puffle_count = sum(not puff.backyard for puff in p.puffles.values())
    if igloo_puffle_count > 10:
        puffle_to_relocate = next(puff for puff in p.puffles.values() if not puff.backyard)
        await puffle_to_relocate.update(backyard=True).apply()


@handlers.handler(XTPacket('p', 'pn'), client=ClientType.Legacy)
async def handle_adopt_puffle_legacy(p, type_id: int, name: str):
    if type_id not in LegacyPuffleIds or not check_name(p, name):
        return await p.send_error(441)

    name = name.title()
    cost = 800

    if p.coins < cost:
        return await p.send_error(401)

    if len(p.puffles) >= 18:
        return await p.send_error(440)

    await p.update(coins=p.coins - cost).apply()

    puffle = await p.puffles.insert(puffle_id=type_id, name=name)

    puffle_string = f'{puffle.id}|{puffle.name}|{puffle.puffle_id}|100|100|100|100|100|100'
    await p.send_xt('pn', p.coins, puffle_string)

    await p.add_inbox(p.server.postcards[111], details=puffle.name)
    await p.add_puffle_item(p.server.puffle_items[p.server.puffles[type_id].favourite_toy], notify=False)
    await p.send_xt('pgu', *get_my_player_puffles(p))


@handlers.handler(XTPacket('p', 'pgpi'), client=ClientType.Vanilla)
async def handle_get_care_inventory(p):
    await p.send_xt('pgpi',
                    *(f'{item_id}|1' for item_id in BasicCareInventory),
                    *(f'{care_item.item_id}|{care_item.quantity}' for care_item in p.puffle_items.values()))


@handlers.handler(XTPacket('p', 'pm'))
async def handle_puffle_move(p, puffle: PenguinPuffle, x: int, y: int):
    await p.room.send_xt('pm', f'{puffle.id}|{x}|{y}', f=operator.attrgetter('is_vanilla_client'))
    await p.room.send_xt('pm', puffle.id, x, y, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'ps'))
async def handle_puffle_frame(p, puffle_id: int, frame_id: int):
    if puffle_id in p.puffles:
        await p.room.send_xt('ps', puffle_id, frame_id)


@handlers.handler(XTPacket('p', 'pw'), client=ClientType.Vanilla)
async def handle_puffle_walk_vanilla(p, puffle: PenguinPuffle, walking: int):
    if not p.walking and walking:
        await p.update(walking=puffle.id).apply()
        parent_id, puffle_id = get_client_puffle_id(p, puffle.puffle_id)
        await p.room.send_xt('pw', p.id, puffle.id, parent_id, puffle_id, 1, puffle.hat or 0)
    elif not walking and puffle.id == p.walking:
        igloo_puffle_count = sum(not puff.backyard and puff.id != puffle.id for puff in p.puffles.values())
        in_backyard = type(p.room) == PenguinBackyardRoom
        return_to_backyard = in_backyard or type(p.room) != PenguinIglooRoom and puffle.backyard
        if igloo_puffle_count >= 10 and not return_to_backyard:
            return await p.send_error(443)

        await puffle.update(backyard=return_to_backyard).apply()

        await p.update(walking=None).apply()
        await p.room.send_xt('pw', p.id, puffle.id, 0, 0, 0, 0)

    puffle_string = f'{puffle.id}||||||||||||{walking}'
    await p.room.send_xt('pw', p.id, puffle_string, f=operator.attrgetter('is_legacy_client'))
    p.can_dig_gold = False

    if not p.status_field_get(StatusField.HasWalkedPuffleFirstTime):
        await p.status_field_set(StatusField.HasWalkedPuffleFirstTime)
    else:
        await p.status_field_set(StatusField.HasWalkedPuffleSecondTime)


@handlers.handler(XTPacket('p', 'pw'), client=ClientType.Legacy)
async def handle_puffle_walk_legacy(p, puffle: PenguinPuffle, walking: int):
    if puffle.id != p.walking and walking:
        if puffle.rest < 20 and puffle.food < 40:
            return

        await p.update(walking=puffle.id).apply()
        await p.room.send_xt('pw', p.id, puffle.id, -1, str(), 1, 0,
                             f=operator.attrgetter('is_vanilla_client'))
    elif puffle.id == p.walking and not walking:
        await p.update(walking=None).apply()
        await p.room.send_xt('pw', p.id, puffle.id, 0, 0, 0, 0,
                             f=operator.attrgetter('is_vanilla_client'))

    puffle_string = f'{puffle.id}||||||||||||{walking}'
    await p.room.send_xt('pw', p.id, puffle_string, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('s', 'upa'), client=ClientType.Legacy)
async def handle_wear_puffle(p, item_id: int):
    if p.walking:
        walking_puffle = p.puffles[p.walking]
        if item_id == walking_puffle.puffle_id + 750:
            await p.update(hand=item_id).apply()
            await p.room.send_xt('upa', p.id, item_id)
        else:
            await p.update(walking=None).apply()


@handlers.disconnected
@handlers.player_attribute(client_type=ClientType.Legacy)
@handlers.player_attribute(joined_world=True)
async def handle_stop_walking(p):
    if p.joined_world:
        if p.walking:
            await p.update(hand=None, walking=None).apply()


@handlers.handler(XTPacket('p', 'pp'), client=ClientType.Vanilla)
async def handle_puffle_play_vanilla(p, puffle: PenguinPuffle):
    favourite_toy = p.server.puffle_items[p.server.puffles[puffle.puffle_id].favourite_toy]
    await deliver(p, favourite_toy, puffle)

    legacy_puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    vanilla_puffle_string = f'{puffle.id}|{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}'
    await p.room.send_xt('pp', legacy_puffle_string, 1, f=operator.attrgetter('is_legacy_client'))
    await p.room.send_xt('pp', p.id, vanilla_puffle_string, f=operator.attrgetter('is_vanilla_client'))


@handlers.handler(XTPacket('p', 'pp'), client=ClientType.Legacy)
async def handle_puffle_play_legacy(p, puffle: PenguinPuffle):
    if puffle.rest < 20 or puffle.clean < 10:
        return

    negative_food = random.randrange(10, 25)
    negative_rest = random.randrange(10, 25)
    await puffle.update(
        food=max(0, puffle.food - negative_food),
        rest=max(0, puffle.rest - negative_rest),
        clean=min(100, puffle.clean + 10)
    ).apply()

    play_type = 1 if puffle.rest > 80 else random.choice([0, 2])

    puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    await p.room.send_xt('pp', puffle_string, play_type, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'pr'), client=ClientType.Vanilla)
async def handle_puffle_rest_vanilla(p, puffle: PenguinPuffle):
    sleep = p.server.puffle_items[37]

    await deliver(p, sleep, puffle)

    legacy_puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    vanilla_puffle_string = f'{puffle.id}|{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}'
    await p.room.send_xt('pr', legacy_puffle_string, f=operator.attrgetter('is_legacy_client'))
    await p.room.send_xt('pr', p.id, vanilla_puffle_string, f=operator.attrgetter('is_vanilla_client'))


@handlers.handler(XTPacket('p', 'pr'), client=ClientType.Legacy)
async def handle_puffle_rest_legacy(p, puffle: PenguinPuffle):
    positive_rest = random.randrange(15, 40)
    await puffle.update(rest=min(100, puffle.rest + positive_rest)).apply()

    puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    await p.room.send_xt('pr', puffle_string, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'pt'), client=ClientType.Legacy)
async def handle_puffle_treat_legacy(p, puffle: PenguinPuffle, treat_id: int):
    if p.coins > 5:
        positive_food = random.randrange(5, 15)
        await puffle.update(food=min(100, puffle.food + positive_food)).apply()
        await p.update(coins=p.coins - 5).apply()

        puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
        await p.room.send_xt('pt', p.coins, puffle_string, treat_id, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'pf'), client=ClientType.Legacy)
async def handle_puffle_feed_legacy(p, puffle: PenguinPuffle):
    if p.coins > 10:
        positive_food = random.randrange(15, 40)
        await puffle.update(food=min(100, puffle.food + positive_food)).apply()
        await p.update(coins=p.coins - 10).apply()

        puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
        await p.room.send_xt('pf', p.coins, puffle_string, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'pb'), client=ClientType.Legacy)
async def handle_puffle_bath_legacy(p, puffle: PenguinPuffle):
    if p.coins > 5:
        additional_rest = random.randrange(5, 15)
        additional_clean = random.randrange(15, 40)
        await puffle.update(
            rest=min(100, puffle.rest + additional_rest),
            clean=min(100, puffle.clean + additional_clean)
        ).apply()

        await p.update(coins=p.coins - 5).apply()

        puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
        await p.room.send_xt('pb', p.coins, puffle_string, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'ip'), client=ClientType.Legacy)
async def handle_puffle_play_interation_legacy(p, puffle: PenguinPuffle, x: int, y: int):
    if puffle.rest < 20 or puffle.clean < 10:
        return

    negative_food = random.randrange(15, 25)
    negative_rest = random.randrange(15, 25)
    await puffle.update(
        food=max(0, puffle.food - negative_food),
        rest=max(0, puffle.rest - negative_rest),
        clean=min(100, puffle.clean + 20)
    ).apply()

    puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    await p.room.send_xt('ip', puffle_string, x, y, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'ir'), client=ClientType.Legacy)
async def handle_puffle_rest_interation_legacy(p, puffle: PenguinPuffle, x: int, y: int):
    positive_rest = random.randrange(20, 50)
    await puffle.update(rest=min(100, puffle.rest + positive_rest)).apply()

    puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    await p.room.send_xt('ir', puffle_string, x, y, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'if'), client=ClientType.Legacy)
async def handle_puffle_feed_interation_legacy(p, puffle: PenguinPuffle, x: int, y: int):
    positive_food = random.randrange(20, 50)
    await puffle.update(
        food=min(100, puffle.food + positive_food)
    ).apply()

    await p.update(coins=p.coins - 10).apply()

    puffle_string = f'{puffle.id}|puf|fle|{puffle.clean}|{puffle.food}|{puffle.rest}'
    await p.room.send_xt('if', p.coins, puffle_string, x, y, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'ip'), client=ClientType.Vanilla)
async def handle_puffle_play_interation_vanilla(p, puffle: PenguinPuffle, x: int, y: int):
    favourite_toy = p.server.puffle_items[p.server.puffles[puffle.puffle_id].favourite_toy]
    await deliver(p, favourite_toy, puffle)

    puffle_string = f'{puffle.id}|{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}|{x}|{y}'
    await p.room.send_xt('ip', puffle_string)


@handlers.handler(XTPacket('p', 'ir'), client=ClientType.Vanilla)
async def handle_puffle_rest_interation_vanilla(p, puffle: PenguinPuffle, x: int, y: int):
    sleep = p.server.puffle_items[37]
    await deliver(p, sleep, puffle)

    puffle_string = f'{puffle.id}|{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}|{x}|{y}'
    await p.room.send_xt('ir', puffle_string)


@handlers.handler(XTPacket('p', 'pip'))
async def handle_puffle_init_play_interation(p, puffle: PenguinPuffle, x: int, y: int):
    await p.room.send_xt('pip', f'{puffle.id}|{x}|{y}', f=operator.attrgetter('is_vanilla_client'))
    await p.room.send_xt('pip', puffle.id, x, y, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'pir'))
async def handle_puffle_init_rest_interaction(p, puffle: PenguinPuffle, x: int, y: int):
    await p.room.send_xt('pir', f'{puffle.id}|{x}|{y}', f=operator.attrgetter('is_vanilla_client'))
    await p.room.send_xt('pir', puffle.id, x, y, f=operator.attrgetter('is_legacy_client'))


@handlers.handler(XTPacket('p', 'papi'), client=ClientType.Vanilla)
async def handle_add_puffle_care_item(p, item_id: int):
    if item_id not in p.server.puffle_items:
        return await p.send_error(402)

    care_item = p.server.puffle_items[item_id]

    if care_item.cost > p.coins:
        return await p.send_error(401)

    await p.add_puffle_item(care_item)


@handlers.handler(XTPacket('p', 'pgmps'), client=ClientType.Vanilla)
async def handle_get_my_puffle_stats(p):
    puffle_stats = ','.join(f'{puffle.id}|{puffle.food}|{puffle.play}|{puffle.rest}|{puffle.clean}'
                            for puffle in p.puffles.values())
    await p.room.send_xt('pgmps', puffle_stats)


@handlers.handler(XTPacket('p', 'pcid'), client=ClientType.Vanilla)
async def handle_puffle_care_item_delivered(p, puffle: PenguinPuffle, care_item_id: int):
    care_item = p.server.puffle_items[care_item_id]
    await deliver(p, care_item, puffle)


@handlers.handler(XTPacket('p', 'phg'))
async def handle_get_puffle_handler(p):
    await p.send_xt('phg', int(p.puffle_handler))


@handlers.handler(XTPacket('p', 'phs'))
@handlers.allow_once
async def handle_set_puffle_handler(p):
    await p.update(puffle_handler=True).apply()


@handlers.handler(XTPacket('p', 'puphi'), client=ClientType.Vanilla)
async def handle_puffle_visitor_hat_update(p, puffle: PenguinPuffle, hat_id: int):
    if hat_id in p.puffle_items or hat_id == 0:
        await puffle.update(hat=hat_id if hat_id > 0 else None).apply()
        await p.room.send_xt('puphi', puffle.id, hat_id)
        if puffle.id == p.walking:
            parent_id, puffle_id = get_client_puffle_id(p, puffle.puffle_id)
            await p.room.send_xt('pw', p.id, puffle.id, 0, 0, 0, 0)
            await p.room.send_xt('pw', p.id, puffle.id, parent_id, puffle_id, 1, puffle.hat or 0)


@handlers.handler(XTPacket('p', 'pufflewalkswap'), client=ClientType.Vanilla)
async def handle_walk_swap_puffles(p, puffle: PenguinPuffle):
    if puffle.id != p.walking:
        walking_puffle = p.puffles[p.walking]
        in_backyard = type(p.room) == PenguinBackyardRoom
        return_to_backyard = in_backyard or type(p.room) != PenguinIglooRoom and walking_puffle.backyard
        await walking_puffle.update(backyard=return_to_backyard).apply()

        puffle = p.puffles[puffle.id]
        await p.update(walking=puffle.id).apply()

        parent_id, puffle_id = get_client_puffle_id(p, puffle.puffle_id)
        await p.room.send_xt('pufflewalkswap', p.id, puffle.id, parent_id, puffle_id, 1, puffle.hat or 0)
        p.can_dig_gold = False


@handlers.handler(XTPacket('p', 'puffletrick'), client=ClientType.Vanilla)
async def handle_puffle_trick(p, trick_id: int):
    if p.walking is not None:
        await p.room.send_xt('puffletrick', p.id, trick_id)


@handlers.handler(XTPacket('p', 'puffleswap'), client=ClientType.Vanilla)
async def handle_change_puffle_room(p, puffle: PenguinPuffle, room_type: str):
    to_backyard = room_type == 'backyard'
    igloo_puffle_count = sum(not puff.backyard and puff.id != p.walking for puff in p.puffles.values())
    if igloo_puffle_count >= 10 and not to_backyard:
        return await p.send_error(443)

    await puffle.update(backyard=1 if to_backyard else 0).apply()
    await p.room.send_xt('puffleswap', puffle.id, room_type)
    await p.status_field_set(StatusField.PlayerSwapPuffle)


@handlers.handler(XTPacket('p', 'prp'), client=ClientType.Vanilla)
async def handle_return_puffle(p, puffle: PenguinPuffle):
    if p.walking == puffle.id:
        await p.update(walking=None).apply()

    await p.puffles.delete(puffle.id)
    await p.room.send_xt('prp', puffle.id)


@handlers.handler(XTPacket('p', 'carestationmenu'), client=ClientType.Vanilla)
async def handle_care_station_menu(p):
    await p.send_xt('carestationmenu', '7|117', '119')


@handlers.handler(XTPacket('p', 'carestationmenuchoice'), client=ClientType.Vanilla)
async def handle_care_station_menu_choice(p, item_id: int):
    await p.room.send_xt('carestationmenuchoice', p.id, item_id)


@handlers.handler(XTPacket('p', 'puffledig'), client=ClientType.Vanilla)
@handlers.cooldown(60)
async def handle_puffle_dig(p):
    await dig(p)


@handlers.handler(XTPacket('p', 'puffledigoncommand'), client=ClientType.Vanilla)
@handlers.cooldown(119)
async def handle_puffle_dig_on_command(p):
    await dig(p, on_command=True)


@handlers.handler(XTPacket('p', 'revealgoldpuffle'))
async def handle_reveal_gold_puffle(p):
    if p.can_dig_gold and p.nuggets >= 15:
        await p.room.send_xt('revealgoldpuffle', p.id)
