import enum
import inspect
import itertools
from types import FunctionType

from houdini import _AbstractManager, get_package_modules, plugins
from houdini.converters import ChecklistError, _ArgumentDeserializer, _ConverterContext, _listener, do_conversion, \
    get_converter
from houdini.cooldown import BucketType, CooldownError, _Cooldown, _CooldownMapping


class AuthorityError(Exception):
    """Raised when a packet is received but user has not yet authenticated"""


class AbortHandlerChain(Exception):
    """Exception raised when handler wants to abort the rest of the handler chain"""


class _Packet:
    __slots__ = ['id']

    def __init__(self, packet_id):
        self.id = packet_id

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class XTPacket(_Packet):
    def __init__(self, *packet_id, ext='s'):
        super().__init__(ext + '%' + '#'.join(packet_id))


class XMLPacket(_Packet):
    pass


class DummyEventPacket(_Packet):
    pass


class Priority(enum.Enum):
    Override = 3
    High = 2
    Low = 1


class _Listener(_ArgumentDeserializer):

    __slots__ = ['priority', 'packet', 'overrides', 'before', 'after', 'client_type']

    def __init__(self, packet, callback, **kwargs):
        super().__init__(packet.id, callback, **kwargs)
        self.packet = packet

        self.priority = kwargs.get('priority', Priority.Low)
        self.before = kwargs.get('before')
        self.after = kwargs.get('after')
        self.client_type = kwargs.get('client')

        self.overrides = kwargs.get('overrides', [])

        if type(self.overrides) is not list:
            self.overrides = [self.overrides]


class _XTListener(_Listener):

    __slots__ = ['pre_login', 'match']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pre_login = kwargs.get('pre_login')
        self.match = kwargs.get('match')

    async def __call__(self, p, packet_data):
        try:
            if not self.pre_login and not p.joined_world:
                await p.close()
                raise AuthorityError(f'{p} tried sending XT packet before authentication!')

            if self.match is None or packet_data[:len(self.match)] == self.match:
                await super()._check_cooldown(p)
                super()._check_list(p)

                await super().__call__(p, packet_data)
        except CooldownError:
            p.logger.debug(f'{p} tried to send a packet during a cooldown')
        except ChecklistError:
            p.logger.debug(f'{p} sent a packet without meeting checklist requirements')


class _XMLListener(_Listener):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, p, packet_data):
        try:
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
        except CooldownError:
            p.logger.debug(f'{p} tried to send a packet during a cooldown')
        except ChecklistError:
            p.logger.debug(f'{p} sent a packet without meeting checklist requirements')


class _DummyListener(_Listener):
    async def __call__(self, p, *_):
        try:
            super()._check_list(p)
            handler_call_arguments = [self.instance, p] if self.instance is not None else [p]
            return await self.callback(*handler_call_arguments)
        except ChecklistError:
            p.logger.debug(f'{p} sent a packet without meeting checklist requirements')


class _ListenerManager(_AbstractManager):
    ListenerClass = _Listener

    def __init__(self, server):
        self.strict_load = None
        self.exclude_load = None

        super().__init__(server)

    async def setup(self, module, strict_load=None, exclude_load=None):
        self.strict_load, self.exclude_load = strict_load, exclude_load
        for handler_module in get_package_modules(module):
            await self.load(handler_module)

    async def load(self, module):
        module_name = module.__module__ if isinstance(module, plugins.IPlugin) else module.__name__
        if not (self.strict_load and module_name not in self.strict_load or
                self.exclude_load and module_name in self.exclude_load):
            listener_objects = inspect.getmembers(module, self.is_listener)
            for listener_name, listener_object in listener_objects:
                if isinstance(module, plugins.IPlugin):
                    listener_object.instance = module

                if listener_object.packet not in self:
                    self[listener_object.packet] = []

                if listener_object not in self[listener_object.packet]:
                    if listener_object.priority == Priority.High:
                        self[listener_object.packet].insert(0, listener_object)
                    elif listener_object.priority == Priority.Override:
                        self[listener_object.packet] = [listener_object]
                    else:
                        self[listener_object.packet].append(listener_object)

            for listener_name, listener_object in listener_objects:
                if listener_object.before in self[listener_object.packet]:
                    index_of_before = self[listener_object.packet].index(listener_object.before)
                    old_index = self[listener_object.packet].index(listener_object)
                    self[listener_object.packet].insert(index_of_before, self[listener_object.packet].pop(old_index))
                if listener_object.after in self[listener_object.packet]:
                    index_of_after = self[listener_object.packet].index(listener_object.after)
                    old_index = self[listener_object.packet].index(listener_object)
                    self[listener_object.packet].insert(index_of_after + 1, self[listener_object.packet].pop(old_index))
                for override in listener_object.overrides:
                    if override in self[override.packet]:
                        self[override.packet].remove(override)

    @classmethod
    def is_listener(cls, listener):
        return issubclass(type(listener), cls.ListenerClass)


class XTListenerManager(_ListenerManager):
    ListenerClass = _XTListener


class XMLListenerManager(_ListenerManager):
    ListenerClass = _XMLListener


class DummyEventListenerManager(_ListenerManager):
    ListenerClass = _DummyListener

    async def fire(self, event, *args, **kwargs):
        dummy_event = DummyEventPacket(event)
        if dummy_event in self.server.dummy_event_listeners:
            dummy_event_listeners = self.server.dummy_event_listeners[dummy_event]
            for listener in dummy_event_listeners:
                await listener(*args, **kwargs)


def handler(packet, **kwargs):
    if not issubclass(type(packet), _Packet):
        raise TypeError('All handlers can only listen for either XMLPacket or XTPacket.')

    listener_class = _XTListener if isinstance(packet, XTPacket) else _XMLListener
    return _listener(listener_class, packet, **kwargs)


boot = _listener(_DummyListener, DummyEventPacket('boot'))
connected = _listener(_DummyListener, DummyEventPacket('connected'))
disconnected = _listener(_DummyListener, DummyEventPacket('disconnected'))


def cooldown(per=1.0, rate=1, bucket_type=BucketType.Default, callback=None):
    def decorator(handler_function):
        handler_function.__cooldown = _CooldownMapping(callback, _Cooldown(per, rate, bucket_type))
        return handler_function
    return decorator


def check(predicate):
    def decorator(handler_function):
        if not hasattr(handler_function, '__checks'):
            handler_function.__checks = []

        if not type(predicate) == FunctionType:
            raise TypeError('All handler checks must be a function')

        handler_function.__checks.append(predicate)
        return handler_function
    return decorator


def check_for_packet(listener, p):
    return listener.packet not in p.received_packets


allow_once = check(check_for_packet)


def depends_on_packet(*packets):
    def check_for_packets(_, p):
        for packet in packets:
            if packet not in p.received_packets:
                return False
        return True
    return check(check_for_packets)


def player_attribute(**attrs):
    def check_for_attributes(_, p):
        for attr, value in attrs.items():
            if not getattr(p, attr) == value:
                return False
        return True
    return check(check_for_attributes)


def player_in_room(*room_ids):
    def check_room_id(_, p):
        return p.room is not None and p.room.id in room_ids
    return check(check_room_id)


def table(*logic):
    def check_table_game(_, p):
        if p.table is not None and type(p.table.logic) in logic:
            return True
        return False
    return check(check_table_game)


def waddle(*waddle):
    def check_waddle_game(_, p):
        if p.waddle is not None and type(p.waddle) in waddle:
            return True
        return False
    return check(check_waddle_game)
