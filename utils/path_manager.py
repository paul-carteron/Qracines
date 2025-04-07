import os
import yaml

from .variable_utils import get_project_variable
from .plugin_path import get_config_path

def load_sig_structure_yaml():
    path = get_config_path("sig_structure.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_path(logical_key, forest=None, base_dir=None):
    """
    Resolve a full file path from the sig_structure.yaml using a logical key.
    Falls back to QGIS project variables if forest or base_dir are not given.

    Args:
        logical_key (str): key from the YAML structure
        forest (str, optional): forest prefix (e.g. 'AMPLEMONT')
        base_dir (str, optional): root folder containing all forests

    Returns:
        str: full path to the file
    """
    sig_structure = load_sig_structure_yaml()

    forest = forest or get_project_variable("forest_prefix")
    base_dir = base_dir or get_project_variable("forest_directory")

    if not forest or not base_dir:
        raise ValueError("Missing forest or base_dir. Either pass them directly or set them as project variables.")

    for folder in sig_structure["structure"].values():
        files = folder.get("files", {})
        if logical_key in files:
            raw_filename = files[logical_key]["filename"]
            filename = f"{forest}_{raw_filename}" if not raw_filename.startswith(forest) else raw_filename
            folder_path = folder["path"]
            full_folder = os.path.join(base_dir, *folder_path)
            os.makedirs(full_folder, exist_ok=True)
            return os.path.join(full_folder, filename)

    raise KeyError(f"File key '{logical_key}' not found in sig_structure.yaml")
