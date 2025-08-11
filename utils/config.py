import yaml
from pathlib import Path
from dataclasses import dataclass

from qgis.PyQt.QtWidgets import QMessageBox

from .variable import get_project_variable, get_global_variable

# region PLUGIN PATH

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

# endregion

# region RACINES

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

# endregion

# region SIG_STRUCTURE

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
        QMessageBox.critical(None, "Configuration Error", "Veuillez sélectionner une forêt dans 'project_settings'.")
        return None

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

def get_project(folder: str = "output_folder"):

    structure = _load_sig_structure()["structure"]

    if folder not in structure:
        raise KeyError(f"Dossier '{folder}' non trouvé dans sig_structure.yaml")

    files = structure[folder]["files"]
    project_names = {key: get_display_name(key) for key in files.keys()}

    return project_names
  
# endregion

# region WMS

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

# endregion

# region PROJECT
_PROJECT: dict | None = None

def _load_project() -> dict:
    global _PROJECT
    if _PROJECT is None:
        cfg_path = get_config_path("project.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            _PROJECT = yaml.safe_load(f)
    return _PROJECT

@dataclass
class ProjectCanvas:
    scale: int
    zoom_on: str
    groups: list
    themes: list

@dataclass
class ProjectLayout:
    theme: str
    legends: list

def _flatten(seq):
    for x in seq:
        if isinstance(x, (list, tuple)):
            yield from _flatten(x)
        else:
            yield x

def get_project_canvas(name: str) -> ProjectCanvas:
    raw = _load_project().get(name, {}).get("canvas", {})
    if "themes" in raw:
        for t in raw["themes"]:
            if isinstance(t, dict) and "show" in t:
                t["show"] = list(_flatten(t["show"]))
    return ProjectCanvas(**raw)

def get_project_layout(name: str) -> ProjectLayout:
    raw = _load_project().get(name, {}).get("layout", {})
    return ProjectLayout(**raw)

# endregion

# region PEDOLOGY
_PEDOLOGY_CONFIG: dict | None = None

def _load_pedology_config() -> dict:
    global _PEDOLOGY_CONFIG
    if _PEDOLOGY_CONFIG is None:
        pedology_config_path = get_config_path("pedology.yaml")
        with open(pedology_config_path, encoding="utf-8") as f:
            _PEDOLOGY_CONFIG = yaml.safe_load(f)
    return _PEDOLOGY_CONFIG

def get_guides():
    """
    Return the list of guide names defined under 'guides' in stations.yaml.
    """
    pedology_config = _load_pedology_config()
    guides = pedology_config.get("guides")
    if not isinstance(guides, dict):
        raise KeyError("Missing or invalid top‐level 'guides' mapping in stations.yaml")
    return list(guides.keys())

def get_stations(guide):
    """
    Given a guide name, return its list of station codes.
    Raises KeyError if the guide is not defined.
    """
    pedology_config = _load_pedology_config()
    guides = pedology_config.get("guides")
    if not isinstance(guides, dict) or guide not in guides:
        raise KeyError(f"guide '{guide}' not found in stations.yaml")
    stations = guides[guide]
    if not isinstance(stations, list):
        raise ValueError(f"Expected a list of stations for '{guide}', got {type(stations).__name__}")
    return stations

# endregion

# region PEUPLEMENT
_PEUPLEMENT_CONFIG: dict | None = None

def _load_peuplement_config() -> dict:
    global _PEUPLEMENT_CONFIG
    if _PEUPLEMENT_CONFIG is None:
        peuplement_config_path = get_config_path("peuplement.yaml")
        with open(peuplement_config_path, encoding="utf-8") as f:
            _PEUPLEMENT_CONFIG = yaml.safe_load(f)
    return _PEUPLEMENT_CONFIG

def get_peuplements():
    """
    Return the list of guide names defined under 'guides' in stations.yaml.
    """
    peuplement_config = _load_peuplement_config()
    peuplements = peuplement_config.get("peuplement")
    if not isinstance(peuplements, dict):
        raise KeyError("Missing or invalid top‐level 'guides' mapping in stations.yaml")
    return peuplements

# endregion

# region LIMITES
_LIMITE_CONFIG: dict | None = None

def _load_LIMITE_CONFIG() -> dict:
    global _LIMITE_CONFIG
    if _LIMITE_CONFIG is None:
        limite_config_path = get_config_path("limites.yaml")
        with open(limite_config_path, encoding="utf-8") as f:
            _LIMITE_CONFIG = yaml.safe_load(f)
    return _LIMITE_CONFIG

def get_limites():
    """
    Return the list of guide names defined under 'guides' in stations.yaml.
    """
    limite_config = _load_LIMITE_CONFIG()
    limites = limite_config.get("limites")
    if not isinstance(limites, dict):
        raise KeyError("Missing or invalid top‐level 'limites' mapping in stations.yaml")
    return limites

# endregion
