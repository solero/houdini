from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_room

from houdini.data.penguin import Penguin
from houdini.data.buddy import BuddyList, BuddyRequest
from houdini.constants import ClientType


async def update_player_presence(p):
    for buddy_id in p.data.buddies.keys():
        if buddy_id in p.server.penguins_by_id:
            buddy = p.server.penguins_by_id[buddy_id]
            await p.send_xt('bon', buddy.data.id, p.server.server_config['Id'], buddy.room.id)
            await buddy.send_xt('bon', p.data.id, p.server.server_config['Id'], p.room.id)

    for character_id in p.data.character_buddies.keys():
        if character_id in p.server.penguins_by_character_id:
            character = p.server.penguins_by_character_id[character_id]
            await p.send_xt('caon', character_id, p.server.server_config['Id'], character.room.id)

    if p.data.character is not None:
        for penguin in p.server.penguins_by_id.values():
            if p.data.character in penguin.data.character_buddies:
                await penguin.send_xt('caon', p.data.character, p.server.server_config['Id'], p.room.id)


@handlers.handler(XTPacket('j', 'jr'), after=handle_join_room, client=ClientType.Vanilla)
async def handle_send_room_presence(p):
    await update_player_presence(p)


@handlers.handler(XTPacket('b', 'gb'), client=ClientType.Vanilla)
@handlers.allow_once
async def handle_get_buddies(p):
    buddies_query = BuddyList.load(parent=Penguin.on(Penguin.id == BuddyList.buddy_id)).where(
        BuddyList.penguin_id == p.data.id)
    request_query = BuddyRequest.load(parent=Penguin.on(Penguin.id == BuddyRequest.requester_id)).where(
        BuddyRequest.penguin_id == p.data.id)

    buddies = []
    best_buddies = []
    characters = []
    best_characters = []

    async with p.server.db.transaction():
        buddy_list = buddies_query.gino.iterate()
        buddy_requests = request_query.gino.iterate()

        async for buddy in buddy_list:
            buddy_presence = int(buddy.buddy_id in p.server.penguins_by_id)
            buddies.append(f'{buddy.buddy_id}|{buddy.parent.nickname}|{buddy_presence}')

            if buddy.best_buddy:
                best_buddies.append(str(buddy.buddy_id))

        for character in p.data.character_buddies.values():
            character_presence = int(character.character_id in p.server.penguins_by_character_id)
            characters.append(f'{character.character_id}|{character_presence}')

            if character.best_buddy:
                best_characters.append(str(character.character_id))

        requests = [f'{request.requester_id}|{request.parent.nickname}' async for request in buddy_requests]

    best_friend_count = len(best_buddies) + len(best_characters)
    notification_aware = int(best_friend_count >= 1)
    best_friends_enabled = int((len(buddies) + len(characters)) >= 6)
    await p.send_xt('gs', best_friend_count, notification_aware, int(p.data.active), best_friends_enabled)

    await p.send_xt('gb', *buddies)
    await p.send_xt('pr', *requests)
    await p.send_xt('gc', *characters)

    if best_friends_enabled:
        await p.send_xt('gbf', *best_buddies)
        await p.send_xt('gbc', *best_characters)

    await update_player_presence(p)


@handlers.handler(XTPacket('b', 'gb'), client=ClientType.Legacy)
@handlers.allow_once
async def handle_get_buddies_legacy(p):
    buddies_query = BuddyList.load(parent=Penguin.on(Penguin.id == BuddyList.buddy_id)).where(
        BuddyList.penguin_id == p.data.id)

    buddies = []

    async with p.server.db.transaction():
        buddy_list = buddies_query.gino.iterate()

        async for buddy in buddy_list:
            buddy_presence = int(buddy.buddy_id in p.server.penguins_by_id)
            buddies.append(f'{buddy.buddy_id}|{buddy.parent.nickname}|{buddy_presence}')

    await p.send_xt('gb', *buddies)
    await update_player_presence(p)


@handlers.handler(XTPacket('b', 'bf'), client=ClientType.Legacy)
async def handle_find_buddy(p, buddy_id: int):
    if buddy_id in p.data.buddies and buddy_id in p.server.penguins_by_id:
        buddy = p.server.penguins_by_id[buddy_id]
        await p.send_xt('bf', buddy.room.id)


@handlers.handler(XTPacket('b', 'br'))
@handlers.cooldown(.5)
async def handle_buddy_request(p, buddy_id: int):
    if buddy_id not in p.data.buddies:
        if buddy_id in p.server.penguins_by_id:
            buddy = p.server.penguins_by_id[buddy_id]

            if buddy.client_type == ClientType.Vanilla and p.data.id not in buddy.data.buddy_requests:
                await buddy.data.buddy_requests.set(p.data.id)
            elif p.data.id not in buddy.buddy_requests:
                buddy.buddy_requests.add(p.data.id)
            else:
                return

            await buddy.send_xt('br', p.data.id, p.data.nickname)
        else:
            await BuddyRequest.create(penguin_id=buddy_id, requester_id=p.data.id)


@handlers.handler(XTPacket('b', 'ba'))
async def handle_buddy_accept(p, buddy_id: int):
    if buddy_id in p.data.buddy_requests:
        await p.data.buddy_requests.delete(buddy_id)
    elif buddy_id in p.buddy_requests:
        p.buddy_requests.remove(buddy_id)
    else:
        return

    await p.data.buddies.set(buddy_id)

    if buddy_id in p.server.penguins_by_id:
        buddy = p.server.penguins_by_id[buddy_id]
        await buddy.data.buddies.set(p.data.id)
        await buddy.send_xt('ba', p.data.id, p.data.nickname, 1)
        await p.send_xt('ba', buddy.data.id, buddy.data.nickname, 1)

        if p.client_type == ClientType.Vanilla:
            await p.send_xt('bon', buddy.data.id, p.server.server_config['Id'], buddy.room.id)
        if buddy.client_type == ClientType.Vanilla:
            await buddy.send_xt('bon', p.data.id, p.server.server_config['Id'], p.room.id)
    else:
        await BuddyList.create(penguin_id=buddy_id, buddy_id=p.data.id)
        nickname = await Penguin.select('nickname').where(Penguin.id == buddy_id).gino.scalar()
        await p.send_xt('ba', buddy_id, nickname, 0)


@handlers.handler(XTPacket('b', 'rb'))
async def handle_buddy_remove(p, buddy_id: int):
    if buddy_id in p.data.buddies:
        await p.data.buddies.delete(buddy_id)
        await p.send_xt('rb', buddy_id)
        if buddy_id in p.server.penguins_by_id:
            buddy = p.server.penguins_by_id[buddy_id]
            await buddy.send_xt('rb', p.data.id)
            await buddy.data.buddies.delete(p.data.id)
        else:
            await BuddyList.delete.where((BuddyList.penguin_id == buddy_id) &
                                         (BuddyList.buddy_id == p.data.id)).gino.status()


@handlers.handler(XTPacket('b', 'cr'), client=ClientType.Vanilla)
async def handle_character_request(p, character_id: int):
    if character_id in p.server.characters and character_id not in p.data.character_buddies:
        character = p.server.characters[character_id]
        await p.data.character_buddies.set(character_id)
        await p.send_xt('cr', character_id, 0)
        await p.send_xt('caon', character_id, p.server.server_config['Id'], p.room.id)


@handlers.handler(XTPacket('b', 'rr'), client=ClientType.Vanilla)
async def handle_buddy_reject(p, buddy_id: int):
    await p.data.buddy_requests.delete(buddy_id)


@handlers.handler(XTPacket('b', 'tbf'), client=ClientType.Vanilla)
async def handle_toggle_best_friend(p, buddy_id: int):
    if buddy_id in p.data.buddies:
        buddy_record = p.data.buddies[buddy_id]
        await buddy_record.update(best_buddy=not buddy_record.best_buddy).apply()


@handlers.handler(XTPacket('b', 'tbc'), client=ClientType.Vanilla)
async def handle_toggle_best_character(p, character_id: int):
    if character_id in p.data.character_buddies:
        character_buddy_record = p.data.character_buddies[character_id]
        await character_buddy_record.update(best_buddy=not character_buddy_record.best_buddy).apply()


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_buddy(p):
    if p.data.character is not None:
        del p.server.penguins_by_character_id[p.data.character]

        for penguin in p.server.penguins_by_id.values():
            if p.data.character in penguin.data.character_buddies:
                await penguin.send_xt('caof', p.data.character)

    for buddy_id in p.data.buddies:
        if buddy_id in p.server.penguins_by_id:
            await p.server.penguins_by_id[buddy_id].send_xt('bof', p.data.id)
