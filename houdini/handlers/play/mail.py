import time

from houdini import handlers
from houdini.data import db
from houdini.data.buddy import IgnoreList
from houdini.data.mail import PenguinPostcard, PostcardCollection
from houdini.data.penguin import Penguin
from houdini.handlers import XTPacket


@handlers.boot
async def postcards_load(server):
    server.postcards = await PostcardCollection.get_collection()
    server.logger.info(f'Loaded {len(server.postcards)} postcards')


@handlers.handler(XTPacket('l', 'mst'))
@handlers.allow_once
async def handle_start_mail_engine(p):
    mail_count = await db.select([db.func.count(PenguinPostcard.id)]).where(
        PenguinPostcard.penguin_id == p.id).gino.scalar()
    unread_mail_count = await db.select([db.func.count(PenguinPostcard.id)]).where(
        (PenguinPostcard.penguin_id == p.id)
        & (PenguinPostcard.has_read == False)).gino.scalar()
    await p.send_xt('mst', unread_mail_count, mail_count)


@handlers.handler(XTPacket('l', 'mg'))
@handlers.allow_once
async def handle_get_mail(p):
    mail_query = PenguinPostcard.load(parent=Penguin.on(Penguin.id == PenguinPostcard.sender_id)).where(
        PenguinPostcard.penguin_id == p.id).order_by(
        PenguinPostcard.send_date.desc())

    postcards = []
    async with p.server.db.transaction():
        async for postcard in mail_query.gino.iterate():
            sender_name, sender_id = ('sys', 0) if postcard.sender_id is None else (
                postcard.parent.safe_nickname(p.server.config.lang), postcard.sender_id)
            sent_timestamp = int(time.mktime(postcard.send_date.timetuple()))
            postcards.append(f'{sender_name}|{sender_id}|{postcard.postcard_id}|'
                             f'{postcard.details}|{sent_timestamp}|{postcard.id}|{int(postcard.has_read)}')
    await p.send_xt('mg', *postcards)


@handlers.handler(XTPacket('l', 'ms'))
@handlers.depends_on_packet(XTPacket('l', 'mst'))
@handlers.cooldown(2)
async def handle_send_mail(p, recipient_id: int, postcard_id: int):
    if p.coins < 10:
        return await p.send_xt('ms', p.coins, 0)
    mail_count = await db.select([db.func.count(PenguinPostcard.id)]).where(
        PenguinPostcard.penguin_id == recipient_id).gino.scalar()
    if recipient_id in p.server.penguins_by_id:
        recipient = p.server.penguins_by_id[recipient_id]
        if p.id in recipient.ignore:
            return await p.send_xt('ms', p.coins, 1)
        if mail_count >= 100:
            return await p.send_xt('ms', p.coins, 0)
        postcard = await PenguinPostcard.create(penguin_id=recipient_id, sender_id=p.id,
                                                postcard_id=postcard_id)
        sent_timestamp = int(time.mktime(postcard.send_date.timetuple()))
        await recipient.send_xt('mr', p.safe_name, p.id, postcard_id, '', sent_timestamp, postcard.id)
    else:
        ignored = await IgnoreList.query.where((IgnoreList.penguin_id == recipient_id)
                                               & (IgnoreList.ignore_id == p.id)).gino.scalar()
        if ignored is not None:
            return await p.send_xt('ms', p.coins, 1)
        if mail_count >= 100:
            return await p.send_xt('ms', p.coins, 0)
        await PenguinPostcard.create(penguin_id=recipient_id, sender_id=p.id, postcard_id=postcard_id)
    await p.update(coins=p.coins - 10).apply()
    return await p.send_xt('ms', p.coins, 1)


@handlers.handler(XTPacket('l', 'mc'))
@handlers.depends_on_packet(XTPacket('l', 'mst'))
async def handle_mail_checked(p):
    await PenguinPostcard.update.values(has_read=True).where(
        PenguinPostcard.penguin_id == p.id).gino.status()


@handlers.handler(XTPacket('l', 'md'))
@handlers.depends_on_packet(XTPacket('l', 'mst'))
async def handle_delete_mail(p, postcard_id: int):
    await PenguinPostcard.delete.where((PenguinPostcard.penguin_id == p.id)
                                       & (PenguinPostcard.id == postcard_id)).gino.status()


@handlers.handler(XTPacket('l', 'mdp'))
@handlers.depends_on_packet(XTPacket('l', 'mst'))
async def handle_delete_mail_from_user(p, sender_id: int):
    sender_id = None if sender_id == 0 else sender_id
    await PenguinPostcard.delete.where((PenguinPostcard.penguin_id == p.id)
                                       & (PenguinPostcard.sender_id == sender_id)).gino.status()
    mail_count = await db.select([db.func.count(PenguinPostcard.id)]).where(
        PenguinPostcard.penguin_id == p.id).gino.scalar()
    await p.send_xt('mdp', mail_count)
