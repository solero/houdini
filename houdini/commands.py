import inspect

from houdini import _AbstractManager, handlers, plugins
from houdini.constants import ConflictResolution
from houdini.converters import ChecklistError, _ArgumentDeserializer, _listener
from houdini.cooldown import CooldownError


class UnknownCommandException(Exception):
    """Raised when a command is executed that doesn't exist"""


class _Command(_ArgumentDeserializer):

    def __init__(self, name, callback, **kwargs):
        super().__init__(name, callback, **kwargs)

        self.alias = kwargs.get('alias', [])
        self.parent = kwargs.get('parent', None)

    async def __call__(self, p, data):
        try:
            await super()._check_cooldown(p)
            super()._check_list(p)

            await super().__call__(p, data)
        except CooldownError:
            p.logger.debug(f'{p} tried to send a command during a cooldown')
        except ChecklistError:
            p.logger.debug(f'{p} sent a command without meeting checklist requirements')


class _CommandGroup(_Command):
    __slots__ = ['commands']

    def __init__(self, name, callback, **kwargs):
        super().__init__(name, callback, **kwargs)

        self.commands = {}

    async def __call__(self, p, data):
        if not data:
            try:
                await super()._check_cooldown(p)
                super()._check_list(p)

                if self.instance:
                    return await self.callback(self.instance, p)
                return await self.callback(p)
            except CooldownError:
                p.logger.debug(f'{p} tried to send a command during a cooldown')
            except ChecklistError:
                p.logger.debug(f'{p} sent a command without meeting checklist requirements')

        await invoke_command_objects(self.commands, p, data)

    def command(self, name=None, **kwargs):
        return command(name, parent=self, **kwargs)

    def group(self, name=None, **kwargs):
        return group(name, parent=self, **kwargs)


def command(name=None, **kwargs):
    return _listener(_Command, name, string_delimiter=['"', "'"],
                     string_separator=' ', **kwargs)


def group(name=None, **kwargs):
    return _listener(_CommandGroup, name, string_delimiter=['"', "'"],
                     string_separator=' ', **kwargs)


cooldown = handlers.cooldown
check = handlers.check

player_attribute = handlers.player_attribute
player_in_room = handlers.player_in_room


class CommandManager(_AbstractManager):
    async def setup(self, module):
        raise NotImplementedError('Commands can only be loaded from plugins')

    async def load(self, module):
        command_objects = inspect.getmembers(module, is_command)
        if not isinstance(module, plugins.IPlugin):
            raise TypeError('Commands can only be loaded from plugins')

        for command_name, command_object in command_objects:
            command_object.instance = module

            if type(command_object.alias) == str:
                command_object.alias = [command_object.alias]
            command_object.alias.append(command_object.name)

            parent_commands = self if command_object.parent is None else command_object.parent.commands

            for name in command_object.alias:
                if name in parent_commands and len(parent_commands[name]):
                    conflict_command = parent_commands[name][0]
                    conflict_resolution = self.server.config.command_conflict_mode
                    if conflict_resolution == ConflictResolution.Exception:
                        raise NameError(f'Command name conflict: \'{name}\' from plugin \'{module.__class__.__name__}\' '
                                        f'conflicts with \'{conflict_command.name}\' from '
                                        f'module \'{conflict_command.instance.__class__.__name__}\'')
                    elif conflict_resolution == ConflictResolution.Append:
                        parent_commands[name].append(command_object)
                    elif conflict_resolution == ConflictResolution.Silent:
                        module.server.logger.warning(f'Command \'{name}\' from module \'{module.__class__.__name__}\' '
                                                     f'disabled due to conflict with '
                                                     f'\'{conflict_command.instance.__class__.__name__}\'')
                else:
                    parent_commands[name] = [command_object]


def is_command(command_object):
    return issubclass(type(command_object), _Command)


def has_command_prefix(pre, command_string):
    for prefix in pre:
        if command_string.startswith(prefix):
            return True
    return False


def get_command_prefix(pre, command_string):
    for prefix in pre:
        if command_string.startswith(prefix):
            return prefix


async def invoke_command_string(commands, p, command_string):
    prefix = get_command_prefix(p.server.config.command_prefix, command_string)
    no_prefix = command_string[len(prefix):]
    data = no_prefix.split(' ')

    await invoke_command_objects(commands, p, data)


async def invoke_command_objects(commands, p, data):
    command_identifier = data.pop(0)
    if command_identifier not in commands:
        raise UnknownCommandException(f'Command \'{command_identifier}\' does not exist')

    command_objects = commands[command_identifier]
    for command_object in command_objects:
        await command_object(p, data)

