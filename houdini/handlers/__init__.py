import inspect
import enum
import os
import itertools
from types import FunctionType

from houdini.converters import _listener, _ArgumentDeserializer, get_converter, do_conversion, _ConverterContext

from houdini.cooldown import _Cooldown, _CooldownMapping, BucketType
from houdini import plugins


class AuthorityError(Exception):
    """Raised when a packet is received but user has not yet authenticated"""


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


class _Listener(_ArgumentDeserializer):

    __slots__ = ['priority', 'packet', 'overrides']

    def __init__(self, packet, callback, **kwargs):
        super().__init__(packet.id, callback, **kwargs)
        self.packet = packet

        self.priority = kwargs.get('priority', Priority.Low)
        self.overrides = kwargs.get('overrides', [])

        if type(self.overrides) is not list:
            self.overrides = [self.overrides]


class _XTListener(_Listener):

    __slots__ = ['pre_login']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pre_login = kwargs.get('pre_login')

    async def __call__(self, p, packet_data):
        if not self.pre_login and not p.joined_world:
            await p.close()
            raise AuthorityError('{} tried sending XT packet before authentication!'.format(p))

        await super()._check_cooldown(p)
        super()._check_list(p)

        await super().__call__(p, packet_data)


class _XMLListener(_Listener):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, p, packet_data):
        await super()._check_cooldown(p)
        super()._check_list(p)

        handler_call_arguments = [self.instance, p] if self.instance is not None else [p]

        ctx = _ConverterContext(None, None, packet_data, p)
        for ctx.component in itertools.islice(self._signature, len(handler_call_arguments), len(self._signature)):
            if ctx.component.default is not ctx.component.empty:
                handler_call_arguments.append(ctx.component.default)
            elif ctx.component.kind == ctx.component.POSITIONAL_OR_KEYWORD:
                converter = get_converter(ctx.component)

                handler_call_arguments.append(await do_conversion(converter, ctx))
        return await self.callback(*handler_call_arguments)


def get_relative_function_path(function_obj):
    abs_function_file = inspect.getfile(function_obj)
    rel_function_file = os.path.relpath(abs_function_file)

    return rel_function_file


def handler(packet, **kwargs):
    if not issubclass(type(packet), _Packet):
        raise TypeError('All handlers can only listen for either XMLPacket or XTPacket.')

    listener_class = _XTListener if isinstance(packet, XTPacket) else _XMLListener
    return _listener(listener_class, packet, **kwargs)


def listener_exists(xt_listeners, xml_listeners, packet):
    listener_collection = xt_listeners if isinstance(packet, XTPacket) else xml_listeners
    return packet in listener_collection


def is_listener(listener):
    return issubclass(type(listener), _Listener)


def listeners_from_module(xt_listeners, xml_listeners, module):
    listener_objects = inspect.getmembers(module, is_listener)
    for listener_name, listener_object in listener_objects:
        if isinstance(module, plugins.IPlugin):
            listener_object.instance = module

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
                handler_file = get_relative_function_path(handler_listener.callback)
                if handler_file == handler_module_path:
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
    def check_for_packet(listener, p):
        return listener.packet not in p.received_packets
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
