import os
import yaml

from .variable_utils import get_project_variable, get_global_variable
from .plugin_path import get_config_path

def load_sig_structure_yaml():
    path = get_config_path("sig_structure.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_path(logical_key, forest=None, base_dir=None):
    sig_structure = load_sig_structure_yaml()

    forest = forest or get_project_variable("forest_prefix")
    base_dir = base_dir or get_project_variable("forest_directory")

    if not forest or not base_dir:
        raise ValueError("Missing forest or base_dir. Either pass them directly or set them as project variables.")

    for folder in sig_structure["structure"].values():
        files = folder.get("files", {})
        if logical_key in files:
            file_data = files[logical_key]
            folder_path = folder["path"]

            if "filename" not in file_data:
                raise ValueError(f"Missing 'filename' for key '{logical_key}'")

            filename = file_data["filename"]
            if not filename.startswith(forest):
                filename = f"{forest}_{filename}"

            full_folder = os.path.join(base_dir, *folder_path)
            os.makedirs(full_folder, exist_ok=True)
            return os.path.join(full_folder, filename)

    raise KeyError(f"File key '{logical_key}' not found in sig_structure.yaml")

def get_style(logical_key, styles_dir=None):
    """
    Resolve the path to a .qml style file based on the logical key in sig_structure.yaml.

    Requires the 'style' key to be defined explicitly in the YAML.
    Uses get_global_variable("styles_directory") as the root.

    Args:
        logical_key (str): Key of the style to look up
        styles_dir (str, optional): Override styles directory

    Returns:
        str: Full path to the .qml file

    Raises:
        ValueError: If 'style' or 'filename' is missing
        FileNotFoundError: If the style file does not exist
        KeyError: If logical_key is not in YAML
    """
    sig_structure = load_sig_structure_yaml()
    styles_dir = styles_dir or get_global_variable("styles_directory")

    if not styles_dir:
        raise ValueError("Global variable 'styles_directory' is not set.")

    for folder in sig_structure["structure"].values():
        files = folder.get("files", {})
        if logical_key in files:
            file_data = files[logical_key]

            if "style" not in file_data:
                raise ValueError(f"Missing 'style' for key '{logical_key}' in YAML. You must define it explicitly.")

            style_filename = file_data["style"]
            style_path = os.path.join(styles_dir, style_filename)

            if not os.path.exists(style_path):
                raise FileNotFoundError(f"Style file not found: {style_path}")

            return style_path

    raise KeyError(f"Style key '{logical_key}' not found in sig_structure.yaml")

def find_similar_filenames(expected_path, pattern):
    """
    Cherche dans le dossier du raster attendu les fichiers contenant une partie du nom logique (comme 'irc').
    """
    directory = os.path.dirname(expected_path)
    if not os.path.exists(directory):
        return []

    return [f for f in os.listdir(directory)if pattern.lower() in f.lower()]
