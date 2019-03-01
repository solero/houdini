from Houdini.Handlers import Handlers, XTPacket
from Houdini.Converters import RoomConverter


@Handlers.handler(XTPacket('j', 'js'))
async def handle_join_world(p, is_moderator: bool, is_mascot: bool, is_member: bool):
    print(p, is_moderator, is_mascot, is_member)


@Handlers.handler(XTPacket('j', 'jr'))
async def handle_join_room(p, room: RoomConverter):
    print(room)
