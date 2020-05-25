from houdini import handlers
from houdini.constants import ClientType
from houdini.data.buddy import BuddyList, BuddyListCollection, BuddyRequest, BuddyRequestCollection, \
    CharacterBuddyCollection, CharacterCollection
from houdini.data.penguin import Penguin
from houdini.handlers import Priority, XMLPacket, XTPacket
from houdini.handlers.play.navigation import handle_join_room


async def update_player_presence(p):
    for buddy_id in p.buddies.keys():
        if buddy_id in p.server.penguins_by_id:
            buddy = p.server.penguins_by_id[buddy_id]
            await p.send_xt('bon', buddy.id, p.server.config.id, buddy.room.id)
            await buddy.send_xt('bon', p.id, p.server.config.id, p.room.id)

    for character_id in p.character_buddies.keys():
        if character_id in p.server.penguins_by_character_id:
            character = p.server.penguins_by_character_id[character_id]
            await p.send_xt('caon', character_id, p.server.config.id, character.room.id)

    if p.character is not None:
        for penguin in p.server.penguins_by_id.values():
            if p.character in penguin.character_buddies:
                await penguin.send_xt('caon', p.character, p.server.config.id, p.room.id)


@handlers.boot
async def characters_load(server):
    server.characters = await CharacterCollection.get_collection()
    server.logger.info(f'Loaded {len(server.characters)} characters')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_buddy_inventory(p):
    p.buddies = await BuddyListCollection.get_collection(p.id)
    p.buddy_requests = await BuddyRequestCollection.get_collection(p.id)
    p.character_buddies = await CharacterBuddyCollection.get_collection(p.id)


@handlers.handler(XTPacket('j', 'jr'), after=handle_join_room, client=ClientType.Vanilla)
async def handle_send_room_presence(p):
    await update_player_presence(p)


@handlers.handler(XTPacket('b', 'gb'), client=ClientType.Vanilla)
@handlers.allow_once
async def handle_get_buddies(p):
    buddies_query = BuddyList.load(parent=Penguin.on(Penguin.id == BuddyList.buddy_id)).where(
        BuddyList.penguin_id == p.id)
    request_query = BuddyRequest.load(parent=Penguin.on(Penguin.id == BuddyRequest.requester_id)).where(
        BuddyRequest.penguin_id == p.id)

    buddies = []
    best_buddies = []
    characters = []
    best_characters = []

    async with p.server.db.transaction():
        buddy_list = buddies_query.gino.iterate()
        buddy_requests = request_query.gino.iterate()

        async for buddy in buddy_list:
            buddy_presence = int(buddy.buddy_id in p.server.penguins_by_id)
            buddies.append(f'{buddy.buddy_id}|{buddy.parent.safe_nickname(p.server.config.lang)}|{buddy_presence}')

            if buddy.best_buddy:
                best_buddies.append(str(buddy.buddy_id))

        for character in p.character_buddies.values():
            character_presence = int(character.character_id in p.server.penguins_by_character_id)
            characters.append(f'{character.character_id}|{character_presence}')

            if character.best_buddy:
                best_characters.append(str(character.character_id))

        requests = [f'{request.requester_id}|{request.parent.safe_nickname(p.server.config.lang)}'
                    async for request in buddy_requests]

    best_friend_count = len(best_buddies) + len(best_characters)
    notification_aware = int(best_friend_count >= 1)
    best_friends_enabled = int((len(buddies) + len(characters)) >= 6)
    await p.send_xt('gs', best_friend_count, notification_aware, int(p.active), best_friends_enabled)

    await p.send_xt('gb', *buddies)
    await p.send_xt('pbr', *requests)
    await p.send_xt('gc', *characters)

    if best_friends_enabled:
        await p.send_xt('gbf', *best_buddies)
        await p.send_xt('gbc', *best_characters)

    await update_player_presence(p)


@handlers.handler(XTPacket('b', 'gb'), client=ClientType.Legacy)
@handlers.allow_once
async def handle_get_buddies_legacy(p):
    buddies_query = BuddyList.load(parent=Penguin.on(Penguin.id == BuddyList.buddy_id)).where(
        BuddyList.penguin_id == p.id)

    buddies = []

    async with p.server.db.transaction():
        buddy_list = buddies_query.gino.iterate()

        async for buddy in buddy_list:
            buddy_presence = int(buddy.buddy_id in p.server.penguins_by_id)
            buddies.append(f'{buddy.buddy_id}|{buddy.parent.safe_nickname(p.server.config.lang)}|{buddy_presence}')

    await p.send_xt('gb', *buddies)
    await update_player_presence(p)


@handlers.handler(XTPacket('b', 'bf'), client=ClientType.Legacy)
async def handle_find_buddy(p, buddy_id: int):
    if buddy_id in p.buddies and buddy_id in p.server.penguins_by_id:
        buddy = p.server.penguins_by_id[buddy_id]
        await p.send_xt('bf', buddy.room.external_id if buddy.room.igloo else buddy.room.id)


@handlers.handler(XTPacket('b', 'br'))
@handlers.cooldown(.5)
async def handle_buddy_request(p, buddy_id: int):
    if buddy_id not in p.buddies:
        if buddy_id in p.server.penguins_by_id:
            buddy = p.server.penguins_by_id[buddy_id]

            if buddy.client_type == ClientType.Vanilla and p.id not in buddy.buddy_requests:
                await buddy.buddy_requests.insert(requester_id=p.id)
            elif p.id not in buddy.legacy_buddy_requests:
                buddy.legacy_buddy_requests.add(p.id)
            else:
                return

            await buddy.send_xt('br', p.id, p.safe_name)
        else:
            await BuddyRequest.create(penguin_id=buddy_id, requester_id=p.id)


@handlers.handler(XTPacket('b', 'ba'))
async def handle_buddy_accept(p, buddy_id: int):
    if buddy_id in p.buddy_requests:
        await p.buddy_requests.delete(buddy_id)
    elif buddy_id in p.legacy_buddy_requests:
        p.legacy_buddy_requests.remove(buddy_id)
    else:
        return

    if buddy_id in p.buddies:
        return

    await p.buddies.insert(buddy_id=buddy_id)

    if buddy_id in p.server.penguins_by_id:
        buddy = p.server.penguins_by_id[buddy_id]
        await buddy.buddies.insert(buddy_id=p.id)
        await buddy.send_xt('ba', p.id, p.safe_name, 1)
        await p.send_xt('ba', buddy.id, buddy.safe_name, 1)

        if p.client_type == ClientType.Vanilla:
            await p.send_xt('bon', buddy.id, p.server.config.id, buddy.room.id)
        if buddy.client_type == ClientType.Vanilla:
            await buddy.send_xt('bon', p.id, p.server.config.id, p.room.id)
    else:
        await BuddyList.create(penguin_id=buddy_id, buddy_id=p.id)
        nickname = await Penguin.select('nickname').where(Penguin.id == buddy_id).gino.scalar()
        await p.send_xt('ba', buddy_id, nickname, 0)


@handlers.handler(XTPacket('b', 'rb'))
async def handle_buddy_remove(p, buddy_id: int):
    if buddy_id in p.buddies:
        await p.buddies.delete(buddy_id)
        await p.send_xt('rb', buddy_id)
        if buddy_id in p.server.penguins_by_id:
            buddy = p.server.penguins_by_id[buddy_id]
            await buddy.send_xt('rb', p.id)
            await buddy.buddies.delete(p.id)
        else:
            await BuddyList.delete.where((BuddyList.penguin_id == buddy_id) &
                                         (BuddyList.buddy_id == p.id)).gino.status()


@handlers.handler(XTPacket('b', 'cr'), client=ClientType.Vanilla)
async def handle_character_request(p, character_id: int):
    if character_id in p.server.characters and character_id not in p.character_buddies:
        await p.character_buddies.insert(character_id=character_id)
        await p.send_xt('cr', character_id, 0)
        await p.send_xt('caon', character_id, p.server.config.id, p.room.id)


@handlers.handler(XTPacket('b', 'rr'), client=ClientType.Vanilla)
async def handle_buddy_reject(p, buddy_id: int):
    await p.buddy_requests.delete(buddy_id)


@handlers.handler(XTPacket('b', 'tbf'), client=ClientType.Vanilla)
async def handle_toggle_best_friend(p, buddy_id: int):
    if buddy_id in p.buddies:
        buddy_record = p.buddies[buddy_id]
        await buddy_record.update(best_buddy=not buddy_record.best_buddy).apply()


@handlers.handler(XTPacket('b', 'tbc'), client=ClientType.Vanilla)
async def handle_toggle_best_character(p, character_id: int):
    if character_id in p.character_buddies:
        character_buddy_record = p.character_buddies[character_id]
        await character_buddy_record.update(best_buddy=not character_buddy_record.best_buddy).apply()


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_buddy(p):
    if p.character is not None:
        del p.server.penguins_by_character_id[p.character]

        for penguin in p.server.penguins_by_id.values():
            if p.character in penguin.character_buddies:
                await penguin.send_xt('caof', p.character)

    for buddy_id in p.buddies:
        if buddy_id in p.server.penguins_by_id:
            await p.server.penguins_by_id[buddy_id].send_xt('bof', p.id)
