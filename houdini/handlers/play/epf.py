import datetime
import random
import time

from houdini import handlers
from houdini.constants import ClientType
from houdini.data.item import Item
from houdini.data.mail import PenguinPostcard
from houdini.data.penguin import EpfComMessage
from houdini.handlers import XTPacket
from houdini.handlers.play.mail import handle_start_mail_engine


async def get_com_messages(p):
    async with p.server.db.transaction():
        messages = []
        async for message in EpfComMessage.query.order_by(EpfComMessage.date.desc()).gino.iterate():
            messages.append(f'{message.message}|{int(time.mktime(message.date.timetuple()))}|{message.character_id}')
        return '%'.join(messages)


@handlers.handler(XTPacket('l', 'mst'), before=handle_start_mail_engine)
async def handle_send_job_mail(p):
    postcards = []
    if p.is_legacy_client and not p.agent_status and random.random() < 0.1:
        epf_invited = await PenguinPostcard.query.where(
            (PenguinPostcard.penguin_id == p.id) & ((PenguinPostcard.postcard_id == 112)
                                                    | (PenguinPostcard.postcard_id == 47))).gino.scalar()
        if not epf_invited:
            postcards.append({
                'penguin_id': p.id,
                'postcard_id': 112
            })

    last_paycheck = p.last_paycheck.date()
    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)
    last_paycheck = last_paycheck.replace(day=1)

    player_data = p.update()
    while last_paycheck < first_day_of_month:
        last_paycheck = last_paycheck + datetime.timedelta(days=32)
        last_paycheck = last_paycheck.replace(day=1)
        send_date = last_paycheck
        if 428 in p.inventory:
            postcards.append({
                'penguin_id': p.id,
                'postcard_id': 172,
                'send_date': send_date
            })
            player_data.update(coins=p.coins + 250)
        if p.agent_status:
            postcards.append({
                'penguin_id': p.id,
                'postcard_id': 184,
                'send_date': send_date
            })
            player_data.update(coins=p.coins + 350)

    await player_data.update(last_paycheck=last_paycheck).apply()
    if postcards:
        await PenguinPostcard.insert().values(postcards).gino.status()


@handlers.handler(XTPacket('f', 'epfga'))
async def handle_get_agent_status(p):
    await p.send_xt('epfga', int(p.agent_status))


@handlers.handler(XTPacket('f', 'epfsa'))
@handlers.player_attribute(agent_status=False)
async def handle_set_agent_status(p):
    await p.update(agent_status=True).apply()
    await p.send_xt('epfsa', int(p.agent_status))


@handlers.handler(XTPacket('f', 'epfgf'), pre_login=True)
@handlers.player_attribute(joined_world=True)
async def handle_get_field_op_status(p):
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    if p.last_field_op.date() < monday:
        await p.update(field_op_status=0).apply()
    await p.send_xt('epfgf', p.field_op_status)


@handlers.handler(XTPacket('f', 'epfsf'))
@handlers.player_attribute(agent_status=True)
async def handle_set_field_op_status(p, field_op_status: int):
    if 2 >= field_op_status == p.field_op_status + 1:
        player_data = p.update(field_op_status=p.field_op_status + 1)
        if p.field_op_status == 2:
            player_data.update(career_medals=p.career_medals + 2)
            player_data.update(agent_medals=p.agent_medals + 2)

        await p.send_xt('epfsf', p.field_op_status)
        await player_data.update(last_field_op=datetime.datetime.now()).apply()


@handlers.handler(XTPacket('f', 'epfgr'))
async def handle_get_epf_points(p):
    await p.send_xt('epfgr', p.career_medals, p.agent_medals)


@handlers.handler(XTPacket('f', 'epfai'))
@handlers.player_attribute(agent_status=True)
async def handle_buy_epf_item(p, item: Item):
    if item.epf:
        if item.id in p.inventory:
            return await p.send_error(400)

        if p.agent_medals < item.cost:
            return await p.send_error(405)

        await p.add_epf_inventory(item)


@handlers.handler(XTPacket('f', 'epfgm'), client=ClientType.Vanilla)
@handlers.allow_once
async def handle_get_com_messages(p):
    unread_com_message = await EpfComMessage.query.where(
        EpfComMessage.date > p.com_message_read_date).gino.scalar()
    if unread_com_message:
        p.server.cache.delete('com_messages')
        await p.update(com_message_read_date=datetime.datetime.now()).apply()
    com_messages = p.server.cache.get('com_messages')
    com_messages = await get_com_messages(p) if com_messages is None else com_messages
    p.server.cache.set('com_messages', com_messages)
    if com_messages:
        await p.send_xt('epfgm', int(bool(unread_com_message)), com_messages)
    else:
        await p.send_xt('epfgm', int(bool(unread_com_message)))


@handlers.handler(XTPacket('f', 'epfgrantreward'))
@handlers.cooldown(60)
@handlers.player_attribute(agent_status=True)
async def handle_epf_grant_reward(p, medals: int):
    medals = min(45, medals)
    await p.update(career_medals=p.career_medals + medals,
                   agent_medals=p.agent_medals + medals).apply()
    await p.send_xt('epfgr', p.career_medals, p.agent_medals)


@handlers.handler(XTPacket('epfsf', ext='z'))
async def handle_epf_medal_check(p, stamp_id: int):
    if not p.agent_status:
        await p.send_xt('epfsf', 'naa')

    if stamp_id not in p.stamps:
        await p.send_xt('epfsf', 'nem', stamp_id)
    else:
        await p.send_xt('epfsf', 'ahm')
