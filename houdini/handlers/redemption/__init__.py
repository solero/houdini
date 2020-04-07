from houdini import handlers
from houdini.constants import ClientType
from houdini.data.redemption import PenguinRedemptionBook
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('rjs', ext='red'), pre_login=True, client=ClientType.Vanilla)
@handlers.allow_once
async def handle_join_redemption_server_vanilla(p, credentials: str, confirmation_hash: str):
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
async def handle_join_redemption_server_legacy(p, _, login_key: str):
    if login_key != p.login_key:
        return await p.close()

    tr = p.server.redis.multi_exec()
    tr.setex(f'{p.username}.lkey', p.server.config.auth_ttl, login_key)
    await tr.execute()

    redeemed_books = await PenguinRedemptionBook.query.where(PenguinRedemptionBook.penguin_id == p.id).gino.all()
    await p.send_xt('rjs', ','.join(str(redeemed_book.book_id) for redeemed_book in redeemed_books), 'houdini',
                    int(p.is_member))
