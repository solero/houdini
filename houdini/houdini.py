import asyncio
import os
import sys
import pkgutil
import importlib
import copy

from houdini.spheniscidae import Spheniscidae
from houdini.penguin import Penguin
from houdini import PenguinStringCompiler
import config

import logging
from logging.handlers import RotatingFileHandler

import aioredis
from aiocache import SimpleMemoryCache
from watchdog.observers import Observer

from houdini.data import db
from houdini.data.item import ItemCrumbsCollection
from houdini.data.igloo import IglooCrumbsCollection, FurnitureCrumbsCollection, \
    LocationCrumbsCollection, FlooringCrumbsCollection
from houdini.data.room import RoomCrumbsCollection
from houdini.data.stamp import StampCrumbsCollection
from houdini.data.ninja import CardCrumbsCollection
from houdini.data.mail import PostcardCrumbsCollection
from houdini.data.pet import PuffleCrumbsCollection, PuffleItemCrumbsCollection
from houdini.data.permission import PermissionCrumbsCollection

try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None

import houdini.handlers
import houdini.plugins
from houdini.events.listener_file_event import ListenerFileEventHandler
from houdini.events.plugin_file_event import PluginFileEventHandler

from houdini.handlers import XTListenerManager, XMLListenerManager
from houdini.plugins import PluginManager
from houdini.commands import CommandManager


class Houdini:

    def __init__(self, server_name,  **kwargs):
        self.server = None
        self.redis = None
        self.config = None
        self.cache = None
        self.db = db
        self.peers_by_ip = {}

        self.server_name = server_name
        self.database_config_override = kwargs.get('database')
        self.redis_config_override = kwargs.get('redis')
        self.commands_config_override = kwargs.get('commands')
        self.server_config_override = kwargs.get('server')
        self.server_config = None

        self.logger = None

        self.client_class = Spheniscidae
        self.penguin_string_compiler = None
        self.anonymous_penguin_string_compiler = None

        self.penguins_by_id = {}
        self.penguins_by_username = {}

        self.login_attempts = {}

        self.xt_listeners = XTListenerManager(self)
        self.xml_listeners = XMLListenerManager(self)
        self.commands = CommandManager(self)
        self.plugins = PluginManager(self)

        self.permissions = None

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

        self.server_config = copy.deepcopy(self.config.servers[self.server_name])
        self.server_config.update(self.server_config_override)

        self.config.database.update(self.database_config_override)
        self.config.redis.update(self.redis_config_override)
        self.config.commands.update(self.commands_config_override)

        general_log_directory = os.path.dirname(self.server_config["Logging"]["General"])
        errors_log_directory = os.path.dirname(self.server_config["Logging"]["Errors"])

        if not os.path.exists(general_log_directory):
            os.mkdir(general_log_directory)

        if not os.path.exists(errors_log_directory):
            os.mkdir(errors_log_directory)

        self.logger = logging.getLogger('houdini')
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

        self.logger.info('Booting Houdini')

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

            self.xml_listeners.setup(houdini.handlers, exclude_load='houdini.handlers.login.login')
            self.xt_listeners.setup(houdini.handlers)
            self.logger.info('World server started')
        else:
            self.xml_listeners.setup(houdini.handlers, 'houdini.handlers.login.login')
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

        self.permissions = await PermissionCrumbsCollection.get_collection()

        handlers_path = './houdini{}handlers'.format(os.path.sep)
        plugins_path = './houdini{}plugins'.format(os.path.sep)
        self.configure_observers([handlers_path, ListenerFileEventHandler],
                                 [plugins_path, PluginFileEventHandler])

        self.logger.info('Listening on {}:{}'.format(self.server_config['Address'], self.server_config['Port']))

        self.plugins.setup(houdini.plugins)

        async with self.server:
            await self.server.serve_forever()

    async def client_connected(self, reader, writer):
        client_object = self.client_class(self, reader, writer)
        await client_object.run()

    def get_package_modules(self, package):
        package_modules = []

        for importer, module_name, is_package in pkgutil.iter_modules(package.__path__):
            full_module_name = '{0}.{1}'.format(package.__name__, module_name)

            if is_package:
                subpackage_object = importlib.import_module(full_module_name, package=package.__path__)
                subpackage_object_directory = dir(subpackage_object)

                if houdini.plugins.IPlugin.__name__ in subpackage_object_directory:
                    package_modules.append(subpackage_object)
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
