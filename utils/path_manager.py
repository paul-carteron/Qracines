import os
import yaml

from .variable_utils import get_project_variable, get_global_variable
from .plugin_path import get_config_path

from pathlib import Path

_SIG_STRUCT: dict | None = None

def _load_sig_structure() -> dict:
    global _SIG_STRUCT
    if _SIG_STRUCT is None:
        cfg_path = get_config_path("sig_structure.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            _SIG_STRUCT = yaml.safe_load(f)
    return _SIG_STRUCT

def _find_entry(logical_key):
    """
    Return (entry_dict, folder_path_parts) for this key,
    or KeyError if missing entirely.
    """
    struct = _load_sig_structure()["structure"]
    for folder in struct.values():
        files = folder.get("files", {})
        if logical_key in files:
            return files[logical_key], folder.get("path", [])
    raise KeyError(f"No entry for '{logical_key}' in sig_structure.yaml")

def get_path(logical_key, forest=None, base_dir=None):
    entry, path = _find_entry(logical_key)
    filename = entry.get("filename")
    if not filename:
        raise KeyError(f"Entry for '{logical_key}' missing 'filename'")

    forest = forest or get_project_variable("forest_prefix")
    base_dir = base_dir or get_project_variable("forest_directory")
    if not forest or not base_dir:
        raise ValueError("Must set forest_prefix & forest_directory")

    # ensure dir exists
    folder = Path(base_dir).joinpath(*path)
    folder.mkdir(parents=True, exist_ok=True)

    # prefix if needed
    if not filename.startswith(forest):
        filename = f"{forest}_{filename}"

    return folder / filename

def get_style(logical_key, styles_dir=None):
    entry, _ = _find_entry(logical_key)
    style_name = entry.get("style")
    if not style_name:
        raise KeyError(f"Entry '{logical_key}' missing required 'style'")

    styles_dir = styles_dir or get_global_variable("styles_directory")
    if not styles_dir:
        raise ValueError("Global 'styles_directory' is not set")

    style_path = Path(styles_dir) / style_name
    if not style_path.exists():
        raise FileNotFoundError(f"Style file not found: {style_path}")

    return style_path

def get_display_name(logical_key):
    """
    Return the display_name for this logical_key,
    or the key itself if none defined.
    """
    entry, _ = _find_entry(logical_key)
    return entry.get("display_name")



def get_wms(logical_key):
    wms_config_path = get_config_path("wms.yaml")
    with open(wms_config_path, "r", encoding="utf-8") as f:
        wms_config = yaml.safe_load(f)
    
    entry = wms_config.get("wms", {}).get(logical_key)
    if not entry:
        raise KeyError(f"No WMS config for key {logical_key}")

    # Extract the two fields
    display_name = entry.get("display_name")
    url = entry.get("url")

    return display_name, url

def get_racines_path(site, *subpaths):
    site_map = {
        "cartographie": "Cartographie - Documents",
        "expertise": "Equipe - Expertise",
        "foret": "Equipe - Forêts",
        "racines": "Equipe - Racines",
        "transaction": "Equipe - Transaction",
    }

    folder = site_map.get(site.lower())
    if folder is None:
        raise ValueError(f"Unknown site '{site}'. Must be one of: {', '.join(site_map)}")

    base = Path.home() / "Racines" / folder
    return base.joinpath(*subpaths)


# Not sure it's the right place
def find_similar_filenames(expected_path, pattern, extensions=None):
    directory = os.path.dirname(expected_path)
    if not os.path.exists(directory):
        return []

    matches = []
    for f in os.listdir(directory):
        if pattern.lower() in f.lower():
            if extensions is None or any(f.lower().endswith(ext.lower()) for ext in extensions):
                matches.append(os.path.join(directory, f))

    return matches
