import inspect
import time
import enum
import os
import asyncio
from types import FunctionType

from Houdini.Converters import IConverter

from Houdini.Cooldown import _Cooldown, _CooldownMapping, BucketType, CooldownError

def get_relative_function_path(function_obj):
    abs_function_file = inspect.getfile(function_obj)
    rel_function_file = os.path.relpath(abs_function_file)

    return rel_function_file


def get_converter(component):
    if component.annotation is component.empty:
        return str
    return component.annotation


async def do_conversion(converter, p, component_data):
    if IConverter.implementedBy(converter):
        converter_instance = converter(p, component_data)
        if asyncio.iscoroutinefunction(converter_instance.convert):
            return await converter_instance.convert()
        return converter_instance.convert()
    return converter(component_data)


class _Packet:
    __slots__ = ['id']

    def __init__(self):
        self.id = None

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class XTPacket(_Packet):
    def __init__(self, *packet_id):
        super().__init__()
        self.id = '#'.join(packet_id)

    def __hash__(self):
        return hash(self.id)


class XMLPacket(_Packet):
    def __init__(self, packet_id):
        super().__init__()
        self.id = packet_id


class Priority(enum.Enum):
    Override = 3
    High = 2
    Low = 1


class _Listener:

    __slots__ = ['packet', 'components', 'handler', 'priority',
                 'cooldown', 'pass_packet', 'handler_file',
                 'overrides', 'pre_login', 'checklist', 'instance']

    def __init__(self, packet, components, handler_function, **kwargs):
        self.packet = packet
        self.components = components
        self.handler = handler_function

        self.priority = kwargs.get('priority', Priority.Low)
        self.overrides = kwargs.get('overrides', [])
        self.cooldown = kwargs.get('cooldown')
        self.pass_packet = kwargs.get('pass_packet', False)
        self.checklist = kwargs.get('checklist', [])

        self.instance = None

        if type(self.overrides) is not list:
            self.overrides = [self.overrides]

        self.handler_file = get_relative_function_path(handler_function)

    def _can_run(self, p):
        return True if not self.checklist else all(predicate(self.packet, p) for predicate in self.checklist)

    def __hash__(self):
        return hash(self.__name__())

    def __name__(self):
        return "{}.{}".format(self.handler.__module__, self.handler.__name__)

    def __call__(self, p, packet_data):
        if self.cooldown is not None:
            bucket = self.cooldown.get_bucket(p)
            if bucket.is_cooling:
                raise RuntimeError('{} sent packet during cooldown'.format(p.peer_name))

        if not self._can_run(p):
            raise RuntimeError('Could not handle packet due to checklist failure')


class _XTListener(_Listener):

    __slots__ = ['pre_login', 'rest_raw', 'keywords']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pre_login = kwargs.get('pre_login')
        self.rest_raw = kwargs.get('rest_raw', False)

        self.keywords = len(inspect.getfullargspec(self.handler).kwonlyargs)

        if self.rest_raw:
            self.components = self.components[:-1]

    async def __call__(self, p, packet_data):
        await super().__call__(p, packet_data)

        handler_call_arguments = [self.plugin] if self.plugin is not None else []
        handler_call_arguments += [self.packet, p] if self.pass_packet else [p]
        handler_call_keywords = {}

        arguments = iter(packet_data[:-self.keywords])
        ctx = _ConverterContext(None, arguments, None, p)
        for ctx.component in self.components:
            if ctx.component.annotation is ctx.component.empty and ctx.component.default is not ctx.component.empty:
                handler_call_arguments.append(ctx.component.default)
                next(ctx.arguments)
            elif ctx.component.kind == ctx.component.POSITIONAL_OR_KEYWORD:
                ctx.argument = next(ctx.arguments)
                converter = get_converter(ctx.component)

                handler_call_arguments.append(await do_conversion(converter, ctx))
            elif ctx.component.kind == ctx.component.VAR_POSITIONAL:
                for argument in ctx.arguments:
                    ctx.argument = argument
                    converter = get_converter(ctx.component)

                    handler_call_arguments.append(await do_conversion(converter, ctx))
            elif ctx.component.kind == ctx.component.KEYWORD_ONLY:
                ctx.argument = packet_data[-self.keywords:][len(handler_call_keywords)]
                converter = get_converter(ctx.component)
                handler_call_keywords[ctx.component.name] = await do_conversion(converter, ctx)

        if self.rest_raw:
            handler_call_arguments.append(list(ctx.arguments))
            return await self.handler(*handler_call_arguments, **handler_call_keywords)
        elif not len(list(ctx.arguments)):
            return await self.handler(*handler_call_arguments, **handler_call_keywords)


class _XMLListener(_Listener):
    __slots__ = ['pre_login']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, p, packet_data):
        super().__call__(p, packet_data)

        handler_call_arguments = [self.instance] if self.instance is not None else []
        handler_call_arguments += [self.packet, p] if self.pass_packet else [p]

        for index, component in enumerate(self.components):
            if component.default is not component.empty:
                handler_call_arguments.append(component.default)
            elif component.kind == component.POSITIONAL_OR_KEYWORD:
                converter = get_converter(component)
                handler_call_arguments.append(await do_conversion(converter, p, packet_data))
        return await self.handler(*handler_call_arguments)


def handler(packet, **kwargs):
    def decorator(handler_function):
        if not asyncio.iscoroutinefunction(handler_function):
            raise TypeError('All handlers must be a coroutine.')

        components = list(inspect.signature(handler_function).parameters.values())[1:]

        if not issubclass(type(packet), _Packet):
            raise TypeError('All handlers can only listen for either XMLPacket or XTPacket.')

        listener_class = _XTListener if isinstance(packet, XTPacket) else _XMLListener

        try:
            cooldown_object = handler_function.__cooldown
            del handler_function.__cooldown
        except AttributeError:
            cooldown_object = None

        try:
            checklist = handler_function.__checks
            del handler_function.__checks
        except AttributeError:
            checklist = []

        listener_object = listener_class(packet, components, handler_function,
                                         cooldown=cooldown_object, checklist=checklist,
                                         **kwargs)
        return listener_object
    return decorator


def listener_exists(xt_listeners, xml_listeners, packet):
    listener_collection = xt_listeners if isinstance(packet, XTPacket) else xml_listeners
    return packet in listener_collection


def is_listener(listener):
    return issubclass(type(listener), _Listener)


def listeners_from_module(xt_listeners, xml_listeners, module):
    listener_objects = inspect.getmembers(module, is_listener)
    for listener_name, listener_object in listener_objects:
        listener_collection = xt_listeners if type(listener_object) == _XTListener else xml_listeners
        if listener_object.packet not in listener_collection:
            listener_collection[listener_object.packet] = []

        if listener_object not in listener_collection[listener_object.packet]:
            if listener_object.priority == Priority.High:
                listener_collection[listener_object.packet].insert(0, listener_object)
            elif listener_object.priority == Priority.Override:
                listener_collection[listener_object.packet] = [listener_object]
            else:
                listener_collection[listener_object.packet].append(listener_object)

    for listener_name, listener_object in listener_objects:
        listener_collection = xt_listeners if type(listener_object) == _XTListener else xml_listeners
        for override in listener_object.overrides:
            listener_collection[override.packet].remove(override)


def remove_handlers_by_module(xt_listeners, xml_listeners, handler_module_path):
    def remove_handlers(remove_handler_items):
        for handler_id, handler_listeners in remove_handler_items:
            for handler_listener in handler_listeners:
                if handler_listener.handler_file == handler_module_path:
                    handler_listeners.remove(handler_listener)
    remove_handlers(xt_listeners.items())
    remove_handlers(xml_listeners.items())


def cooldown(per=1.0, rate=1, bucket_type=BucketType.Default, callback=None):
    def decorator(handler_function):
        handler_function.__cooldown = _CooldownMapping(callback, _Cooldown(per, rate, bucket_type))
        return handler_function
    return decorator


def check(predicate):
    def decorator(handler_function):
        if not hasattr(handler_function, 'checks'):
            handler_function.__checks = []

        if not type(predicate) == FunctionType:
            raise TypeError('All handler checks must be a function')

        handler_function.__checks.append(predicate)
        return handler_function
    return decorator


def allow_once():
    def check_for_packet(packet, p):
        return packet not in p.received_packets
    return check(check_for_packet)


def player_attribute(**attrs):
    def check_for_attributes(_, p):
        for attr, value in attrs.items():
            if not getattr(p, attr) == value:
                return False
        return True
    return check(check_for_attributes)


def player_data_attribute(**attrs):
    def check_for_attributes(_, p):
        for attr, value in attrs.items():
            if not getattr(p.data, attr) == value:
                return False
        return True
    return check(check_for_attributes)


def player_in_room(*room_ids):
    def check_room_id(_, p):
        return p.room.ID in room_ids
    return check(check_room_id)
