from houdini import handlers
from houdini.commands import has_command_prefix, invoke_command_string
from houdini.data.moderator import ChatFilterRuleCollection
from houdini.handlers import XTPacket
from houdini.handlers.play.moderation import moderator_ban


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

        consequence = next((c for w, c in p.server.chat_filter_words.items() if w in tokens), None)

        if consequence is not None:
            if consequence.ban:
                await moderator_ban(p, p.id, comment='Inappropriate language', message=message)
                return
            if consequence.filter:
                return

    if has_command_prefix(p.server.config.command_prefix, message):
        await p.room.send_xt('mm', message, p.id, f=lambda px: px.moderator)
        await invoke_command_string(p.server.commands, p, message)
    else:
        await p.room.send_xt('sm', p.id, message)

    p.logger.info(f'{p.username} said \'{message}\' in room \'{p.room.name}\'')
