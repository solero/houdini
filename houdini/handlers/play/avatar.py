from houdini import handlers
from houdini.handlers import XTPacket
from houdini.constants import ClientType


@handlers.handler(XTPacket('pt', 'spts'), client=ClientType.Vanilla)
@handlers.cooldown(1)
async def handle_player_transformation(p, transform_id: int):
    p.avatar = transform_id
    await p.room.send_xt('spts', p.id, transform_id)
