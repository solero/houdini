from houdini import handlers
from houdini.handlers import XTPacket
from houdini.commands import invoke_command_string


@handlers.handler(XTPacket('m', 'sm'))
@handlers.cooldown(.5)
async def handle_send_message(p, penguin_id: int, message):
    if penguin_id != p.data.id:
        return await p.close()

    if p.muted:
        for room_player in p.room.penguins:
            if room_player.data.moderator:
                await room_player.sendXt("mm", message, penguin_id)
        return

    await p.room.send_xt('sm', p.data.id, message)
    await invoke_command_string(p.server.commands, p, message)
