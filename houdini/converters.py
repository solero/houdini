from abc import ABC
from abc import abstractmethod

import asyncio
import itertools
import inspect
import collections

from houdini.cooldown import CooldownError

from houdini.data.room import Room
from houdini.data.item import Item
from houdini.data.igloo import Igloo, Furniture, Flooring, Location
from houdini.data.stamp import Stamp
from houdini.data.pet import Puffle, PenguinPuffle


class ChecklistError(Exception):
    """Raised when a checklist fails"""


class _ArgumentDeserializer:
    __slots__ = ['name', 'components', 'callback', 'parent', 'pass_raw', 'cooldown',
                 'checklist', 'instance', 'alias', 'rest_raw', 'string_delimiter',
                 'string_separator', '_signature', '_arguments', '_exception_callback',
                 '_exception_class']

    def __init__(self, name, callback, **kwargs):
        self.callback = callback

        self.name = callback.__name__ if name is None else name
        self.cooldown = kwargs.get('cooldown')
        self.checklist = kwargs.get('checklist', [])
        self.rest_raw = kwargs.get('rest_raw', False)
        self.string_delimiter = kwargs.get('string_delimiter', [])
        self.string_separator = kwargs.get('string_separator', str())

        self.instance = None

        self._signature = list(inspect.signature(self.callback).parameters.values())
        self._arguments = inspect.getfullargspec(self.callback)

        self._exception_callback = None
        self._exception_class = Exception

        if self.rest_raw:
            self._signature = self._signature[:-1]

    def _can_run(self, p):
        return True if not self.checklist else all(predicate(self, p) for predicate in self.checklist)

    async def _check_cooldown(self, p):
        if self.cooldown is not None:
            bucket = self.cooldown.get_bucket(p)
            if bucket.is_cooling:
                if self.cooldown.callback is not None:
                    if self.instance:
                        await self.cooldown.callback(self.instance, p)
                    else:
                        await self.cooldown.callback(p)
                else:
                    raise CooldownError(f'{p} invoked listener during cooldown')

    def _check_list(self, p):
        if not self._can_run(p):
            raise ChecklistError('Could not invoke listener due to checklist failure')

    def _consume_separated_string(self, ctx):
        if ctx.argument and ctx.argument[0] in self.string_delimiter:
            while not ctx.argument.endswith(ctx.argument[0]):
                ctx.argument += self.string_separator + next(ctx.arguments)
            ctx.argument = ctx.argument[1:-1]

    def error(self, exception_class=Exception):
        def decorator(exception_callback):
            self._exception_callback = exception_callback
            self._exception_class = exception_class
        return decorator

    async def _deserialize(self, p, data):
        handler_call_arguments = [self.instance, p] if self.instance is not None else [p]
        handler_call_keywords = {}

        arguments = itertools.islice(data, len(data) - len(self._arguments.kwonlyargs))
        keyword_arguments = itertools.islice(data, len(data) - len(self._arguments.kwonlyargs), len(data))

        ctx = _ConverterContext(None, arguments, None, p)
        for ctx.component in itertools.islice(self._signature, len(handler_call_arguments), len(self._signature)):
            if ctx.component.annotation is ctx.component.empty and ctx.component.default is not ctx.component.empty:
                handler_call_arguments.append(ctx.component.default)
            elif ctx.component.kind == ctx.component.POSITIONAL_OR_KEYWORD:
                ctx.argument = next(ctx.arguments, None)

                if ctx.argument is None:
                    if ctx.component.default is not ctx.component.empty:
                        handler_call_arguments.append(ctx.component.default)
                    else:
                        raise StopIteration
                else:
                    converter = get_converter(ctx.component)

                    if converter == str:
                        self._consume_separated_string(ctx)

                    handler_call_arguments.append(await do_conversion(converter, ctx))
            elif ctx.component.kind == ctx.component.VAR_POSITIONAL:
                for argument in ctx.arguments:
                    ctx.argument = argument
                    converter = get_converter(ctx.component)

                    if converter == str:
                        self._consume_separated_string(ctx)

                    handler_call_arguments.append(await do_conversion(converter, ctx))
            elif ctx.component.kind == ctx.component.KEYWORD_ONLY:
                ctx.arguments = keyword_arguments
                ctx.argument = next(keyword_arguments)
                converter = get_converter(ctx.component)

                if converter == str:
                    self._consume_separated_string(ctx)

                handler_call_keywords[ctx.component.name] = await do_conversion(converter, ctx)

        if self.rest_raw:
            handler_call_arguments.append(list(ctx.arguments))

        return handler_call_arguments, handler_call_keywords

    async def __call__(self, p, data):
        try:
            handler_call_arguments, handler_call_keywords = await self._deserialize(p, data)

            return await self.callback(*handler_call_arguments, **handler_call_keywords)
        except Exception as e:
            if self._exception_callback and isinstance(e, self._exception_class):
                if self.instance:
                    await self._exception_callback(self.instance, e)
                else:
                    await self._exception_callback(e)
            else:
                raise e

    def __hash__(self):
        return hash(self.__name__())

    def __name__(self):
        return f'{self.callback.__module__}.{self.callback.__name__}'


def _listener(cls, name, **kwargs):
    def decorator(callback):
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError('All listeners must be a coroutine.')

        try:
            cooldown_object = callback.__cooldown
            del callback.__cooldown
        except AttributeError:
            cooldown_object = None

        try:
            checklist = callback.__checks
            del callback.__checks
        except AttributeError:
            checklist = []

        listener_object = cls(name, callback, cooldown=cooldown_object, checklist=checklist, **kwargs)
        return listener_object
    return decorator


class IConverter(ABC):

    @property
    @abstractmethod
    def description(self):
        """A short description of the purpose of the converter"""

    @abstractmethod
    async def convert(self, ctx):
        """The actual converter implementation"""


Credentials = collections.namedtuple('Credentials', ('username', 'password'))
WorldCredentials = collections.namedtuple('Credentials', [
    'id',
    'username',
    'login_key',
    'language_approved', 'language_rejected',
    'client_key',
    'confirmation_hash'
])


class CredentialsConverter(IConverter):

    description = """Used for obtaining login credentials from XML login data"""

    async def convert(self, ctx):
        username = ctx.argument[0][0].text
        password = ctx.argument[0][1].text
        return Credentials(username.lower(), password)


class WorldCredentialsConverter(IConverter):

    description = """Used for obtaining login credentials on the world server"""

    async def convert(self, ctx):
        raw_login_data = ctx.argument[0][0].text
        password_hashes = ctx.argument[0][1].text
        penguin_id, _, username, login_key, _, language_approved, language_rejected = raw_login_data.split('|')
        client_key, confirmation_hash = password_hashes.split('#')
        return WorldCredentials(int(penguin_id), username.lower(), login_key,
                                int(language_approved),
                                int(language_rejected),
                                client_key,
                                confirmation_hash)


class VersionChkConverter(IConverter):

    description = """Used for checking the verChk version number"""

    async def convert(self, ctx):
        return int(ctx.argument[0].get('v'))


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

    description = """Converts a room ID into a houdini.data.Room instance"""

    async def convert(self, ctx):
        room_id = int(ctx.argument)
        if room_id in ctx.p.server.rooms:
            return ctx.p.server.rooms[room_id]
        return None


class ItemConverter(IConverter):

    description = """Converts an item ID into a houdini.data.Item instance"""

    async def convert(self, ctx):
        item_id = int(ctx.argument)
        if item_id in ctx.p.server.items:
            return ctx.p.server.items[item_id]
        return None


class IglooConverter(IConverter):

    description = """Converts an igloo ID into a houdini.data.Igloo instance"""

    async def convert(self, ctx):
        igloo_id = int(ctx.argument)
        if igloo_id in ctx.p.server.igloos:
            return ctx.p.server.igloos[igloo_id]
        return None


class FurnitureConverter(IConverter):

    description = """Converts a furniture ID into a houdini.data.Furniture instance"""

    async def convert(self, ctx):
        furniture_id = int(ctx.argument)
        if furniture_id in ctx.p.server.furniture:
            return ctx.p.server.furniture[furniture_id]
        return None


class FlooringConverter(IConverter):

    description = """Converts a flooring ID into a houdini.data.Flooring instance"""

    async def convert(self, ctx):
        flooring_id = int(ctx.argument)
        if flooring_id in ctx.p.server.flooring:
            return ctx.p.server.flooring[flooring_id]
        return None


class LocationConverter(IConverter):

    description = """Converts a location ID into a houdini.data.Location instance"""

    async def convert(self, ctx):
        location_id = int(ctx.argument)
        if location_id in ctx.p.server.locations:
            return ctx.p.server.locations[location_id]
        return None


class StampConverter(IConverter):

    description = """Converts a stamp ID into a houdini.data.Stamp instance"""

    async def convert(self, ctx):
        stamp_id = int(ctx.argument)
        if stamp_id in ctx.p.server.stamps:
            return ctx.p.server.stamps[stamp_id]
        return None


class PuffleConverter(IConverter):

    description = """Converts a puffle ID into a houdini.data.Puffle instance"""

    async def convert(self, ctx):
        puffle_id = int(ctx.argument)
        try:
            return ctx.p.server.puffles[puffle_id]
        except KeyError:
            return None


class PenguinPuffleConverter(IConverter):

    description = """Converts a penguin puffle ID into a houdini.data.PenguinPuffle instance"""

    async def convert(self, ctx):
        puffle_id = int(ctx.argument)
        try:
            return ctx.p.puffles[puffle_id]
        except KeyError:
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


ConverterTypes = {
    Credentials: CredentialsConverter,
    WorldCredentials: WorldCredentialsConverter,

    Room: RoomConverter,
    Item: ItemConverter,
    Furniture: FurnitureConverter,
    Igloo: IglooConverter,
    Flooring: FlooringConverter,
    Location: LocationConverter,
    Stamp: StampConverter,
    Puffle: PuffleConverter,

    PenguinPuffle: PenguinPuffleConverter
}


def get_converter(component):
    if component.annotation in ConverterTypes:
        return ConverterTypes[component.annotation]
    if component.annotation is component.empty:
        return str
    return component.annotation


async def do_conversion(converter, ctx):
    if not isinstance(converter, IConverter) and issubclass(converter, IConverter):
        converter = converter()
    if isinstance(converter, IConverter):
        if asyncio.iscoroutinefunction(converter.convert):
            return await converter.convert(ctx)
        return converter.convert(ctx)
    return converter(ctx.argument)
