from houdini import handlers
from houdini.handlers import XTPacket
from houdini.commands import invoke_command_string, has_command_prefix


@handlers.handler(XTPacket('m', 'sm'))
@handlers.cooldown(.5)
async def handle_send_message(p, penguin_id: int, message: str):
    if penguin_id != p.data.id:
        return await p.close()

    if p.muted:
        for penguin in p.room.penguins_by_id.values():
            if penguin.data.moderator:
                await penguin.send_xt("mm", message, penguin_id)
        return

    if has_command_prefix(message):
        await invoke_command_string(p.server.commands, p, message)
    else:
        await p.room.send_xt('sm', p.data.id, message)
