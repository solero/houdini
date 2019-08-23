from houdini import handlers
from houdini.handlers import XTPacket

from houdini.data.item import Item

import datetime


@handlers.handler(XTPacket('f', 'epfga'))
async def handle_get_agent_status(p):
    await p.send_xt('epfga', int(p.data.agent_status))


@handlers.handler(XTPacket('f', 'epfsa'))
@handlers.player_data_attribute(agent_status=False)
async def handle_set_agent_status(p):
    await p.data.update(agent_status=True).apply()
    await p.send_xt('epfsa', int(p.data.agent_status))


@handlers.handler(XTPacket('f', 'epfgf'))
async def handle_get_field_op_status(p):
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    if p.data.last_field_op.date() < monday:
        await p.data.update(field_op_status=0).apply()
    await p.send_xt('epfgf', p.data.field_op_status)


@handlers.handler(XTPacket('f', 'epfsf'))
@handlers.player_data_attribute(agent_status=True)
async def handle_set_field_op_status(p, field_op_status: int):
    if 2 >= field_op_status == p.data.field_op_status + 1:
        player_data = p.data.update(field_op_status=p.data.field_op_status + 1)
        if p.data.field_op_status == 2:
            player_data.update(career_medals=p.data.career_medals + 2)
            player_data.update(agent_medals=p.data.agent_medals + 2)

        await p.send_xt('epfsf', p.data.field_op_status)
        await player_data.update(last_field_op=datetime.datetime.now()).apply()


@handlers.handler(XTPacket('f', 'epfgr'))
async def handle_get_epf_points(p):
    await p.send_xt('epfgr', p.data.career_medals, p.data.agent_medals)


@handlers.handler(XTPacket('f', 'epfai'))
@handlers.player_data_attribute(agent_status=True)
async def handle_buy_epf_item(p, item: Item):
    if item.epf:
        if item.id in p.data.inventory:
            return await p.send_error(400)

        if p.data.agent_medals < item.cost:
            return await p.send_error(401)

        await p.add_epf_inventory(item)
