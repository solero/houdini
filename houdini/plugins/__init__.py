import inspect
from abc import ABC, abstractmethod

from houdini import _AbstractManager, get_package_modules
from houdini.data.plugin import PluginAttributeCollection


class IPlugin(ABC):
    """
    Plugin interface which all plugins *must* implement.
    """

    @property
    @abstractmethod
    def author(self):
        """The plugin's author which is usually a nickname and an e-mail address."""

    @property
    @abstractmethod
    def version(self):
        """The version of the plugin."""

    @property
    @abstractmethod
    def description(self):
        """Short summary of the plugin's intended purpose."""

    @abstractmethod
    async def ready(self):
        """Called when the plugin is ready to function."""

    def get_attribute(self, name, default=None):
        plugin_attribute = self.attributes.get(name, default)
        if plugin_attribute == default:
            return default
        return plugin_attribute.value

    async def set_attribute(self, name, value):
        if name not in self.attributes:
            await self.attributes.insert(name=name, value=value)
        else:
            plugin_attribute = self.attributes.get(name)
            await plugin_attribute.update(value=value).apply()

    async def delete_attribute(self, name):
        if name in self.attributes:
            await self.attributes.delete(name)

    @abstractmethod
    def __init__(self, server):
        self.server = server
        self.attributes = None


class PluginManager(_AbstractManager):
    async def setup(self, module):
        for plugin_package in get_package_modules(module):
            await self.load(plugin_package)

    async def load(self, module):
        plugin_class, plugin_type = inspect.getmembers(module, is_plugin).pop()
        plugin_index = plugin_class.lower()

        if self.server.config.plugins != '*' and \
                plugin_index not in self.server.config.plugins:
            return

        plugin_object = plugin_type(self.server)

        if plugin_index in self:
            raise KeyError(f'Duplicate plugin name "{plugin_index}" exists')

        self[plugin_index] = plugin_object

        await self.server.commands.load(plugin_object)
        await self.server.xt_listeners.load(plugin_object)
        await self.server.xml_listeners.load(plugin_object)
        await self.server.dummy_event_listeners.load(plugin_object)

        plugin_object.attributes = await PluginAttributeCollection.get_collection(plugin_index)
        await plugin_object.ready()


def is_plugin(plugin_class):
    return inspect.isclass(plugin_class) and issubclass(plugin_class, IPlugin) and plugin_class != IPlugin
