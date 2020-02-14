from houdini import handlers
from houdini.handlers import XTPacket
from houdini.commands import invoke_command_string, has_command_prefix

from houdini.data.moderator import ChatFilterRuleCollection


@handlers.boot
async def filter_load(server):
    server.chat_filter_words = await ChatFilterRuleCollection.get_collection()
    server.logger.info(f'Loaded {len(server.chat_filter_words)} filter words')


@handlers.handler(XTPacket('m', 'sm'))
@handlers.cooldown(.5)
async def handle_send_message(p, penguin_id: int, message: str):
    if penguin_id != p.id:
        return await p.close()

    if p.muted:
        for penguin in p.room.penguins_by_id.values():
            if penguin.moderator:
                await penguin.send_xt("mm", message, penguin_id)
        return

    tokens = message.lower()
    for word, consequence in p.server.chat_filter_words.items():
        if word in tokens:
            if consequence.ban:
                return
            elif consequence.warn:
                return
            elif consequence.filter:
                return

    if has_command_prefix(p.server.config.command_prefix, message):
        await invoke_command_string(p.server.commands, p, message)
    else:
        await p.room.send_xt('sm', p.id, message)
