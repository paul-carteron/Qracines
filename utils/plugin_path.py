from pathlib import Path

def get_plugin_root() -> Path:
    """
    Returns the root directory of the plugin (two levels up from this file).
    """
    return Path(__file__).resolve().parent.parent

def get_config_path(filename: str) -> Path:
    """
    Returns the full path to a file under the plugin's 'config' folder.
    """
    return get_plugin_root() / "config" / filename

