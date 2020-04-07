from houdini import handlers
from houdini.data import db
from houdini.data.redemption import PenguinRedemptionBook, RedemptionBook, RedemptionBookWord
from houdini.handlers import XTPacket


@handlers.handler(XTPacket('rgbq', ext='red'), pre_login=True)
@handlers.depends_on_packet(XTPacket('rjs', ext='red'))
async def handle_get_book_question(p, book: int):
    book_exist = await RedemptionBook.query.where(RedemptionBook.id == book).gino.scalar()
    book_redeemed = await PenguinRedemptionBook.query.\
        where((PenguinRedemptionBook.book_id == book) &
              (PenguinRedemptionBook.penguin_id == p.id)).gino.scalar()
    if not book_exist:
        return await p.close()

    if book_redeemed:
        return await p.close()

    question = await RedemptionBookWord.query.where(RedemptionBookWord.book_id == book)\
        .order_by(db.func.random()).gino.first()
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

    redemption_book_answer = await RedemptionBookWord.select('answer').\
        where((RedemptionBookWord.book_id == book) &
              (RedemptionBookWord.question_id == question_id)).gino.scalar()

    if answer == redemption_book_answer:
        item = None
        if book == 23:
            item = 14608
            await p.add_inventory(p.server.items[item], notify=False)
        elif book == 24:
            item = 13054
            await p.add_inventory(p.server.items[item], notify=False)
        elif 15007 not in p.inventory:
            item = 15007
            await p.add_inventory(p.server.items[item], notify=False)

        await p.update(coins=p.coins + 1500).apply()

        await p.send_xt('rsba', item or '', 1500)
        await PenguinRedemptionBook.create(penguin_id=p.id, book_id=book)
    else:
        return await p.send_error(712)
