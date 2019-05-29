from abc import ABC
from abc import abstractmethod

import inspect
import asyncio

from houdini import _AbstractManager


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

    @abstractmethod
    def __init__(self, server):
        self.server = server


class PluginManager(_AbstractManager):
    def setup(self, module):
        for plugin_package in self.server.get_package_modules(module):
            self.load(plugin_package)

    def load(self, module):
        plugin_class, plugin_type = inspect.getmembers(module, is_plugin).pop()

        if self.server.server_config['Plugins'] is not True and \
                plugin_class not in self.server.server_config['Plugins']:
            return

        plugin_object = plugin_type(self.server)
        self[module.__name__] = plugin_object

        self.server.commands.load(plugin_object)
        self.server.xt_listeners.load(plugin_object)
        self.server.xml_listeners.load(plugin_object)

        asyncio.run_coroutine_threadsafe(plugin_object.ready(), self.server.server.get_loop())

    def remove(self, module):
        if module.__name__ in self:
            del self[module.__name__]

            self.server.commands.remove(module)
            self.server.xt_listeners.remove(module)
            self.server.xml_listeners.remove(module)


def is_plugin(plugin_class):
    return inspect.isclass(plugin_class) and issubclass(plugin_class, IPlugin) and plugin_class != IPlugin
