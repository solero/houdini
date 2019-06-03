import sys
import importlib
import logging
from watchdog.events import FileSystemEventHandler

from houdini.events import evaluate_listener_file_event


class ListenerFileEventHandler(FileSystemEventHandler):

    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger('houdini')

    def on_created(self, event):
        listener_module_details = evaluate_listener_file_event(event)

        if not listener_module_details:
            return

        listener_module_path, listener_module = listener_module_details

        self.logger.debug('New listener module detected {}'.format(listener_module))

        try:
            module = importlib.import_module(listener_module)
            self.server.xt_listeners.load(module)
            self.server.xml_listeners.load(module)

            self.logger.info('New listener module loaded {}'.format(listener_module))
        except Exception as import_error:
            self.logger.error('{} detected in {}, not importing'.format(
                import_error.__class__.__name__, listener_module))

    def on_deleted(self, event):
        listener_module_details = evaluate_listener_file_event(event)

        if not listener_module_details:
            return

        listener_module_path, listener_module = listener_module_details

        if listener_module not in sys.modules:
            return

        listener_module_object = sys.modules[listener_module]

        self.logger.debug('Deleting listener module {}'.format(listener_module))

        self.server.xt_listeners.remove(listener_module_object)
        self.server.xml_listeners.remove(listener_module_object)
        del sys.modules[listener_module]

        self.logger.info('Deleted listener module {}'.format(listener_module))

    def on_modified(self, event):
        listener_module_details = evaluate_listener_file_event(event)

        if not listener_module_details:
            return

        listener_module_path, listener_module = listener_module_details

        if listener_module not in sys.modules:
            return False

        self.logger.info('Reloading listener module {}'.format(listener_module))

        self.server.xt_listeners.backup()
        self.server.xml_listeners.backup()

        listener_module_object = sys.modules[listener_module]

        self.server.xt_listeners.remove(listener_module_object)
        self.server.xml_listeners.remove(listener_module_object)

        try:
            module = importlib.reload(listener_module_object)
            self.server.xt_listeners.load(module)
            self.server.xml_listeners.load(module)

            self.logger.info('Successfully reloaded listener module {}!'.format(listener_module))
        except Exception as rebuild_error:
            self.logger.error('{} detected in {}, not reloading.'.format(
                rebuild_error.__class__.__name__, listener_module))

            self.server.xt_listeners.restore()
            self.server.xml_listeners.restore()
