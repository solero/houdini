import zope.interface
from zope.interface import implementer


class IConverter(zope.interface.Interface):

    description = zope.interface.Attribute("""A short description of the purpose of the converter""")

    async def convert(self):
        raise NotImplementedError('Converter must derive this class!')


class Converter:

    __slots__ = ['p', 'argument']

    def __init__(self, p, argument):
        self.p = p
        self.argument = argument


@implementer(IConverter)
class CredentialsConverter(Converter):

    description = """Used for obtaining login credentials from XML login data"""

    async def convert(self):
        username = self.argument[0][0].text
        password = self.argument[0][1].text
        return username, password


@implementer(IConverter)
class VersionChkConverter(Converter):

    description = """Used for checking the verChk version number"""

    async def convert(self):
        return self.argument[0].get('v')


@implementer(IConverter)
class ConnectedPenguinConverter(Converter):

    description = """Converts a penguin ID into a live penguin instance 
                     or none if the player is offline"""

    async def convert(self):
        penguin_id = int(self.argument)
        if penguin_id in self.p.server.penguins_by_id:
            return self.p.server.penguins_by_id[penguin_id]
        return None


@implementer(IConverter)
class ConnectedIglooConverter(Converter):

    description = """Converts a penguin ID into a live igloo instance or 
                    none if it's not available"""

    async def convert(self):
        igloo_id = int(self.argument)
        if igloo_id in self.p.server.igloo_map:
            return self.p.server.igloo_map[igloo_id]
        return None


@implementer(IConverter)
class RoomConverter(Converter):

    description = """Converts a room ID into a Houdini.Data.Room instance"""

    async def convert(self):
        room_id = int(self.argument)
        if room_id in self.p.server.rooms:
            return self.p.server.rooms[room_id]
        return None


@implementer(IConverter)
class ItemConverter(Converter):

    description = """Converts an item ID into a Houdini.Data.Item instance"""

    async def convert(self):
        item_id = int(self.argument)
        if item_id in self.p.server.items:
            return self.p.server.items[item_id]
        return None


@implementer(IConverter)
class IglooConverter(Converter):

    description = """Converts an igloo ID into a Houdini.Data.Igloo instance"""

    async def convert(self):
        igloo_id = int(self.argument)
        if igloo_id in self.p.server.igloos:
            return self.p.server.igloos[igloo_id]
        return None


@implementer(IConverter)
class FurnitureConverter(Converter):

    description = """Converts a furniture ID into a Houdini.Data.Furniture instance"""

    async def convert(self):
        furniture_id = int(self.argument)
        if furniture_id in self.p.server.furniture:
            return self.p.server.furniture[furniture_id]
        return None


@implementer(IConverter)
class FlooringConverter(Converter):

    description = """Converts a flooring ID into a Houdini.Data.Flooring instance"""

    async def convert(self):
        flooring_id = int(self.argument)
        if flooring_id in self.p.server.flooring:
            return self.p.server.flooring[flooring_id]
        return None


@implementer(IConverter)
class StampConverter(Converter):

    description = """Converts a stamp ID into a Houdini.Data.Stamp instance"""

    async def convert(self):
        stamp_id = int(self.argument)
        if stamp_id in self.p.server.stamps:
            return self.p.server.stamps[stamp_id]
        return None


@implementer(IConverter)
class VerticalConverter(Converter):

    description = """Converts vertically separated values into an int list"""

    async def convert(self):
        return map(int, self.argument.split('|'))


@implementer(IConverter)
class CommaConverter(Converter):

    description = """Converts comma separated values into an int list"""

    async def convert(self):
        return map(int, self.argument.split(','))
