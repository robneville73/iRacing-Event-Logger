"""Configuration loading from YAML/JSON with env and CLI overrides."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default config file search order
CONFIG_PATHS = [
    Path("config.yaml"),
    Path("config.json"),
    Path(os.path.expanduser("~/.config/iracing-event-logger/config.yaml")),
    Path(os.path.expanduser("~/.config/iracing-event-logger/config.json")),
]


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load config from path or first existing CONFIG_PATHS. Returns a dict.
    Env override: IRACING_LOG_* for top-level keys (e.g. IRACING_LOG_LOG_FILE).
    """
    raw: Dict[str, Any] = {}
    if path and path.exists():
        raw = _read_file(path)
    else:
        for p in CONFIG_PATHS:
            if p.exists():
                raw = _read_file(p)
                break

    # Env overrides (optional)
    for key, val in os.environ.items():
        if key.startswith("IRACING_LOG_"):
            k = key[12:].lower()
            if k == "log_file":
                raw["log_file"] = val
            elif k == "focus_car":
                raw["focus_car"] = val
            elif k == "focus_driver":
                raw["focus_driver"] = val
            elif k == "battle_gap_s":
                try:
                    raw["battle_gap_s"] = float(val)
                except ValueError:
                    pass
            elif k == "start_telemetry":
                raw["start_telemetry"] = val.lower() in ("1", "true", "yes")

    return raw


def _read_file(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        with open(path, "r", encoding="utf-8") as f:
            if suffix == ".json":
                return json.load(f)
            if suffix in (".yaml", ".yml"):
                import yaml
                return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Failed to load config from %s: %s", path, e)
    return {}


def get(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get config key with default."""
    return config.get(key, default)


def get_log_file(config: Dict[str, Any]) -> str:
    return get(config, "log_file", "event_log.json")


def get_focus_driver(config: Dict[str, Any]) -> Optional[str]:
    return get(config, "focus_driver")


def get_focus_car(config: Dict[str, Any]) -> Optional[str]:
    return get(config, "focus_car")


def get_battle_gap_s(config: Dict[str, Any]) -> float:
    return float(get(config, "battle_gap_s", 1.5))


def get_start_telemetry(config: Dict[str, Any]) -> bool:
    return bool(get(config, "start_telemetry", False))


def get_event_types_enabled(config: Dict[str, Any]) -> Optional[List[str]]:
    """If set, only these event types are emitted; otherwise all enabled."""
    return get(config, "event_types")
