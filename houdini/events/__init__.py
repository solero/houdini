import os


def evaluate_listener_file_event(listener_file_event):
    # Ignore all directory events
    if listener_file_event.is_directory:
        return False

    listener_module_path = listener_file_event.src_path[2:]

    # Ignore non-Python files
    if listener_module_path[-3:] != ".py":
        return False

    # Ignore package index files
    if '__init__.py' in listener_module_path:
        return False

    listener_module = listener_module_path.replace(os.path.sep, ".")[:-3]

    return listener_module_path, listener_module


def evaluate_plugin_file_event(plugin_file_event):
    # Ignore all directory events
    if plugin_file_event.is_directory:
        return False

    plugin_module_path = plugin_file_event.src_path[2:]

    # Ignore non-Python files
    if plugin_module_path[-3:] != ".py":
        return False

    # Remove file extension and replace path separator with dots. Then make like a banana.. and split.
    plugin_module_tokens = plugin_module_path.replace(os.path.sep, ".")[:-3].split(".")

    if plugin_module_tokens.pop() == "__init__":
        return plugin_module_path, ".".join(plugin_module_tokens)

    return False
