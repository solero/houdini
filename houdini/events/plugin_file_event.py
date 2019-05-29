import sys
import importlib
import os.path
import logging
import asyncio
from watchdog.events import FileSystemEventHandler

from houdini.events import evaluate_plugin_file_event


class PluginFileEventHandler(FileSystemEventHandler):

    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger('houdini')

    def on_created(self, event):
        plugin_module_details = evaluate_plugin_file_event(event)

        if not plugin_module_details:
            return

        plugin_module_path, plugin_module = plugin_module_details

        self.logger.debug('New plugin detected %s', plugin_module)

        try:
            plugin_module_object = importlib.import_module(plugin_module)

            self.server.plugin.load(plugin_module_object)

            self.logger.info('New plugin \'%s\' has been loaded.' % plugin_module)
        except Exception as import_error:
            self.logger.error('%s detected in %s, not importing.', import_error.__class__.__name__, plugin_module)

    def on_deleted(self, event):
        plugin_module_path = event.src_path[2:]

        plugin_module = plugin_module_path.replace(os.path.pathsep, ".")

        if plugin_module not in sys.modules:
            return

        self.logger.debug('Deleting listeners registered by %s.', plugin_module)

        plugin_module_object = sys.modules[plugin_module]

        self.server.plugins.remove(plugin_module_object)

    def on_modified(self, event):
        plugin_module_details = evaluate_plugin_file_event(event)
        if not plugin_module_details:
            return

        plugin_module_path, plugin_module = plugin_module_details

        if plugin_module not in sys.modules:
            return

        self.logger.info('Reloading %s', plugin_module)

        plugin_module_object = sys.modules[plugin_module]

        self.server.xt_listeners.backup()
        self.server.xml_listeners.backup()
        self.server.commands.backup()

        self.server.plugins.remove(plugin_module_object)

        try:
            new_plugin_module = importlib.reload(plugin_module_object)

            self.server.plugins.load(new_plugin_module)

            self.logger.info('Successfully reloaded %s!', plugin_module)
        except LookupError as lookup_error:
            self.logger.warning('Did not reload plugin \'%s\': %s.', plugin_module, lookup_error)
        except Exception as rebuild_error:
            self.logger.error('%s detected in %s, not reloading.', rebuild_error.__class__.__name__, plugin_module)
            self.logger.info('Restoring handler references...')

            self.server.xt_listeners.restore()
            self.server.xml_listeners.restore()
            self.server.commands.restore()

            self.logger.info('Restored handler references. Phew!')
