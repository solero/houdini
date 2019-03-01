import os
import copy


def evaluate_handler_file_event(handler_file_event):
    # Ignore all directory events
    if handler_file_event.is_directory:
        return False

    handler_module_path = handler_file_event.src_path[2:]

    # Ignore non-Python files
    if handler_module_path[-3:] != ".py":
        return False

    handler_module = handler_module_path.replace(os.path.sep, ".")[:-3]

    return handler_module_path, handler_module


def evaluate_plugin_file_event(plugin_file_event):
    # Ignore all directory events
    if plugin_file_event.is_directory:
        return False

    handler_module_path = plugin_file_event.src_path[2:]

    # Ignore non-Python files
    if handler_module_path[-3:] != ".py":
        return False

    # Remove file extension and replace path separator with dots. Then make like a banana.. and split.
    handler_module_tokens = handler_module_path.replace(os.path.sep, ".")[:-3].split(".")

    if handler_module_tokens.pop() == "__init__":
        return handler_module_path, ".".join(handler_module_tokens)

    return False


def remove_handlers_by_module(xt_listeners, xml_listeners, handler_module_path):
    def remove_handlers(remove_handler_items):
        for handler_id, handler_listeners in remove_handler_items:
            for handler_listener in handler_listeners:
                if handler_listener.handler_file == handler_module_path:
                    handler_listeners.remove(handler_listener)

    xt_handler_collection = copy.copy(xt_listeners)
    remove_handlers(xt_listeners.items())

    xml_handler_collection = copy.copy(xml_listeners)
    remove_handlers(xml_listeners.items())

    return xt_handler_collection, xml_handler_collection
