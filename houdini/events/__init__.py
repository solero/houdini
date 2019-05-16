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
