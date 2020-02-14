from houdini import handlers
from houdini.handlers import XTPacket
from houdini.constants import ClientType

from houdini.data import db
from houdini.data.redemption import RedemptionCode, RedemptionAwardCard, RedemptionAwardFlooring, \
    RedemptionAwardFurniture, RedemptionAwardIgloo, RedemptionAwardItem, RedemptionAwardLocation,\
    RedemptionAwardPuffle, RedemptionAwardPuffleItem, PenguinRedemptionBook, PenguinRedemptionCode

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
        owned_ids = ','.join((item.item_id for item in code.items if item.item_id in p.inventory))
        return await p.send_xt('rsc', 'treasurebook', 3, owned_ids, 0)

    await p.send_xt('rsc', code.type, '', code.coins)

