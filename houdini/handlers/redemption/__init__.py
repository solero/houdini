from houdini import handlers
from houdini.handlers import XTPacket
from houdini.constants import ClientType
from houdini.data.item import Item
from houdini.data.igloo import Furniture, Igloo
from houdini.data import db
from houdini.data.redemption import RedemptionCode, RedemptionAwardCard, RedemptionAwardFlooring, \
    RedemptionAwardFurniture, RedemptionAwardIgloo, RedemptionAwardItem, RedemptionAwardLocation,\
    RedemptionAwardPuffle, RedemptionAwardPuffleItem, PenguinRedemptionBook, PenguinRedemptionCode

import random
from datetime import datetime


@handlers.handler(XTPacket('rjs', ext='red'), pre_login=True, client=ClientType.Vanilla)
@handlers.allow_once
async def handle_join_redemption_server_vanilla(p, credentials: str, confirmation_hash: str, lang: str):
    pid, _, username, login_key, rdnk, approved, rejected = credentials.split('|')

    if login_key != p.login_key:
        return await p.close()

    tr = p.server.redis.multi_exec()
    tr.setex(f'{username}.lkey', p.server.config.auth_ttl, login_key)
    tr.setex(f'{username}.ckey', p.server.config.auth_ttl, confirmation_hash)
    await tr.execute()

    redeemed_books = await PenguinRedemptionBook.query.where(PenguinRedemptionBook.penguin_id == p.id).gino.all()
    await p.send_xt('rjs', ','.join(str(redeemed_book.book_id) for redeemed_book in redeemed_books), 'houdini',
                    int(p.is_member))


@handlers.handler(XTPacket('rsc', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_code(p, redemption_code: str):
    query = RedemptionCode.distinct(RedemptionCode.id)\
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id)
              )\
        .query.where(RedemptionCode.code == redemption_code)
    code = await query.gino.all()
    awards = []

    if code[0] is None:
        return await p.send_error(720)

    if code[0].uses is not None:
        redeemed_count = await db.select([db.func.count(PenguinRedemptionCode.code_id)]).where(
            PenguinRedemptionCode.code_id == code[0].id).gino.scalar()

        if redeemed_count >= code[0].uses:
            return await p.send_error(721)

    penguin_redeemed = await PenguinRedemptionCode.query.where((PenguinRedemptionCode.code_id == code[0].id) &
                                                               (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()
    if penguin_redeemed:
        return await p.send_error(721)

    if code[0].expires is not None and code[0].expires < datetime.now():
        return await p.send_error(726)

    if code[0].type == 'CATALOG':
        num_redeemed_codes = await PenguinRedemptionCode.join(RedemptionCode).count().where(
            (PenguinRedemptionCode.penguin_id == p.id) & (RedemptionCode.type == 'CATALOG')
        ).gino.scalar()
        owned_ids = ','.join((str(item) for item in p.server.items.treasure if item in p.inventory))
        return await p.send_xt('rsc', 'treasurebook', 3, owned_ids, num_redeemed_codes)

    if code[0].type == 'INNOCENT':
        innocent_redeemed_items = { item for item in p.server.items.innocent if item.id in p.inventory }
        innocent_redeemed_furniture = { item for item in p.server.furniture.innocent if item.id in p.furniture }
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
                awards.append('g' + str(item.id))
                await p.add_igloo(item, notify=False)
            elif type(item) is Furniture:
                awards.append('f' + str(item.id))
                await p.add_furniture(item, notify=False)

        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code[0].id)

        return await p.send_xt('rsc', 'INNOCENT', ','.join(map(str, awards)), 
                            len(innocent_redeemed) + len(choices), 
                            len(innocent_items))
    if code[0].type == 'GOLDEN':
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank, 0,
                        int(p.fire_ninja_rank > 0), int(p.water_ninja_rank > 0), 0)

    if code[0].type == 'CARD':
        for award in code[0].cards:
            awards.append(str(award.card_id))
            await p.add_card(p.server.cards[award.card_id])

    else:
        if code[0].items:
            for award in code[0].items:
                awards.append(str(award.item_id))
                await p.add_inventory(p.server.items[award.item_id], notify=False)
            
        if code[0].furniture:
            for award in code[0].furniture:
                awards.append('f'+str(award.furniture_id))
                await p.add_furniture(p.server.furniture[award.furniture_id], notify=False)

        if code[0].igloos:
            for award in code[0].igloos:
                awards.append('g'+str(award.igloo_id))
                await p.add_igloo(p.server.igloos[award.igloo_id], notify=False)

        if code[0].locations:
            for award in code[0].locations:
                awards.append('loc'+str(award.location_id))
                await p.add_location(p.server.locations[award.location_id], notify=False)
        
        if code[0].flooring:
            for award in code[0].flooring:
                awards.append('flr'+str(award.flooring_id))
                await p.add_flooring(p.server.flooring[award.flooring_id], notify=False)
            
        if code[0].puffles:
            for award in code[0].puffles:
                awards.append('p'+str(award.puffle_id))
        
        if code[0].puffle_items:
            for award in code[0].puffle_items:
                awards.append('pi'+str(award.puffle_item_id))
                await p.add_puffle_item(p.server.puffle_items[award.puffle_item_id], notify=False)


        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code[0].id)
        await p.update(coins=p.coins + code[0].coins).apply()
        coins = "" if code[0].coins == 0 else code[0].coins
        return await p.send_xt('rsc', code[0].type, ','.join(map(str, awards)), coins)


@handlers.handler(XTPacket('rsgc', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_golden_choice(p, redemption_code: str, choice: int):    
    query = RedemptionCode.distinct(RedemptionCode.id)\
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id)
              )\
        .query.where(RedemptionCode.code == redemption_code)
    code = await query.gino.all()

    if len(code[0].cards) < 6:
        return await p.close()

    penguin_redeemed = await PenguinRedemptionCode.query.where((PenguinRedemptionCode.code_id == code[0].id) & (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()

    if penguin_redeemed:
        return await p.close()

    if choice == 1:
        



    
    

