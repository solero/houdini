from abc import ABC
from abc import abstractmethod


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
        """
        Called when the plugin is ready to function.
        """

    @abstractmethod
    def __init__(self, server):
        self.server = server
