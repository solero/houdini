import asyncio
import os
import sys
import pkgutil
import importlib

from Houdini.Spheniscidae import Spheniscidae
from Houdini.Penguin import Penguin
from Houdini import PenguinStringCompiler
import config

from aiologger import Logger
from aiologger.handlers.files import AsyncTimedRotatingFileHandler, RolloverInterval, AsyncFileHandler
from aiologger.handlers.streams import AsyncStreamHandler

import logging
from logging.handlers import RotatingFileHandler

import aioredis
from aiocache import SimpleMemoryCache
from watchdog.observers import Observer

from Houdini.Data import db
from Houdini.Data.Item import ItemCrumbsCollection
from Houdini.Data.Igloo import IglooCrumbsCollection, FurnitureCrumbsCollection, \
    LocationCrumbsCollection, FlooringCrumbsCollection
from Houdini.Data.Room import RoomCrumbsCollection
from Houdini.Data.Stamp import StampCrumbsCollection
from Houdini.Data.Ninja import CardCrumbsCollection
from Houdini.Data.Mail import PostcardCrumbsCollection
from Houdini.Data.Pet import PuffleCrumbsCollection, PuffleItemCrumbsCollection

try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None

import Houdini.Handlers
from Houdini.Handlers import listeners_from_module, remove_handlers_by_module
from Houdini.Events.HandlerFileEvent import HandlerFileEventHandler
from Houdini.Events.PluginFileEvent import PluginFileEventHandler

from Houdini.Commands import commands_from_plugin

import Houdini.Plugins as Plugins


class HoudiniFactory:

    def __init__(self, **kwargs):
        self.server = None
        self.redis = None
        self.config = None
        self.cache = None
        self.db = db
        self.peers_by_ip = {}

        self.server_name = kwargs['server']
        self.server_config = None

        self.logger = None

        self.client_class = Spheniscidae
        self.penguin_string_compiler = None
        self.anonymous_penguin_string_compiler = None

        self.penguins_by_id = {}
        self.penguins_by_username = {}

        self.xt_listeners, self.xml_listeners = {}, {}
        self.commands = {}
        self.plugins = {}

        self.items = None
        self.igloos = None
        self.furniture = None
        self.locations = None
        self.flooring = None
        self.rooms = None
        self.stamps = None
        self.cards = None
        self.postcards = None
        self.puffles = None
        self.puffle_items = None

        self.spawn_rooms = None

    async def start(self):
        self.config = config

        self.server_config = self.config.servers[self.server_name]

        general_log_directory = os.path.dirname(self.server_config["Logging"]["General"])
        errors_log_directory = os.path.dirname(self.server_config["Logging"]["Errors"])

        if not os.path.exists(general_log_directory):
            os.mkdir(general_log_directory)

        if not os.path.exists(errors_log_directory):
            os.mkdir(errors_log_directory)

        if sys.platform != 'win32':
            self.logger = Logger(name='Houdini')
            universal_handler = AsyncTimedRotatingFileHandler(
                filename=self.server_config['Logging']['General'],
                backup_count=3,
                when=RolloverInterval.HOURS
            )
            error_handler = AsyncFileHandler(filename=self.server_config['Logging']['Errors'])
            console_handler = AsyncStreamHandler(stream=sys.stdout)
        else:
            self.logger = logging.getLogger('Houdini')
            universal_handler = RotatingFileHandler(self.server_config['Logging']['General'],
                                                    maxBytes=2097152, backupCount=3, encoding='utf-8')

            error_handler = logging.FileHandler(self.server_config['Logging']['Errors'])
            console_handler = logging.StreamHandler(stream=sys.stdout)

        log_formatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
        error_handler.setLevel(logging.ERROR)

        universal_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        self.logger.addHandler(universal_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)

        level = logging.getLevelName(self.server_config['Logging']['Level'])
        self.logger.setLevel(level)

        self.server = await asyncio.start_server(
            self.client_connected, self.server_config['Address'],
            self.server_config['Port']
        )

        await self.db.set_bind('postgresql://{}:{}@{}/{}'.format(
            self.config.database['Username'], self.config.database['Password'],
            self.config.database['Address'],
            self.config.database['Name']))

        self.logger.info('Houdini module instantiated')

        self.redis = await aioredis.create_redis_pool('redis://{}:{}'.format(
            self.config.redis['Address'], self.config.redis['Port']),
            minsize=5, maxsize=10)

        if self.server_config['World']:
            await self.redis.delete('{}.players'.format(self.server_name))
            await self.redis.delete('{}.population'.format(self.server_name))

            self.cache = SimpleMemoryCache(namespace='houdini', ttl=self.server_config['CacheExpiry'])

            self.client_class = Penguin
            self.penguin_string_compiler = PenguinStringCompiler()
            self.anonymous_penguin_string_compiler = PenguinStringCompiler()

            PenguinStringCompiler.setup_default_builder(self.penguin_string_compiler)
            PenguinStringCompiler.setup_anonymous_default_builder(self.anonymous_penguin_string_compiler)

            self.load_handler_modules(exclude_load='Houdini.Handlers.Login.Login')
            self.logger.info('World server started')
        else:
            self.load_handler_modules('Houdini.Handlers.Login.Login')
            self.logger.info('Login server started')

        self.items = await ItemCrumbsCollection.get_collection()
        self.logger.info('Loaded {} clothing items'.format(len(self.items)))

        self.igloos = await IglooCrumbsCollection.get_collection()
        self.logger.info('Loaded {} igloos'.format(len(self.igloos)))

        self.furniture = await FurnitureCrumbsCollection.get_collection()
        self.logger.info('Loaded {} furniture items'.format(len(self.furniture)))

        self.locations = await LocationCrumbsCollection.get_collection()
        self.logger.info('Loaded {} igloo locations'.format(len(self.locations)))

        self.flooring = await FlooringCrumbsCollection.get_collection()
        self.logger.info('Loaded {} igloo flooring'.format(len(self.flooring)))

        self.rooms = await RoomCrumbsCollection.get_collection()
        self.spawn_rooms = self.rooms.get_spawn_rooms()
        await self.rooms.setup_tables()
        await self.rooms.setup_waddles()
        self.logger.info('Loaded {} rooms ({} spawn)'.format(len(self.rooms), len(self.spawn_rooms)))

        self.postcards = await PostcardCrumbsCollection.get_collection()
        self.logger.info('Loaded {} postcards'.format(len(self.postcards)))

        self.stamps = await StampCrumbsCollection.get_collection()
        self.logger.info('Loaded {} stamps'.format(len(self.stamps)))

        self.cards = await CardCrumbsCollection.get_collection()
        self.logger.info('Loaded {} ninja cards'.format(len(self.cards)))

        self.puffles = await PuffleCrumbsCollection.get_collection()
        self.logger.info('Loaded {} puffles'.format(len(self.puffles)))

        self.puffle_items = await PuffleItemCrumbsCollection.get_collection()
        self.logger.info('Loaded {} puffle care items'.format(len(self.puffle_items)))

        handlers_path = './Houdini{}Handlers'.format(os.path.sep)
        plugins_path = './Houdini{}Plugins'.format(os.path.sep)
        self.configure_observers([handlers_path, HandlerFileEventHandler],
                                 [plugins_path, PluginFileEventHandler])

        self.logger.info('Listening on {}:{}'.format(self.server_config['Address'], self.server_config['Port']))

        await self.load_plugins()

        async with self.server:
            await self.server.serve_forever()

    async def load_plugins(self):
        for plugin_package in self.get_package_modules(Plugins):
            await self.load_plugin(plugin_package)

    async def load_plugin(self, plugin):
        plugin_module, plugin_class = plugin

        if plugin_class not in self.server_config['Plugins']:
            return

        plugin_object = getattr(plugin_module, plugin_class)(self)

        if isinstance(plugin_object, Plugins.IPlugin):
            self.plugins[plugin_class] = plugin_object

            listeners_from_module(self.xt_listeners, self.xml_listeners, plugin_object)
            commands_from_plugin(self.commands, plugin_object)

            await plugin_object.ready()
        else:
            self.logger.warn('{0} plugin object doesn\'t provide the plugin interface'.format(plugin_class))

    def unload_plugin(self, plugin):
        plugin_module, plugin_class = plugin

        if plugin_class in self.plugins:
            plugin_module_path = plugin_module.__file__
            del self.plugins[plugin_class]

            remove_handlers_by_module(self.xt_listeners, self.xml_listeners, plugin_module_path)

    async def client_connected(self, reader, writer):
        client_object = self.client_class(self, reader, writer)
        await client_object.run()

    def load_handler_modules(self, strict_load=None, exclude_load=None):
        for handler_module in self.get_package_modules(Houdini.Handlers):
            if not (strict_load and handler_module not in strict_load or exclude_load and handler_module in exclude_load):
                if handler_module not in sys.modules.keys():
                    module = importlib.import_module(handler_module)
                    listeners_from_module(self.xt_listeners, self.xml_listeners, module)

        self.logger.info('Handler modules loaded')

    def get_package_modules(self, package):
        package_modules = []

        for importer, module_name, is_package in pkgutil.iter_modules(package.__path__):
            full_module_name = '{0}.{1}'.format(package.__name__, module_name)

            if is_package:
                subpackage_object = importlib.import_module(full_module_name, package=package.__path__)
                subpackage_object_directory = dir(subpackage_object)

                if Plugins.IPlugin.__name__ in subpackage_object_directory:
                    package_modules.append((subpackage_object, module_name))
                    continue

                sub_package_modules = self.get_package_modules(subpackage_object)

                package_modules = package_modules + sub_package_modules
            else:
                package_modules.append(full_module_name)

        return package_modules

    def configure_observers(self, *observer_settings):
        for observer_path, observer_class in observer_settings:
            event_observer = Observer()
            event_observer.schedule(observer_class(self), observer_path, recursive=True)
            event_observer.start()
