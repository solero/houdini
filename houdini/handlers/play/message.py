from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.moderation import moderator_ban

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

    if p.server.chat_filter_words:
        tokens = message.lower().split()

        word, consequence = next(((w, c) for w, c in p.server.chat_filter_words.items() if w in tokens))

        if consequence.ban:
            return await moderator_ban(p, p.id, comment='Inappropriate language', message=message)
        elif consequence.warn:
            return
        elif consequence.filter:
            return

    if has_command_prefix(p.server.config.command_prefix, message):
        await invoke_command_string(p.server.commands, p, message)
    else:
        await p.room.send_xt('sm', p.id, message)
