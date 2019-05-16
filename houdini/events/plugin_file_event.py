import sys
import importlib
import os.path
import copy
import asyncio
from watchdog.events import FileSystemEventHandler

from houdini.events import evaluate_handler_file_event


class PluginFileEventHandler(FileSystemEventHandler):

    def __init__(self, server):
        self.logger = server.logger
        self.server = server

    def on_created(self, event):
        plugin_module_details = evaluate_handler_file_event(event)

        if not plugin_module_details:
            return

        plugin_module_path, plugin_module = plugin_module_details

        self.logger.debug('New handler module detected %s', plugin_module)

        try:
            plugin_module_object = importlib.import_module(plugin_module)
            plugin_class = plugin_module_object.__name__.split(".")[2]

            asyncio.run(self.server.load_plugin((plugin_module_object, plugin_class)))

            self.logger.info('New plugin \'%s\' has been loaded.' % plugin_class)
        except Exception as import_error:
            self.logger.error('%s detected in %s, not importing.', import_error.__class__.__name__, plugin_module)

    def on_deleted(self, event):
        plugin_module_path = event.src_path[2:]

        plugin_module = plugin_module_path.replace(os.path.pathsep, ".")

        if plugin_module not in sys.modules:
            return

        self.logger.debug('Deleting listeners registered by %s.', plugin_module)

        plugin_module_object = sys.modules[plugin_module]
        plugin_class = plugin_module_object.__name__.split(".")[2]

        self.server.unload_plugin((plugin_module_object, plugin_class))

    def on_modified(self, event):
        plugin_module_details = evaluate_handler_file_event(event)

        if not plugin_module_details:
            return

        plugin_module_path, plugin_module = plugin_module_details

        if plugin_module not in sys.modules:
            return

        self.logger.info('Reloading %s', plugin_module)

        plugin_module_object = sys.modules[plugin_module]
        plugin_class = plugin_module_object.__name__.split(".")[2]

        xt_listeners, xml_listeners = copy.copy(self.server.xt_listeners), copy.copy(self.server.xml_listeners)

        self.server.unload_plugin((plugin_module_object, plugin_class))

        try:
            new_plugin_module = importlib.reload(plugin_module_object)
            asyncio.run(self.server.load_plugin((new_plugin_module, plugin_class)))

            self.logger.info('Successfully reloaded %s!', plugin_module)
        except LookupError as lookup_error:
            self.logger.warn('Did not reload plugin \'%s\': %s.', plugin_class, lookup_error)
        except Exception as rebuild_error:
            self.logger.error('%s detected in %s, not reloading.', rebuild_error.__class__.__name__, plugin_module)
            self.logger.info('Restoring handler references...')

            self.server.xt_handlers = xt_listeners
            self.server.xml_handlers = xml_listeners

            self.logger.info('Restored handler references. Phew!')
