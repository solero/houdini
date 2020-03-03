from houdini import handlers
from houdini.handlers import XTPacket
from houdini.constants import ClientType

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
    query = RedemptionCode.load(cards=RedemptionAwardCard,
                                flooring=RedemptionAwardFlooring,
                                furniture=RedemptionAwardFurniture,
                                igloos=RedemptionAwardIgloo,
                                items=RedemptionAwardItem,
                                locations=RedemptionAwardLocation,
                                puffles=RedemptionAwardPuffle,
                                puffle_items=RedemptionAwardPuffleItem)\
        .query.where(RedemptionCode.code == redemption_code)
    code = await query.gino.first()

    if code is None:
        return await p.send_error(720)

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
        owned_ids = ','.join((str(item.id) for item in p.server.items.values() if item.treasure and item.id in p.inventory))
        p.tb_validation = True
        return await p.send_xt('rsc', 'treasurebook', 3, owned_ids, num_redeemed_codes)

    if code.type == 'INNOCENT':
        all_innocent_items = [item.id for item in p.server.items.values() if item.id in p.inventory and item.innocent]
        all_innocent_furniture = [item.id for item in p.server.furniture.values() if item.id in p.furniture and item.innocent]
        innocent_redeemed = all_innocent_items + all_innocent_furniture

        innocent_furniture = ['f' + str(item.id) for item in p.server.furniture.values() if item.innocent]
        innocent_clothing = [str(item.id) for item in p.server.items.values() if item.innocent]

        innocent_items = innocent_clothing + innocent_furniture
        awards = []

        while len(awards) < 3:
            if len(innocent_redeemed) >= len(innocent_items):
                choice = random.choice(innocent_furniture)
                if choice not in awards:
                    p.add_furniture(int(choice[1:]), 1, False)
                    awards.append(choice)
                else:
                    choice = random.choice(innocent_items)
                    if choice in innocent_clothing:
                        if int(choice) not in innocent_redeemed and choice not in awards:
                            p.add_inventory(int(choice), False)
                            awards.append(choice)
                        elif choice in innocent_furniture:
                            if int(choice[1:]) not in innocent_redeemed and choice not in awards:
                                p.add_furniture(int(choice[1:]), 1, False)
                                awards.append(choice)

        redeemed = len(innocent_redeemed) + 3
        if redeemed == len(innocent_items):
            redeemed += 1
            p.add_igloo(53, False)
            awards.append("g53")

        if code.uses != -1:
            await PenguinRedemptionCode.create(penguin_id=p.id, code_id=code.id)

        await p.send_xt('rsc', 'INNOCENT', ','.join(map(str, awards)), redeemed, len(innocent_items))


