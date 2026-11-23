"""Repository-relative settings, sample data and generated output locations."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRECTORY = PROJECT_ROOT / "config"
SAMPLE_DIRECTORY = PROJECT_ROOT / "data" / "samples"
EXPORT_DIRECTORY = PROJECT_ROOT / "data" / "exports"


def settings_path(module_file):
    """Keep settings separate for each application and its measurement units."""
    return CONFIG_DIRECTORY / f"{Path(module_file).stem}.local.json"


def load_settings(module_file):
    """Prefer local settings, falling back to the tracked example configuration."""
    path = settings_path(module_file)
    if not path.exists():
        path = CONFIG_DIRECTORY / f"{Path(module_file).stem}.example.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as stream:
        settings = json.load(stream)
    if not isinstance(settings, dict):
        raise ValueError(f"Settings must be a JSON object: {path}")
    return settings


def save_settings(module_file, settings):
    """Save local overrides without changing the versioned example file."""
    path = settings_path(module_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(settings, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def export_directory():
    """Create the output directory only when it is needed."""
    EXPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIRECTORY
