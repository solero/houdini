from houdini import handlers
from houdini.constants import ClientType
from houdini.data.item import Item
from houdini.data.igloo import Furniture, Igloo
from houdini.data import db
from houdini.data.redemption import RedemptionBook, RedemptionBookWord,PenguinRedemptionBook, PenguinRedemptionCode, RedemptionAwardCard, \
    RedemptionAwardFlooring, RedemptionAwardFurniture, RedemptionAwardIgloo, RedemptionAwardItem, \
    RedemptionAwardLocation, RedemptionAwardPuffle, RedemptionAwardPuffleItem, RedemptionCode
from houdini.handlers import XTPacket

from houdini.handlers.games.ninja.card import ninja_rank_up

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


@handlers.handler(XTPacket('rjs', ext='red'), pre_login=True, client=ClientType.Legacy)
@handlers.allow_once
async def handle_join_redemption_server_legacy(p, penguin_id: int, login_key: str, lang: str):
    if login_key != p.login_key:
        return await p.close()

    tr = p.server.redis.multi_exec()
    tr.setex(f'{p.username}.lkey', p.server.config.auth_ttl, login_key)
    await tr.execute()

    redeemed_books = await PenguinRedemptionBook.query.where(PenguinRedemptionBook.penguin_id == p.id).gino.all()
    await p.send_xt('rjs', ','.join(str(redeemed_book.book_id) for redeemed_book in redeemed_books), 'houdini', int(p.is_member))


@handlers.handler(XTPacket('rsc', ext='red'), pre_login=True, client=ClientType.Legacy)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_code_legacy(p, redemption_code: str):
    query = RedemptionCode.distinct(RedemptionCode.id) \
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              flooring=RedemptionAwardFlooring.distinct(RedemptionAwardFlooring.flooring_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id)
              ) \
        .query.where(RedemptionCode.code == redemption_code)
    codes = await query.gino.all()
    awards = []

    if not codes:
        return await p.send_error(720)

    code = codes[0]

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

    if code.type == 'GOLDEN':
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank,
                               int(p.fire_ninja_rank > 0), int(p.water_ninja_rank > 0))

    if code.type == 'CARD':
        for award in code.cards:
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
    query = RedemptionCode.distinct(RedemptionCode.id)\
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              flooring = RedemptionAwardFlooring.distinct(RedemptionAwardFlooring.flooring_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id)
              )\
        .query.where(RedemptionCode.code == redemption_code)
    codes = await query.gino.all()
    awards = []

    if not codes:
        return await p.send_error(720)

    code = codes[0]

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
            (PenguinRedemptionCode.penguin_id == p.id) & (RedemptionCode.type == 'CATALOG')
        ).gino.scalar()
        owned_ids = ','.join((str(item) for item in p.server.items.treasure if item in p.inventory))
        return await p.send_xt('rsc', 'treasurebook', 3, owned_ids, num_redeemed_codes)

    if code.type == 'INNOCENT':
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

    if code.type == 'GOLDEN':
        return await p.send_xt('rsc', 'GOLDEN', p.ninja_rank, p.fire_ninja_rank, p.water_ninja_rank, 0,
                        int(p.fire_ninja_rank > 0), int(p.water_ninja_rank > 0), 0)

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
                awards.append('f'+str(award.furniture_id))
                await p.add_furniture(p.server.furniture[award.furniture_id], notify=False)

        if code.igloos:
            for award in code.igloos:
                awards.append('g'+str(award.igloo_id))
                await p.add_igloo(p.server.igloos[award.igloo_id], notify=False)

        if code.locations:
            for award in code.locations:
                awards.append('loc'+str(award.location_id))
                await p.add_location(p.server.locations[award.location_id], notify=False)
        
        if code.flooring:
            for award in code.flooring:
                awards.append('flr'+str(award.flooring_id))
                await p.add_flooring(p.server.flooring[award.flooring_id], notify=False)
            
        if code.puffles:
            for award in code[0].puffles:
                awards.append('p'+str(award.puffle_id))
        
        if code.puffle_items:
            for award in code.puffle_items:
                awards.append('pi'+str(award.puffle_item_id))
                await p.add_puffle_item(p.server.puffle_items[award.puffle_item_id], notify=False)


        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)
        await p.update(coins=p.coins + code.coins).apply()
        coins = "" if code.coins == 0 else code.coins
        return await p.send_xt('rsc', code.type, ','.join(map(str, awards)), coins)


@handlers.handler(XTPacket('rsgc', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_golden_choice(p, redemption_code: str, choice: int):    
    query = RedemptionCode.distinct(RedemptionCode.id)\
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id)
              )\
        .query.where(RedemptionCode.code == redemption_code)
    codes = await query.gino.all()

    if not codes:
        return await p.close()

    code = codes[0]

    if len(code.cards) < 6:
        return await p.close()

    penguin_redeemed = await PenguinRedemptionCode.query.where((PenguinRedemptionCode.code_id == code.id) & (PenguinRedemptionCode.penguin_id == p.id)).gino.scalar()

    if penguin_redeemed:
        return await p.close()

    card_ids = [card.card_id for card in code.cards]

    if choice == 1:
        await ninja_rank_up(p)
        await p.send_xt('rsgc', ','.join(map(str, card_ids[:4])) + '|' + str(p.ninja_rank))

    elif choice == 2:
        await p.send_xt('rsgc', ','.join(map(str, card_ids[:4])) + '|' + ','.join(map(str, card_ids[-2:])))
        for card in code.cards:
            await p.add_card(p.server.cards[card.card_id])

    if code.uses is None:
        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)


@handlers.handler(XTPacket('rscrt', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_send_cart(p, redemption_code: str, choice: str, super_exclusive: int):
    query = RedemptionCode.distinct(RedemptionCode.id) \
        .load(cards=RedemptionAwardCard.distinct(RedemptionAwardCard.card_id),
              items=RedemptionAwardItem.distinct(RedemptionAwardItem.item_id),
              flooring=RedemptionAwardFlooring.distinct(RedemptionAwardFlooring.flooring_id),
              furniture=RedemptionAwardFurniture.distinct(RedemptionAwardFurniture.furniture_id),
              igloos=RedemptionAwardIgloo.distinct(RedemptionAwardIgloo.igloo_id),
              locations=RedemptionAwardLocation.distinct(RedemptionAwardLocation.location_id),
              puffles=RedemptionAwardPuffle.distinct(RedemptionAwardPuffle.puffle_id),
              puffle_items=RedemptionAwardPuffleItem.distinct(RedemptionAwardPuffleItem.puffle_item_id)
              ) \
        .query.where(RedemptionCode.code == redemption_code)
    codes = await query.gino.all()

    if len(codes) == 0:
        return await p.close()

    code = codes[0]
    coins = 0
    if choice is None:
        return await p.close()

    choices = choice.split(',')
    for choice in choices:
        if choice[:2] == 'c0':
            coins += 500

        elif choice[:1] != 'p':
            if p.server.items[int(choice)] not in p.server.items.treasure:
                return await p.close()
            else:
                await p.add_inventory(p.server.items[int(choice)], notify=False)

    while 'c0' in choices:
        choices.remove('c0')

    if code.uses is None:
        await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)

    if coins == 0:
        coins = ''
    else:
        await p.update(coins=p.coins + coins).apply()

    await p.send_xt('rscrt', ','.join(choices), coins)



@handlers.handler(XTPacket('rsp', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rsc', ext='red'))
async def handle_redeem_puffle(p, name: str, id: int):
    if name is None or id is None:
        return await p.close()

    if id not in p.server.puffles:
        return await p.close()

    if not 16 > len(name) >= 3:
        await p.send_xt('rsp', 0)

    if len(p.puffles) >= 75:
        return await p.send_error(440)

    puffle = await p.puffles.insert(puffle_id=id, name=name)
    await p.add_puffle_item(p.server.puffle_items[3], quantity=5, cost=0)
    await p.add_puffle_item(p.server.puffle_items[79], cost=0)
    await p.add_puffle_item(p.server.puffle_items[p.server.puffles[puffle.id].favourite_toy])
    await p.add_inbox(p.server.postcards[111], details=puffle.name)
    await p.send_xt('rsp', 1)


@handlers.handler(XTPacket('rgbq', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_get_book_question(p, book: int):
    book_exist = await RedemptionBook.query.where(RedemptionBook.id == book).gino.scalar()
    book_redeemed = await PenguinRedemptionBook.query.where((PenguinRedemptionBook.book_id == book) &
                                                               (PenguinRedemptionBook.penguin_id == p.id)).gino.scalar()
    if not book_exist:
        return await p.close()

    if book_redeemed:
        return await p.close()

    question = await RedemptionBookWord.query.where(RedemptionBookWord.book_id == book).order_by(db.func.random()).gino.first()
    await p.send_xt('rgbq', question.question_id, question.book_id, question.page, question.line, question.word_number)


@handlers.handler(XTPacket('rsba', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rgbq', ext='red'))
async def handle_send_book_answer(p, book: int, question_id: int, answer: str):
    book_exist = await RedemptionBook.query.where(RedemptionBook.id == book).gino.scalar()
    book_redeemed = await PenguinRedemptionBook.query.where((PenguinRedemptionBook.book_id == book) &
                                                            (PenguinRedemptionBook.penguin_id == p.id)).gino.scalar()
    if not book_exist:
        return await p.close()

    if book_redeemed:
        return await p.close()

    redemption_attempts_key = f'{p.id}.redemption_attempts'

    if await p.server.redis.exists(redemption_attempts_key):
        tr = p.server.redis.multi_exec()
        tr.incr(redemption_attempts_key)
        tr.expire(redemption_attempts_key, p.server.config.login_failure_timer)
        failure_count, _ = await tr.execute()

        if failure_count >= 5:
            return await p.send_error(713)
    else:
        await p.server.redis.setex(redemption_attempts_key, p.server.config.login_failure_timer, 1)


    redemption_book_answer = await RedemptionBookWord.select('answer').where((RedemptionBookWord.book_id == book) &
                                                             (RedemptionBookWord.question_id == question_id)).gino.scalar()

    if answer == redemption_book_answer:
        if book == 23:
            item = 14608
            await p.add_inventory(p.server.items[14608], notify=False)

        elif book == 24:
            item = 13054
            await p.add_inventory(p.server.items[13054], notify=False)

        else:
            if 15007 not in p.inventory:
                item = 15007
                await p.add_inventory(p.server.items[15007], notify=False)
            else:
                item = ''

        await p.update(coins=p.coins + 1500).apply()

        await p.send_xt('rsba', item, 1500)
        await PenguinRedemptionBook.create(penguin_id=p.id, book_id=book)

    else:
        return await p.send_error(712)






