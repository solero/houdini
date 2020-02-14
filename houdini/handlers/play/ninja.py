from houdini import handlers
from houdini.handlers import XMLPacket, XTPacket, Priority
from houdini.data.ninja import PenguinCardCollection, CardCollection


@handlers.boot
async def cards_load(server):
    server.cards = await CardCollection.get_collection()
    server.logger.info(f'Loaded {len(server.cards)} ninja cards')


@handlers.handler(XMLPacket('login'), priority=Priority.Low)
@handlers.allow_once
async def load_ninja_inventory(p):
    p.cards = await PenguinCardCollection.get_collection(p.id)
