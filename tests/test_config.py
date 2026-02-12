"""Tests for config loading."""

import json
import tempfile
from pathlib import Path

import pytest

from iracing_event_logger.config import (
    load_config,
    get_log_file,
    get_focus_car,
    get_focus_driver,
    get_battle_gap_s,
    get_start_telemetry,
)


def test_load_config_json(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({"focus_car": "5", "log_file": "out.json"}), encoding="utf-8")
    config = load_config(cfg_path)
    assert config.get("focus_car") == "5"
    assert config.get("log_file") == "out.json"


def test_getters_defaults():
    config = {}
    assert get_log_file(config) == "event_log.json"
    assert get_focus_driver(config) is None
    assert get_focus_car(config) is None
    assert get_battle_gap_s(config) == 1.5
    assert get_start_telemetry(config) is False


def test_getters_from_config():
    config = {"log_file": "custom.json", "focus_car": "12", "battle_gap_s": 2.0, "start_telemetry": True}
    assert get_log_file(config) == "custom.json"
    assert get_focus_car(config) == "12"
    assert get_battle_gap_s(config) == 2.0
    assert get_start_telemetry(config) is True
