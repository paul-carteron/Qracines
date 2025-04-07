import os

def get_plugin_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path(filename):
    return os.path.join(get_plugin_root(), "config", filename)
