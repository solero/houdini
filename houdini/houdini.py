import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from redis import asyncio as aioredis
from cacheout import Cache

from houdini import PenguinStringCompiler
from houdini.data import db
from houdini.data.permission import PermissionCollection
from houdini.penguin import Penguin
from houdini.spheniscidae import Spheniscidae

try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None

import houdini.handlers
import houdini.plugins

from houdini.handlers import XTListenerManager, XMLListenerManager, DummyEventListenerManager
from houdini.plugins import PluginManager
from houdini.commands import CommandManager


class Houdini:

    def __init__(self, config):
        self.server = None
        self.redis = None
        self.cache = None
        self.config = config
        self.db = db
        self.peers_by_ip = {}

        self.logger = None

        self.client_class = Spheniscidae
        self.penguin_string_compiler = None
        self.anonymous_penguin_string_compiler = None

        self.penguins_by_id = {}
        self.penguins_by_username = {}
        self.penguins_by_character_id = {}

        self.igloos_by_penguin_id = {}
        self.open_igloos_by_penguin_id = {}

        self.xt_listeners = XTListenerManager(self)
        self.xml_listeners = XMLListenerManager(self)
        self.dummy_event_listeners = DummyEventListenerManager(self)
        self.commands = CommandManager(self)
        self.plugins = PluginManager(self)

        self.permissions = None
        self.chat_filter_words = None

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
        self.puffle_food_treasure = None
        self.puffle_furniture_treasure = None
        self.puffle_clothing_treasure = None
        self.characters = None
        self.dance_songs = None

        self.heartbeat = None
        self.egg_timer = None
        self.puffle_killer = None

        self.music = None
        self.dance_floor = None
        self.match_making = None
        self.water_match_making = None
        self.fire_match_making = None

        self.puck = (0, 0)

    async def start(self):
        general_log_file = self.config.logging_general_path if self.config.logging_general_path \
            else f'logs/{self.config.name.lower()}.log'
        errors_log_file = self.config.logging_error_path if self.config.logging_error_path \
            else f'logs/{self.config.name.lower()}-errors.log'
        general_log_directory = os.path.dirname(general_log_file)
        errors_log_directory = os.path.dirname(errors_log_file)

        if not os.path.exists(general_log_directory):
            os.mkdir(general_log_directory)

        if not os.path.exists(errors_log_directory):
            os.mkdir(errors_log_directory)

        self.logger = logging.getLogger('houdini')
        universal_handler = RotatingFileHandler(general_log_file,
                                                maxBytes=2097152, backupCount=3, encoding='utf-8')

        error_handler = logging.FileHandler(errors_log_file)
        console_handler = logging.StreamHandler(stream=sys.stdout)

        log_formatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
        error_handler.setLevel(logging.ERROR)

        universal_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        self.logger.addHandler(universal_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)

        level = logging.getLevelName(self.config.logging_level)
        self.logger.setLevel(level)

        self.server = await asyncio.start_server(
            self.client_connected, self.config.address,
            self.config.port
        )

        await self.db.set_bind('postgresql://{}:{}@{}/{}'.format(
            self.config.database_username, self.config.database_password,
            self.config.database_address,
            self.config.database_name))

        self.logger.info('Booting Houdini')
        pool = aioredis.ConnectionPool.from_url(f'redis://{self.config.redis_address}:{self.config.redis_port}')
        self.redis = aioredis.Redis(connection_pool=pool)

        if self.config.type == 'world':
            await self.redis.delete(f'houdini.players.{self.config.id}')
            await self.redis.hset(f'houdini.population', self.config.id, 0)

            self.cache = Cache(maxsize=None, ttl=self.config.cache_expiry)

            self.client_class = Penguin
            self.penguin_string_compiler = PenguinStringCompiler()
            self.anonymous_penguin_string_compiler = PenguinStringCompiler()

            PenguinStringCompiler.setup_default_builder(self.penguin_string_compiler)
            PenguinStringCompiler.setup_anonymous_default_builder(self.anonymous_penguin_string_compiler)

            await self.xml_listeners.setup(houdini.handlers, exclude_load='houdini.handlers.login.login')
            await self.xt_listeners.setup(houdini.handlers)
            self.logger.info('World server started')
        else:
            await self.xml_listeners.setup(houdini.handlers, 'houdini.handlers.login.login')
            self.logger.info('Login server started')

        await self.dummy_event_listeners.setup(houdini.handlers)
        await self.dummy_event_listeners.fire('boot', self)

        self.permissions = await PermissionCollection.get_collection()

        self.logger.info(f'Multi-client support is '
                         f'{"enabled" if not self.config.single_client_mode else "disabled"}')
        self.logger.info(f'Listening on {self.config.address}:{self.config.port}')

        if self.config.auth_key != 'houdini':
            self.logger.warning('The static key has been changed from the default, '
                                'this may cause authentication issues!')

        await self.plugins.setup(houdini.plugins)

        async with self.server:
            await self.server.serve_forever()

    async def client_connected(self, reader, writer):
        client_object = self.client_class(self, reader, writer)
        await client_object.run()
