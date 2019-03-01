import inspect
import time
import enum
import os
import asyncio
from types import FunctionType

from Houdini.Converters import IConverter


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


class BucketType(enum.Enum):
    Default = 1
    Penguin = 1
    Server = 2


class _Cooldown:

    __slots__ = ['rate', 'per', 'bucket_type', 'last',
                 '_window', '_tokens']

    def __init__(self, per, rate, bucket_type):
        self.per = float(per)
        self.rate = int(rate)
        self.bucket_type = bucket_type
        self.last = 0.0

        self._window = 0.0
        self._tokens = self.rate

    @property
    def is_cooling(self):
        current = time.time()
        self.last = current

        if self._tokens == self.rate:
            self._window = current

        if current > self._window + self.per:
            self._tokens = self.rate
            self._window = current

        if self._tokens == 0:
            return self.per - (current - self._window)

        self._tokens -= 1
        if self._tokens == 0:
            self._window = current

    def reset(self):
        self._tokens = self.rate
        self.last = 0.0

    def copy(self):
        return _Cooldown(self.per, self.rate, self.bucket_type)


class _CooldownMapping:

    __slots__ = ['_cooldown', '_cache']

    def __init__(self, cooldown_object):
        self._cooldown = cooldown_object

        self._cache = {}

    def _get_bucket_key(self, p):
        if self._cooldown.bucket_type == BucketType.Default:
            return p
        return p.server

    def _verify_cache_integrity(self):
        current = time.time()
        self._cache = {cache_key: bucket for cache_key, bucket in
                       self._cache.items() if current < bucket.last + bucket.per}

    def get_bucket(self, p):
        self._verify_cache_integrity()
        cache_key = self._get_bucket_key(p)
        if cache_key not in self._cache:
            bucket = self._cooldown.copy()
            self._cache[cache_key] = bucket
        else:
            bucket = self._cache[cache_key]
        return bucket


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

    __slots__ = ['pre_login']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pre_login = kwargs.get('pre_login')

    async def __call__(self, p, packet_data):
        if not self.pre_login and not p.joined_world:
            p.logger.warn('{} tried sending XT packet before authentication!'.format(p.peer_name))
            await p.close()
            return

        super().__call__(p, packet_data)

        handler_call_arguments = [self.instance] if self.instance is not None else []
        handler_call_arguments += [self.packet, p] if self.pass_packet else [p]

        arguments = iter(packet_data)
        for index, component in enumerate(self.components):
            if component.default is not component.empty:
                handler_call_arguments.append(component.default)
                next(arguments)
            elif component.kind == component.POSITIONAL_OR_KEYWORD:
                component_data = next(arguments)
                converter = get_converter(component)
                handler_call_arguments.append(await do_conversion(converter, p, component_data))
            elif component.kind == component.VAR_POSITIONAL:
                for component_data in arguments:
                    converter = get_converter(component)
                    handler_call_arguments.append(await do_conversion(converter, p, component_data))
                break
        return await self.handler(*handler_call_arguments)


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
            cooldown_object = handler_function.cooldown
            del handler_function.cooldown
        except AttributeError:
            cooldown_object = None

        try:
            checklist = handler_function.checks
            del handler_function.checks
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


def cooldown(per=1.0, rate=1, bucket_type=BucketType.Default):
    def decorator(handler_function):
        handler_function.cooldown = _CooldownMapping(_Cooldown(per, rate, bucket_type))
        return handler_function
    return decorator


def check(predicate):
    def decorator(handler_function):
        if not hasattr(handler_function, 'checks'):
            handler_function.checks = []

        if not type(predicate) == FunctionType:
            raise TypeError('All handler checks must be a function')

        handler_function.checks.append(predicate)
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
