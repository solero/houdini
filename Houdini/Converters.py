from abc import ABC
from abc import abstractmethod

import asyncio


class IConverter(ABC):

    @property
    @abstractmethod
    def description(self):
        """A short description of the purpose of the converter"""

    @abstractmethod
    async def convert(self, ctx):
        """The actual converter implementation"""


class CredentialsConverter(IConverter):

    description = """Used for obtaining login credentials from XML login data"""

    async def convert(self, ctx):
        username = ctx.argument[0][0].text
        password = ctx.argument[0][1].text
        return username, password


class VersionChkConverter(IConverter):

    description = """Used for checking the verChk version number"""

    async def convert(self, ctx):
        return ctx.argument[0].get('v')


class ConnectedPenguinConverter(IConverter):

    description = """Converts a penguin ID into a live penguin instance 
                     or none if the player is offline"""

    async def convert(self, ctx):
        penguin_id = int(ctx.argument)
        if penguin_id in ctx.p.server.penguins_by_id:
            return ctx.p.server.penguins_by_id[penguin_id]
        return None


class ConnectedIglooConverter(IConverter):

    description = """Converts a penguin ID into a live igloo instance or 
                    none if it's not available"""

    async def convert(self, ctx):
        igloo_id = int(ctx.argument)
        if igloo_id in ctx.p.server.igloo_map:
            return ctx.p.server.igloo_map[igloo_id]
        return None


class RoomConverter(IConverter):

    description = """Converts a room ID into a Houdini.Data.Room instance"""

    async def convert(self, ctx):
        room_id = int(ctx.argument)
        if room_id in ctx.p.server.rooms:
            return ctx.p.server.rooms[room_id]
        return None


class ItemConverter(IConverter):

    description = """Converts an item ID into a Houdini.Data.Item instance"""

    async def convert(self, ctx):
        item_id = int(ctx.argument)
        if item_id in ctx.p.server.items:
            return ctx.p.server.items[item_id]
        return None


class IglooConverter(IConverter):

    description = """Converts an igloo ID into a Houdini.Data.Igloo instance"""

    async def convert(self, ctx):
        igloo_id = int(ctx.argument)
        if igloo_id in ctx.p.server.igloos:
            return ctx.p.server.igloos[igloo_id]
        return None


class FurnitureConverter(IConverter):

    description = """Converts a furniture ID into a Houdini.Data.Furniture instance"""

    async def convert(self, ctx):
        furniture_id = int(ctx.argument)
        if furniture_id in ctx.p.server.furniture:
            return ctx.p.server.furniture[furniture_id]
        return None


class FlooringConverter(IConverter):

    description = """Converts a flooring ID into a Houdini.Data.Flooring instance"""

    async def convert(self, ctx):
        flooring_id = int(ctx.argument)
        if flooring_id in ctx.p.server.flooring:
            return ctx.p.server.flooring[flooring_id]
        return None


class StampConverter(IConverter):

    description = """Converts a stamp ID into a Houdini.Data.Stamp instance"""

    async def convert(self, ctx):
        stamp_id = int(ctx.argument)
        if stamp_id in ctx.p.server.stamps:
            return ctx.p.server.stamps[stamp_id]
        return None


class SeparatorConverter(IConverter):

    __slots__ = ['separator', 'mapper']

    description = """Converts strings separated by char into a list of type"""

    def __init__(self, separator='|', mapper=int):
        self.separator = separator
        self.mapper = mapper

    async def convert(self, ctx):
        return map(self.mapper, ctx.argument.split(self.separator))


class UnionConverter(IConverter):

    __slots__ = ['types']

    description = """Converts union type into argument"""

    def __init__(self, *types, skip_none=False):
        self.types = types
        self.skip_none = skip_none

    async def convert(self, ctx):
        for converter in self.types:
            try:
                result = await do_conversion(converter, ctx)
                if not self.skip_none or result is not None:
                    return result
            except ValueError:
                continue


class GreedyConverter(IConverter):

    __slots__ = ['target']

    description = """Converts until it can't any longer"""

    def __init__(self, target=int):
        self.target = target

    async def convert(self, ctx):
        converted = []
        try:
            converted.append(await do_conversion(self.target, ctx))
            for ctx.argument in ctx.arguments:
                converted.append(await do_conversion(self.target, ctx))
        except ValueError:
            return converted
        return converted


class OptionalConverter(IConverter):

    __slots__ = ['target']

    description = """Tries to convert but ignores if it can't"""

    def __init__(self, target=int):
        self.target = target

    async def convert(self, ctx):
        try:
            return await do_conversion(self.target, ctx)
        except ValueError:
            return ctx.component.default


class _ConverterContext:

    __slots__ = ['component', 'arguments', 'argument', 'p']

    def __init__(self, component, arguments, argument, p):
        self.component = component
        self.arguments = arguments
        self.argument = argument
        self.p = p


def get_converter(component):
    if component.annotation is component.empty:
        return str
    return component.annotation


async def do_conversion(converter, ctx):
    if issubclass(type(converter), IConverter) and not isinstance(converter, IConverter):
        converter = converter()
    if isinstance(converter, IConverter):
        if asyncio.iscoroutinefunction(converter.convert):
            return await converter.convert(ctx)
        return converter.convert(ctx)
    return converter(ctx.argument)
