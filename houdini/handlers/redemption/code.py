import random
from datetime import datetime

from houdini import handlers
from houdini.constants import ClientType
from houdini.data import db
from houdini.data.igloo import Furniture, Igloo
from houdini.data.item import Item
from houdini.data.redemption import PenguinRedemptionCode, RedemptionAwardCard, \
    RedemptionAwardFlooring, RedemptionAwardFurniture, RedemptionAwardIgloo, RedemptionAwardItem, \
    RedemptionAwardLocation, RedemptionAwardPuffle, RedemptionAwardPuffleItem, RedemptionCode
from houdini.handlers import XTPacket
from houdini.handlers.games.ninja.card import ninja_rank_up


TreasureUnlockCount = 3
NinjaRankUpChoice = 1
FireNinjaRankUpChoice = 3
WaterNinjaRankUpChoice = 4
SnowNinjaRankUpChoice = 5


@handlers.handler(XTPacket('rsc', ext='red'), pre_login=True, client=ClientType.Legacy)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_code_legacy(p, redemption_code: str):
    query = RedemptionCode.distinct(RedemptionCode.id)\
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id))\
        .query.where(RedemptionCode.code == redemption_code)
    codes = await query.gino.all()
    if not codes:
        return await p.send_error(720)

    code = codes[0]
    awards = []

    if code.uses is not None:
        redeemed_count = await db.select([db.func.count(PenguinRedemptionCode.code_id)]).where(
            PenguinRedemptionCode.code_id == code.id).gino.scalar()

        if redeemed_count >= code.uses:
            return await p.send_error(721)

    penguin_redeemed = await PenguinRedemptionCode.query.\
        where((PenguinRedemptionCode.code_id == code.id) &
              (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()
    if penguin_redeemed:
        return await p.send_error(721)

    if code.expires is not None and code.expires < datetime.now():
        return await p.send_error(726)

    if code.type == 'GOLDEN':
        p.server.cache.set(f'{p.id}.{code.code}.golden_code', code)
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank,
                               int(p.fire_ninja_rank > 0), int(p.water_ninja_rank > 0))

    if code.type == 'CARD':
        for award in code.cards:
            awards.append(str(award.card_id))
            await p.add_card(p.server.cards[award.card_id])
    else:
        if code.items:
            for award in code.items:
                awards.append(str(award.item_id))
                await p.add_inventory(p.server.items[award.item_id], notify=False)

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)
    await p.update(coins=p.coins + code.coins).apply()
    return await p.send_xt('rsc', code.type, ','.join(map(str, awards)), code.coins)


@handlers.handler(XTPacket('rsc', ext='red'), pre_login=True, client=ClientType.Vanilla)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_code_vanilla(p, redemption_code: str):
    query = RedemptionCode.distinct(RedemptionCode.id) \
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              flooring=RedemptionAwardFlooring.distinct(RedemptionAwardFlooring.flooring_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id))\
        .query.where(RedemptionCode.code == redemption_code)
    codes = await query.gino.all()
    if not codes:
        return await p.send_error(720)

    code = codes[0]
    awards = []

    if code.uses is not None:
        redeemed_count = await db.select([db.func.count(PenguinRedemptionCode.code_id)]).where(
            PenguinRedemptionCode.code_id == code.id).gino.scalar()

        if redeemed_count >= code.uses:
            return await p.send_error(721)

    penguin_redeemed = await PenguinRedemptionCode.query.where((PenguinRedemptionCode.code_id == code.id) &
                                                               (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()
    if penguin_redeemed:
        return await p.send_error(721)

    if code.expires is not None and code.expires < datetime.now():
        return await p.send_error(726)

    if code.type == 'CATALOG':
        num_redeemed_codes = await PenguinRedemptionCode.join(RedemptionCode).count().where(
            (PenguinRedemptionCode.penguin_id == p.id) & (RedemptionCode.type == 'CATALOG')).gino.scalar()
        owned_ids = ','.join((str(item.id) for item in p.server.items.treasure if item.id in p.inventory))

        p.server.cache.set(f'{p.id}.{code.code}.treasure_code', code)
        return await p.send_xt('rsc', 'treasurebook', TreasureUnlockCount, owned_ids, num_redeemed_codes)

    if code.type == 'GOLDEN':
        p.server.cache.set(f'{p.id}.{code.code}.golden_code', code)
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank, 0,
                               int(p.fire_ninja_rank > 0), int(p.water_ninja_rank > 0), 0)

    if code.type == 'INNOCENT':
        innocent_redeemed_items = {item for item in p.server.items.innocent if item.id in p.inventory}
        innocent_redeemed_furniture = {item for item in p.server.furniture.innocent if item.id in p.furniture}
        innocent_redeemed = innocent_redeemed_items.union(innocent_redeemed_furniture)
        innocent_items = set(p.server.items.innocent + p.server.furniture.innocent)

        innocent_remaining = innocent_items - innocent_redeemed

        choices = random.sample(innocent_remaining, min(len(innocent_remaining), 3))
        if len(innocent_redeemed) + 3 == len(innocent_items):
            choices.append(p.server.igloos[53])
        for item in choices:
            if type(item) is Item:
                awards.append(str(item.id))
                await p.add_inventory(item, notify=False)
            elif type(item) is Igloo:
                awards.append(f'g{item.id}')
                await p.add_igloo(item, notify=False)
            elif type(item) is Furniture:
                awards.append(f'f{item.id}')
                await p.add_furniture(item, notify=False)

        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code[0].id)

        return await p.send_xt('rsc', 'INNOCENT', ','.join(map(str, awards)),
                               len(innocent_redeemed) + len(choices),
                               len(innocent_items))

    if code.type == 'CARD':
        for award in code.cards:
            awards.append(str(award.card_id))
            await p.add_card(p.server.cards[award.card_id])
    else:
        if code.items:
            for award in code.items:
                awards.append(str(award.item_id))
                await p.add_inventory(p.server.items[award.item_id], notify=False)
        if code.furniture:
            for award in code.furniture:
                awards.append(f'f{award.furniture_id}')
                await p.add_furniture(p.server.furniture[award.furniture_id], notify=False)
        if code.igloos:
            for award in code.igloos:
                awards.append(f'g{award.igloo_id}')
                await p.add_igloo(p.server.igloos[award.igloo_id], notify=False)
        if code.locations:
            for award in code.locations:
                awards.append(f'loc{award.location_id}')
                await p.add_location(p.server.locations[award.location_id], notify=False)
        if code.flooring:
            for award in code.flooring:
                awards.append(f'flr{award.flooring_id}')
                await p.add_flooring(p.server.flooring[award.flooring_id], notify=False)
        if code.puffles:
            for award in code.puffles:
                awards.append(f'p{award.puffle_id}')
        if code.puffle_items:
            for award in code.puffle_items:
                awards.append(f'pi{award.puffle_item_id}')
                await p.add_puffle_item(p.server.puffle_items[award.puffle_item_id], notify=False)

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)
    await p.update(coins=p.coins + code.coins).apply()
    return await p.send_xt('rsc', code.type, ','.join(map(str, awards)), code.coins or '')


@handlers.handler(XTPacket('rsgc', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_golden_choice(p, redemption_code: str, choice: int):
    code_key = f'{p.id}.{redemption_code}.golden_code'
    code = p.server.cache.get(code_key)
    p.server.cache.delete(code_key)
    if not code:
        return await p.close()

    if len(code.cards) < 6:
        return await p.close()

    cards = list(code.cards)
    card_ids = [str(card.card_id) for card in cards]

    if choice == NinjaRankUpChoice:
        await ninja_rank_up(p)
        cards = cards[:4]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + str(p.ninja_rank))
    else:
        cards = cards[:4] + cards[-2:]
        await p.send_xt('rsgc', ','.join(card_ids[:4]) + '|' + ','.join(card_ids[-2:]))

    for card in cards:
        await p.add_card(p.server.cards[card.card_id])

    await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)


@handlers.handler(XTPacket('rscrt', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_send_cart(p, redemption_code: str, choice: str):
    code_key = f'{p.id}.{redemption_code}.treasure_code'
    code = p.server.cache.get(code_key)
    p.server.cache.delete(code_key)

    if code is None:
        return await p.close()

    coins = 0
    awards = []
    choices = choice.split(',')

    if len(choices) > TreasureUnlockCount:
        return await p.close()

    for choice in choices:
        if choice.startswith('c'):
            coins += 500
        elif choice.startswith('p'):
            awards.append(choice)
        elif choice.isdigit():
            awards.append(choice)
            await p.add_inventory(p.server.items[int(choice)], notify=False)

    if code.uses is not None:
        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)

    await p.update(coins=p.coins + coins).apply()
    await p.send_xt('rscrt', ','.join(awards), coins or '')


@handlers.handler(XTPacket('rsp', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_redeem_puffle(p, name: str, puffle_type: int):
    if puffle_type not in p.server.puffles:
        return await p.close()

    if not 16 > len(name) >= 3:
        await p.send_xt('rsp', 0)

    if len(p.puffles) >= 75:
        return await p.send_error(440)

    puffle = await p.puffles.insert(puffle_id=puffle_type, name=name)
    await p.add_puffle_item(p.server.puffle_items[3], quantity=5, cost=0)
    await p.add_puffle_item(p.server.puffle_items[79], cost=0)
    await p.add_puffle_item(p.server.puffle_items[p.server.puffles[puffle.id].favourite_toy])
    await p.add_inbox(p.server.postcards[111], details=puffle.name)
    await p.send_xt('rsp', 1)
