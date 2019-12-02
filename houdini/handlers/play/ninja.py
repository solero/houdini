from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_server
from houdini.data.ninja import PenguinCardCollection


@handlers.handler(XTPacket('j', 'js'), after=handle_join_server)
@handlers.player_attribute(joined_world=True)
@handlers.allow_once
async def load_ninja_inventory(p):
    p.cards = await PenguinCardCollection.get_collection(p.id)
