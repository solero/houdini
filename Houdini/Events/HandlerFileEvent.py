import sys
import importlib
import copy
from watchdog.events import FileSystemEventHandler

from Houdini.Handlers import listeners_from_module, remove_handlers_by_module
from Houdini.Events import evaluate_handler_file_event


class HandlerFileEventHandler(FileSystemEventHandler):

    def __init__(self, server):
        self.logger = server.logger
        self.server = server

    def on_created(self, event):
        handler_module_details = evaluate_handler_file_event(event)

        if not handler_module_details:
            return

        handler_module_path, handler_module = handler_module_details

        if '__init__.py' in handler_module_path:
            return

        self.logger.debug('New handler module detected %s', handler_module)

        try:
            module = importlib.import_module(handler_module)
            listeners_from_module(self.server.xt_listeners, self.server.xml_listeners, module)
        except Exception as import_error:
            self.logger.error('%s detected in %s, not importing.', import_error.__class__.__name__, handler_module)

    def on_deleted(self, event):
        handler_module_details = evaluate_handler_file_event(event)

        if not handler_module_details:
            return

        handler_module_path, handler_module = handler_module_details

        if handler_module not in sys.modules:
            return

        self.logger.debug('Deleting listeners registered by %s...', handler_module)

        remove_handlers_by_module(self.server.xt_listeners, self.server.xml_listeners, handler_module_path)

    def on_modified(self, event):
        handler_module_details = evaluate_handler_file_event(event)

        if not handler_module_details:
            return

        handler_module_path, handler_module = handler_module_details

        if handler_module not in sys.modules:
            return False

        self.logger.info('Reloading %s', handler_module)

        xt_listeners, xml_listeners = copy.copy(self.server.xt_listeners), copy.copy(self.server.xml_listeners)

        remove_handlers_by_module(self.server.xt_listeners, self.server.xml_listeners, handler_module_path)

        handler_module_object = sys.modules[handler_module]

        try:
            module = importlib.reload(handler_module_object)
            listeners_from_module(self.server.xt_listeners, self.server.xml_listeners, module)

            self.logger.info('Successfully reloaded %s!', handler_module)
        except Exception as rebuild_error:
            self.logger.error('%s detected in %s, not reloading.', rebuild_error.__class__.__name__, handler_module)
            self.logger.info('Restoring handler references...')

            self.server.xt_listeners = xt_listeners
            self.server.xml_listeners = xml_listeners

            self.logger.info('Handler references restored. Phew!')
