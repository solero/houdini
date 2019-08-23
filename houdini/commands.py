import inspect
import config

from houdini import handlers
from houdini import plugins
from houdini import _AbstractManager
from houdini.constants import ConflictResolution

from houdini.converters import _ArgumentDeserializer, _listener


class UnknownCommandException(Exception):
    """Raised when a command is executed that doesn't exist"""


class _Command(_ArgumentDeserializer):

    def __init__(self, name, callback, **kwargs):
        super().__init__(name, callback, **kwargs)

        self.alias = kwargs.get('alias', [])
        self.parent = kwargs.get('parent', None)


class _CommandGroup(_Command):
    __slots__ = ['commands']

    def __init__(self, name, callback, **kwargs):
        super().__init__(name, callback, **kwargs)

        self.commands = {}

    async def __call__(self, p, data):
        if not data:
            if self.instance:
                return await self.callback(self.instance, p)
            return await self.callback(p)

        await invoke_command_objects(self.commands, p, data)

    def command(self, name=None, **kwargs):
        return command(name, parent=self, **kwargs)

    def group(self, name=None, **kwargs):
        return group(name, parent=self, **kwargs)


def command(name=None, **kwargs):
    return _listener(_Command, name, string_delimiter=config.commands['StringDelimiters'],
                     string_separator=' ', **kwargs)


def group(name=None, **kwargs):
    return _listener(_CommandGroup, name, string_delimiter=config.commands['StringDelimiters'],
                     string_separator=' ', **kwargs)


cooldown = handlers.cooldown
check = handlers.check

player_attribute = handlers.player_attribute
player_data_attribute = handlers.player_data_attribute
player_in_room = handlers.player_in_room


class CommandManager(_AbstractManager):
    def load(self, module):
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
                    if config.commands['ConflictMode'] == ConflictResolution.Exception:
                        raise NameError('Command name conflict: \'{}\' from plugin \'{}\' '
                                        'conflicts with \'{}\' from module \'{}\''
                                        .format(name, module.__class__.__name__, conflict_command.name,
                                                conflict_command.instance.__class__.__name__))
                    elif config.commands['ConflictMode'] == ConflictResolution.Append:
                        parent_commands[name].append(command_object)
                    elif config.commands['ConflictMode'] == ConflictResolution.Silent:
                        module.server.logger.warning(
                            'Command \'{}\' from module \'{}\' disabled due to conflict with \'{}\''.format(
                                name, module.__class__.__name__, conflict_command.instance.__class__.__name__))
                else:
                    parent_commands[name] = [command_object]


def is_command(command_object):
    return issubclass(type(command_object), _Command)


if type(config.commands['Prefix']) == str:
    config.commands['Prefix'] = [config.commands['Prefix']]


def has_command_prefix(command_string):
    for prefix in config.commands['Prefix']:
        if command_string.startswith(prefix):
            return True
    return False


def get_command_prefix(command_string):
    for prefix in config.commands['Prefix']:
        if command_string.startswith(prefix):
            return prefix


async def invoke_command_string(commands, p, command_string):
    prefix = get_command_prefix(command_string)
    no_prefix = command_string[len(prefix):]
    data = no_prefix.split(' ')

    await invoke_command_objects(commands, p, data)


async def invoke_command_objects(commands, p, data):
    command_identifier = data.pop(0)
    if command_identifier not in commands:
        raise UnknownCommandException('Command \'{}\' does not exist'.format(command_identifier))

    command_objects = commands[command_identifier]
    for command_object in command_objects:
        await command_object(p, data)

